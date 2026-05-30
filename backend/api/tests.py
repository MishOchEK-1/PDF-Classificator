from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


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
        pdf = SimpleUploadedFile('sample.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf')

        response = self.client.post(reverse('api:classify'), {'file': pdf})

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()['detail'], 'Classification pipeline is not implemented yet.')

    def test_classify_endpoint_requires_file(self):
        response = self.client.post(reverse('api:classify'), {})

        self.assertEqual(response.status_code, 400)
        self.assertIn('file', response.json())
