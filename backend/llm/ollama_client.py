import json
import socket
import time
import urllib.error
import urllib.request

from django.conf import settings


class OllamaClientError(RuntimeError):
    """Base exception for Ollama client failures."""


class OllamaTimeoutError(OllamaClientError):
    """Raised when the Ollama request times out after retries."""


class OllamaUnavailableError(OllamaClientError):
    """Raised when Ollama or the configured model is unavailable."""


class OllamaResponseError(OllamaClientError):
    """Raised when Ollama returns an invalid or unexpected response."""


class OllamaClient:
    """Thin client wrapper for the local Ollama runtime."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        retry_delay_seconds: float | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_URL).rstrip('/')
        self.model = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or getattr(settings, 'OLLAMA_TIMEOUT_SECONDS', 30)
        self.max_retries = max_retries if max_retries is not None else getattr(settings, 'OLLAMA_MAX_RETRIES', 2)
        self.retry_delay_seconds = (
            retry_delay_seconds
            if retry_delay_seconds is not None
            else getattr(settings, 'OLLAMA_RETRY_DELAY_SECONDS', 1.0)
        )

    def send_prompt(self, prompt: str) -> dict:
        payload = json.dumps(
            {
                'model': self.model,
                'prompt': prompt,
                'stream': False,
            }
        ).encode('utf-8')

        request = urllib.request.Request(
            f'{self.base_url}/api/generate',
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        attempts = self.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode('utf-8')
                return json.loads(body)
            except (socket.timeout, TimeoutError) as exc:
                last_error = exc
                if attempt == attempts:
                    raise OllamaTimeoutError('Ollama request timed out.') from exc
                time.sleep(self.retry_delay_seconds)
            except urllib.error.HTTPError as exc:
                error_body = exc.read().decode('utf-8', errors='ignore')

                if exc.code in {404, 503}:
                    raise OllamaUnavailableError(
                        self._build_http_error_message(exc.code, error_body)
                    ) from exc

                raise OllamaClientError(self._build_http_error_message(exc.code, error_body)) from exc
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == attempts:
                    raise OllamaUnavailableError('Unable to reach the Ollama server.') from exc
                time.sleep(self.retry_delay_seconds)
            except json.JSONDecodeError as exc:
                raise OllamaResponseError('Ollama returned invalid JSON.') from exc

        if last_error is not None:
            raise OllamaClientError('Unexpected Ollama client failure.') from last_error

        raise OllamaClientError('Unexpected Ollama client failure.')

    def parse_response(self, response_payload: str | dict) -> str:
        if isinstance(response_payload, str):
            try:
                response_payload = json.loads(response_payload)
            except json.JSONDecodeError as exc:
                raise OllamaResponseError('Ollama returned invalid JSON.') from exc

        if not isinstance(response_payload, dict):
            raise OllamaResponseError('Ollama response must be a JSON object.')

        if isinstance(response_payload.get('response'), str):
            content = response_payload['response'].strip()
            if not content:
                raise OllamaResponseError('Ollama response content is empty.')
            return content

        message = response_payload.get('message')
        if isinstance(message, dict) and isinstance(message.get('content'), str):
            content = message['content'].strip()
            if not content:
                raise OllamaResponseError('Ollama response content is empty.')
            return content

        raise OllamaResponseError('Ollama response does not contain generated text.')

    def classify(self, prompt: str) -> str:
        response_payload = self.send_prompt(prompt)
        return self.parse_response(response_payload)

    @staticmethod
    def _build_http_error_message(status_code: int, error_body: str) -> str:
        cleaned_body = error_body.strip()
        if cleaned_body:
            return f'Ollama request failed with status {status_code}: {cleaned_body}'
        return f'Ollama request failed with status {status_code}.'
