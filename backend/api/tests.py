import json
import socket
from unittest import mock
import urllib.error

from django.conf import settings
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
from backend.prompts.classification import ALLOWED_DOCUMENT_CLASSES, build_classification_prompt
from backend.prompts.validation import (
    PromptResponseValidationError,
    validate_classification_response,
)


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

        response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['detail'], 'Classification pipeline is not implemented yet.')

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


class PromptEngineeringTests(SimpleTestCase):
    def test_prompt_contains_text_classes_and_json_only_instructions(self):
        prompt = build_classification_prompt('Sample invoice text')

        self.assertIn('Sample invoice text', prompt)
        self.assertIn('Return JSON only.', prompt)
        self.assertIn('Do not include markdown.', prompt)

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
            payload = client.send_prompt('Classify this document')

        request = urlopen_mock.call_args.args[0]
        body = json.loads(request.data.decode('utf-8'))

        self.assertEqual(request.full_url, 'http://localhost:11434/api/generate')
        self.assertEqual(body['model'], 'gemma3:4b')
        self.assertEqual(body['prompt'], 'Classify this document')
        self.assertFalse(body['stream'])
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
