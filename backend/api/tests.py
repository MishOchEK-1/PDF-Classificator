import json
import socket
from unittest import mock
import urllib.error
from pathlib import Path
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
import fitz

from backend.llm.ollama_client import (
    OllamaClient,
    OllamaClientError,
    OllamaResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)
from backend.models.schemas import ClassificationSchema
from backend.prompts.classification import (
    ALLOWED_DOCUMENT_CLASSES,
    CLASSIFICATION_RESPONSE_SCHEMA,
    build_classification_prompt,
)
from backend.prompts.validation import (
    PromptResponseValidationError,
    validate_classification_response,
)
from backend.services.classification_service import (
    ClassificationResponseAPIError,
    ClassificationService,
    ClassificationTimeoutAPIError,
    ClassificationUnavailableAPIError,
)
from backend.pdf.cleaner import clean_extracted_text
from backend.pdf.parser import PDFParser
from backend.pdf.storage import TemporaryPDFStorage
from backend.pdf.text_optimizer import PDFTextOptimizer
from backend.pdf.parser import ExtractedPDFDocument
from backend.services.pdf_processing_service import PDFProcessingService


def build_pdf_bytes(text: str | None = None) -> bytes:
    document = fitz.open()
    page = document.new_page()

    if text:
        page.insert_text((72, 72), text)

    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


class ApiSmokeTests(TestCase):
    def test_health_endpoint_returns_backend_status(self):
        response = self.client.get(reverse('api:health'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'status': 'ok',
                'service': 'pdf-classification-backend',
                'ollama_url': settings.OLLAMA_URL,
            },
        )

    def test_classify_endpoint_accepts_pdf_request_shape(self):
        pdf = SimpleUploadedFile(
            'sample.pdf',
            build_pdf_bytes('Backend architecture and API design'),
            content_type='application/pdf',
        )

        with mock.patch(
            'backend.api.views.ClassifyDocumentView.classification_service.classify',
            return_value=ClassificationSchema(
                document_class='technical_documentation',
                tags=['python', 'backend', 'api'],
                confidence=0.92,
            ),
        ):
            response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'class': 'technical_documentation',
                'tags': ['python', 'backend', 'api'],
                'confidence': 0.92,
            },
        )

    def test_classify_endpoint_requires_file(self):
        response = self.client.post(reverse('api:classify'), {})

        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.json())

    def test_classify_endpoint_rejects_non_pdf_extension(self):
        fake_text = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')

        response = self.client.post(reverse('api:classify'), {'file': fake_text})

        self.assertEqual(response.status_code, 400)
        self.assertIn('Only PDF files are supported.', response.json()['file'][0])

    def test_classify_endpoint_rejects_blank_pdf_without_text(self):
        pdf = SimpleUploadedFile('blank.pdf', build_pdf_bytes(), content_type='application/pdf')

        response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 422)
        self.assertIn('no extractable text', response.json()['detail'].lower())

    def test_classify_endpoint_rejects_corrupted_pdf(self):
        corrupted_pdf = SimpleUploadedFile('broken.pdf', b'not-a-real-pdf', content_type='application/pdf')

        response = self.client.post(reverse('api:classify'), {'file': corrupted_pdf})

        self.assertEqual(response.status_code, 422)
        self.assertIn('corrupted or unreadable', response.json()['detail'].lower())

    def test_classify_endpoint_rejects_oversized_pdf(self):
        with self.settings(MAX_UPLOAD_SIZE=10):
            pdf = SimpleUploadedFile(
                'large.pdf',
                build_pdf_bytes('This content is intentionally larger than ten bytes.'),
                content_type='application/pdf',
            )
            response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 400)
        self.assertIn('maximum allowed size', response.json()['file'][0])

    def test_classify_endpoint_translates_unavailable_model_error(self):
        pdf = SimpleUploadedFile(
            'sample.pdf',
            build_pdf_bytes('Model unavailable scenario'),
            content_type='application/pdf',
        )

        with mock.patch(
            'backend.api.views.ClassifyDocumentView.classification_service.classify',
            side_effect=ClassificationUnavailableAPIError('Ollama is offline'),
        ):
            response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 503)
        self.assertIn('Ollama is offline', response.json()['detail'])

    def test_classify_endpoint_translates_timeout_error(self):
        pdf = SimpleUploadedFile(
            'sample.pdf',
            build_pdf_bytes('Timeout scenario'),
            content_type='application/pdf',
        )

        with mock.patch(
            'backend.api.views.ClassifyDocumentView.classification_service.classify',
            side_effect=ClassificationTimeoutAPIError('Timed out'),
        ):
            response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 504)
        self.assertIn('Timed out', response.json()['detail'])


