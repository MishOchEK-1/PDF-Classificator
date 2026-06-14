import io
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import reverse
import fitz


class Command(BaseCommand):
    help = (
        'Run a live end-to-end verification of /api/classify/ against the current '
        'local Ollama-backed runtime when available.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Fail the command when the local Ollama runtime is unavailable.',
        )

    def handle(self, *args, **options):
        client = Client()

        self.stdout.write('Running live verification baseline...')
        self._verify_health(client)
        self._verify_classification(client, strict=options['strict'])

    def _verify_health(self, client: Client) -> None:
        response = client.get(reverse('api:health'))
        if response.status_code != 200:
            raise CommandError(f'Health check failed with status {response.status_code}.')

        payload = response.json()
        self.stdout.write(
            self.style.SUCCESS(
                f"Health check passed: service={payload.get('service')} ollama_url={payload.get('ollama_url')}"
            )
        )

    def _verify_classification(self, client: Client, strict: bool) -> None:
        response = client.post(
            reverse('api:classify'),
            {'file': self._build_sample_pdf()},
        )

        if response.status_code == 200:
            payload = response.json()
            self.stdout.write(self.style.SUCCESS('Live classification passed.'))
            self.stdout.write(json.dumps(payload, indent=2))
            return

        payload = self._safe_json(response)
        detail = payload.get('detail') or payload

        if response.status_code == 503 and not strict:
            self.stdout.write(
                self.style.WARNING(
                    f'Live classification skipped: local Ollama runtime unavailable. Detail: {detail}'
                )
            )
            return

        raise CommandError(
            f'Live classification failed with status {response.status_code}. Detail: {detail}'
        )

    def _build_sample_pdf(self) -> SimpleUploadedFile:
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), 'Technical Documentation')
        page.insert_text((72, 110), 'Python backend API integration guide')

        buffer = io.BytesIO(document.tobytes())
        document.close()

        return SimpleUploadedFile(
            'live-verification.pdf',
            buffer.getvalue(),
            content_type='application/pdf',
        )

    @staticmethod
    def _safe_json(response) -> dict:
        try:
            return response.json()
        except Exception:
            return {'detail': response.content.decode('utf-8', errors='ignore')}
