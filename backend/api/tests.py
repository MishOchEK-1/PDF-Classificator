from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
import fitz

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