class PromptEngineeringTests(SimpleTestCase):
    def test_prompt_contains_text_classes_and_json_only_instructions(self):
        prompt = build_classification_prompt('Sample invoice text')

        self.assertIn('Sample invoice text', prompt)
        self.assertIn('Return exactly one JSON object and nothing else.', prompt)
        self.assertIn('Do not include markdown.', prompt)
        self.assertIn('return "unknown" with lower confidence', prompt)
        self.assertIn('<document_text>', prompt)

        for document_class in ALLOWED_DOCUMENT_CLASSES:
            self.assertIn(document_class, prompt)

    def test_response_validation_accepts_valid_payload(self):
        result = validate_classification_response(
            '{"class":"invoice","tags":["billing","accounts_payable"],"confidence":0.88}'
        )

        self.assertEqual(result.document_class, 'invoice')
        self.assertEqual(result.tags, ['billing', 'accounts_payable'])
        self.assertEqual(result.confidence, 0.88)

    def test_response_validation_rejects_markdown_fenced_json(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response(
                '```json\n{"class":"invoice","tags":["billing"],"confidence":0.8}\n```'
            )

    def test_response_validation_rejects_missing_fields(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response('{"class":"invoice","confidence":0.8}')

    def test_response_validation_rejects_invalid_confidence(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response(
                '{"class":"invoice","tags":["billing"],"confidence":1.2}'
            )

    def test_response_validation_rejects_invalid_tag_format(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response(
                '{"class":"invoice","tags":["Billing!"],"confidence":0.7}'
            )

    def test_response_validation_rejects_extra_keys(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response(
                '{"class":"invoice","tags":["billing"],"confidence":0.7,"summary":"extra"}'
            )

    def test_response_validation_rejects_duplicate_tags(self):
        with self.assertRaises(PromptResponseValidationError):
            validate_classification_response(
                '{"class":"invoice","tags":["billing","billing"],"confidence":0.7}'
            )


class OllamaClientTests(SimpleTestCase):
    def test_send_prompt_posts_to_ollama_generate_endpoint(self):
        client = OllamaClient(
            base_url='http://localhost:11434',
            model='gemma3:4b',
            timeout_seconds=5,
            max_retries=0,
        )

        mocked_response = mock.MagicMock()
        mocked_response.read.return_value = json.dumps({'response': '{"class":"report"}'}).encode('utf-8')
        mocked_context = mock.MagicMock()
        mocked_context.__enter__.return_value = mocked_response
        mocked_context.__exit__.return_value = False

        with mock.patch('urllib.request.urlopen', return_value=mocked_context) as urlopen_mock:
            payload = client.send_prompt(
                'Classify this document',
                response_schema=CLASSIFICATION_RESPONSE_SCHEMA,
                options={'temperature': 0},
            )

        request = urlopen_mock.call_args.args[0]
        body = json.loads(request.data.decode('utf-8'))

        self.assertEqual(request.full_url, 'http://localhost:11434/api/generate')
        self.assertEqual(body['model'], 'gemma3:4b')
        self.assertEqual(body['prompt'], 'Classify this document')
        self.assertFalse(body['stream'])
        self.assertEqual(body['format'], CLASSIFICATION_RESPONSE_SCHEMA)
        self.assertEqual(body['options'], {'temperature': 0})
        self.assertEqual(payload['response'], '{"class":"report"}')

    def test_parse_response_accepts_generate_api_shape(self):
        client = OllamaClient()

        response_text = client.parse_response({'response': '{"class":"invoice"}'})

        self.assertEqual(response_text, '{"class":"invoice"}')

    def test_parse_response_accepts_chat_api_shape(self):
        client = OllamaClient()

        response_text = client.parse_response({'message': {'content': '{"class":"resume"}'}})

        self.assertEqual(response_text, '{"class":"resume"}')

    def test_parse_response_rejects_invalid_shape(self):
        client = OllamaClient()

        with self.assertRaises(OllamaResponseError):
            client.parse_response({'done': True})

    def test_send_prompt_retries_timeout_then_succeeds(self):
        client = OllamaClient(
            base_url='http://localhost:11434',
            model='gemma3:4b',
            timeout_seconds=1,
            max_retries=1,
            retry_delay_seconds=0,
        )

        mocked_response = mock.MagicMock()
        mocked_response.read.return_value = json.dumps({'response': '{"class":"report"}'}).encode('utf-8')
        mocked_context = mock.MagicMock()
        mocked_context.__enter__.return_value = mocked_response
        mocked_context.__exit__.return_value = False

        with mock.patch(
            'urllib.request.urlopen',
            side_effect=[socket.timeout(), mocked_context],
        ) as urlopen_mock:
            payload = client.send_prompt('Retry this prompt')

        self.assertEqual(urlopen_mock.call_count, 2)
        self.assertEqual(payload['response'], '{"class":"report"}')

    def test_send_prompt_raises_timeout_after_retries(self):
        client = OllamaClient(
            base_url='http://localhost:11434',
            model='gemma3:4b',
            timeout_seconds=1,
            max_retries=1,
            retry_delay_seconds=0,
        )

        with mock.patch('urllib.request.urlopen', side_effect=socket.timeout()):
            with self.assertRaises(OllamaTimeoutError):
                client.send_prompt('This request will time out')

    def test_send_prompt_raises_unavailable_for_missing_model(self):
        client = OllamaClient(
            base_url='http://localhost:11434',
            model='missing-model',
            timeout_seconds=1,
            max_retries=0,
        )

        http_error = urllib.error.HTTPError(
            url='http://localhost:11434/api/generate',
            code=404,
            msg='Not Found',
            hdrs=None,
            fp=None,
        )
        http_error.read = lambda: b'model not found'

        with mock.patch('urllib.request.urlopen', side_effect=http_error):
            with self.assertRaises(OllamaUnavailableError):
                client.send_prompt('Missing model prompt')

    def test_send_prompt_raises_generic_client_error_for_http_500(self):
        client = OllamaClient(
            base_url='http://localhost:11434',
            model='gemma3:4b',
            timeout_seconds=1,
            max_retries=0,
        )

        http_error = urllib.error.HTTPError(
            url='http://localhost:11434/api/generate',
            code=500,
            msg='Server Error',
            hdrs=None,
            fp=None,
        )
        http_error.read = lambda: b'internal error'

        with mock.patch('urllib.request.urlopen', side_effect=http_error):
            with self.assertRaises(OllamaClientError):
                client.send_prompt('Server error prompt')


class ClassificationServiceTests(SimpleTestCase):
    def test_classification_service_runs_full_pipeline(self):
        pdf_processing_service = mock.Mock()
        pdf_processing_service.process_upload.return_value = mock.Mock(
            cleaned_text='Invoice total due and payment instructions',
        )
        ollama_client = mock.Mock()
        ollama_client.classify.return_value = (
            '{"class":"invoice","tags":["billing","payment"],"confidence":0.91}'
        )

        service = ClassificationService(
            pdf_processing_service=pdf_processing_service,
            ollama_client=ollama_client,
        )

        result = service.classify(mock.sentinel.pdf_file)

        pdf_processing_service.process_upload.assert_called_once_with(mock.sentinel.pdf_file)
        ollama_client.classify.assert_called_once_with(
            mock.ANY,
            response_schema=CLASSIFICATION_RESPONSE_SCHEMA,
        )
        self.assertEqual(result.document_class, 'invoice')
        self.assertEqual(result.tags, ['billing', 'payment'])
        self.assertEqual(result.confidence, 0.91)

    def test_classification_service_translates_timeout_errors(self):
        pdf_processing_service = mock.Mock()
        pdf_processing_service.process_upload.return_value = mock.Mock(cleaned_text='Resume text')
        ollama_client = mock.Mock()
        ollama_client.classify.side_effect = OllamaTimeoutError('timeout')

        service = ClassificationService(
            pdf_processing_service=pdf_processing_service,
            ollama_client=ollama_client,
        )

        with self.assertRaises(ClassificationTimeoutAPIError):
            service.classify(mock.sentinel.pdf_file)

    def test_classification_service_translates_unavailable_errors(self):
        pdf_processing_service = mock.Mock()
        pdf_processing_service.process_upload.return_value = mock.Mock(cleaned_text='Report text')
        ollama_client = mock.Mock()
        ollama_client.classify.side_effect = OllamaUnavailableError('server unavailable')

        service = ClassificationService(
            pdf_processing_service=pdf_processing_service,
            ollama_client=ollama_client,
        )

        with self.assertRaises(ClassificationUnavailableAPIError):
            service.classify(mock.sentinel.pdf_file)

    def test_classification_service_translates_invalid_model_response(self):
        pdf_processing_service = mock.Mock()
        pdf_processing_service.process_upload.return_value = mock.Mock(cleaned_text='Contract text')
        ollama_client = mock.Mock()
        ollama_client.classify.return_value = '{"class":"contract","confidence":0.9}'

        service = ClassificationService(
            pdf_processing_service=pdf_processing_service,
            ollama_client=ollama_client,
        )

        with self.assertRaises(ClassificationResponseAPIError):
            service.classify(mock.sentinel.pdf_file)

    def test_classification_service_supports_all_document_classes(self):
        for document_class in ALLOWED_DOCUMENT_CLASSES:
            with self.subTest(document_class=document_class):
                pdf_processing_service = mock.Mock()
                pdf_processing_service.process_upload.return_value = mock.Mock(
                    cleaned_text=f'{document_class} example text',
                )
                ollama_client = mock.Mock()
                ollama_client.classify.return_value = json.dumps(
                    {
                        'class': document_class,
                        'tags': [document_class],
                        'confidence': 0.9,
                    }
                )

                service = ClassificationService(
                    pdf_processing_service=pdf_processing_service,
                    ollama_client=ollama_client,
                )

                result = service.classify(mock.sentinel.pdf_file)

                self.assertEqual(result.document_class, document_class)
                self.assertEqual(result.tags, [document_class])
                self.assertEqual(result.confidence, 0.9)

    def test_classification_service_sends_structured_output_schema(self):
        pdf_processing_service = mock.Mock()
        pdf_processing_service.process_upload.return_value = mock.Mock(cleaned_text='API design guide')
        ollama_client = mock.Mock()
        ollama_client.classify.return_value = (
            '{"class":"technical_documentation","tags":["api"],"confidence":0.9}'
        )

        service = ClassificationService(
            pdf_processing_service=pdf_processing_service,
            ollama_client=ollama_client,
        )

        service.classify(mock.sentinel.pdf_file)

        _, kwargs = ollama_client.classify.call_args
        self.assertEqual(kwargs['response_schema'], CLASSIFICATION_RESPONSE_SCHEMA)


class PDFProcessingComponentTests(SimpleTestCase):
    def test_pdf_parser_extracts_text_from_multi_page_pdf(self):
        document = fitz.open()
        document.new_page()
        document.new_page()
        document[0].insert_text((72, 72), 'First page heading')
        document[1].insert_text((72, 72), 'Second page body')

        pdf_path = Path(settings.TEMP_UPLOAD_ROOT) / 'parser-multipage-test.pdf'
        document.save(pdf_path)
        document.close()

        try:
            extracted = PDFParser().extract_text(pdf_path)
        finally:
            pdf_path.unlink(missing_ok=True)

        self.assertEqual(extracted.page_count, 2)
        self.assertIn('First page heading', extracted.text)
        self.assertIn('Second page body', extracted.text)

    def test_pdf_processing_service_returns_clean_merged_text_stream(self):
        document = fitz.open()

        first_page = document.new_page()
        first_page.insert_text((72, 72), 'Invoice Summary', fontsize=18)
        first_page.insert_text((72, 110), 'Amount due: 1200 USD', fontsize=11)

        second_page = document.new_page()
        second_page.insert_text((72, 72), 'Payment Terms', fontsize=18)
        second_page.insert_text((72, 110), 'Pay within 15 days', fontsize=11)

        pdf_bytes = document.tobytes()
        document.close()

        uploaded_pdf = SimpleUploadedFile(
            'invoice.pdf',
            pdf_bytes,
            content_type='application/pdf',
        )

        service = PDFProcessingService(storage=TemporaryPDFStorage(settings.TEMP_UPLOAD_ROOT))
        processed = service.process_upload(uploaded_pdf)

        self.assertEqual(processed.page_count, 2)
        self.assertEqual(
            processed.cleaned_text,
            'Invoice Summary\n\nAmount due: 1200 USD\n\nPayment Terms\n\nPay within 15 days',
        )

    def test_text_optimizer_chunks_and_truncates_large_text(self):
        optimizer = PDFTextOptimizer(chunk_size=40, max_chunks=2, max_characters=70)
        raw_text = (
            'Heading One\nLine A\nLine B\n\n'
            'Heading Two\nLine C\nLine D\n\n'
            'Heading Three\nLine E\nLine F'
        )

        optimized = optimizer.optimize(raw_text)

        self.assertLessEqual(len(optimized), 70)
        self.assertIn('Heading One', optimized)
        self.assertIn('Heading Two', optimized)
        self.assertNotIn('Heading Three', optimized)

    def test_text_optimizer_returns_small_text_without_chunking(self):
        optimizer = PDFTextOptimizer(chunk_size=100, max_chunks=3, max_characters=120)

        optimized = optimizer.optimize('Short text block')

        self.assertEqual(optimized, 'Short text block')

    def test_pdf_processing_service_limits_large_text_before_prompting(self):
        stored_path = Path(settings.TEMP_UPLOAD_ROOT) / 'optimizer-test.pdf'
        uploaded_file = mock.Mock()
        storage = mock.Mock()
        storage.save.return_value = mock.Mock(
            original_name='large.pdf',
            stored_path=stored_path,
        )
        parser = mock.Mock()
        parser.extract_text.return_value = ExtractedPDFDocument(
            text='Section 1\nDetail A\n\nSection 2\nDetail B\n\nSection 3\nDetail C',
            page_count=3,
        )
        optimizer = PDFTextOptimizer(chunk_size=24, max_chunks=2, max_characters=40)

        processed = PDFProcessingService(
            storage=storage,
            parser=parser,
            text_optimizer=optimizer,
        ).process_upload(uploaded_file)

        self.assertEqual(processed.page_count, 3)
        self.assertLessEqual(len(processed.cleaned_text), 40)
        self.assertIn('Section 1', processed.cleaned_text)
        self.assertIn('Section 2', processed.cleaned_text)
        self.assertNotIn('Section 3', processed.cleaned_text)
        storage.cleanup_old_files.assert_called_once_with(exclude=stored_path)

    def test_text_cleaner_normalizes_spacing_and_blank_lines(self):
        raw_text = 'Header   line\r\n\r\n\r\nBody\t\tline\x00\n\nFooter'

        cleaned = clean_extracted_text(raw_text)

        self.assertEqual(cleaned, 'Header line\n\nBody line\n\nFooter')


class FrontendSmokeTests(SimpleTestCase):
    def test_homepage_contains_upload_flow_and_result_sections(self):
        response = self.client.get(reverse('home'))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="classify-form"', html)
        self.assertIn('id="drop-zone"', html)
        self.assertIn('id="pipeline-status"', html)
        self.assertIn('id="result-class"', html)
        self.assertIn('id="result-tags"', html)
        self.assertIn('id="result-error"', html)

    def test_frontend_script_contains_loading_and_error_states(self):
        script = Path(settings.BASE_DIR / 'static/js/app.js').read_text(encoding='utf-8')

        self.assertIn('Uploading PDF...', script)
        self.assertIn('Processing PDF...', script)
        self.assertIn('Running model inference...', script)
        self.assertIn('Invalid PDF', script)
        self.assertIn('Parsing Error', script)
        self.assertIn('Ollama Error', script)
        self.assertIn('Timeout Error', script)

    def test_homepage_includes_progress_and_stage_indicators(self):
        response = self.client.get(reverse('home'))
        html = response.content.decode()

        self.assertIn('id="progress-fill"', html)
        self.assertIn('id="progress-value"', html)
        self.assertIn('id="stage-upload"', html)
        self.assertIn('id="stage-processing"', html)
        self.assertIn('id="stage-inference"', html)


class LiveVerificationCommandTests(TestCase):
    def test_live_verification_command_reports_successful_end_to_end_run(self):
        stdout = StringIO()

        with mock.patch(
            'backend.api.views.ClassifyDocumentView.classification_service.classify',
            return_value=ClassificationSchema(
                document_class='technical_documentation',
                tags=['python', 'backend', 'api'],
                confidence=0.92,
            ),
        ):
            call_command('verify_live_classification', stdout=stdout)

        output = stdout.getvalue()

        self.assertIn('Health check passed', output)
        self.assertIn('Live classification passed.', output)
        self.assertIn('"class": "technical_documentation"', output)

    def test_live_verification_command_skips_when_ollama_is_unavailable(self):
        stdout = StringIO()

        with mock.patch(
            'backend.api.views.ClassifyDocumentView.classification_service.classify',
            side_effect=ClassificationUnavailableAPIError('Ollama is offline'),
        ):
            call_command('verify_live_classification', stdout=stdout)

        output = stdout.getvalue()

        self.assertIn('Health check passed', output)
        self.assertIn('Live classification skipped', output)
        self.assertIn('Ollama is offline', output)
