from rest_framework.exceptions import APIException

from backend.llm.ollama_client import (
    OllamaClient,
    OllamaClientError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)
from backend.models.schemas import ClassificationSchema
from backend.prompts.classification import build_classification_prompt
from backend.prompts.validation import (
    PromptResponseValidationError,
    validate_classification_response,
)

from .pdf_processing_service import PDFProcessingService


class ClassificationPipelineError(APIException):
    status_code = 502
    default_code = 'classification_pipeline_error'
    default_detail = 'The classification pipeline failed.'


class ClassificationTimeoutAPIError(APIException):
    status_code = 504
    default_code = 'classification_timeout'
    default_detail = 'The local model request timed out.'


class ClassificationUnavailableAPIError(APIException):
    status_code = 503
    default_code = 'classification_unavailable'
    default_detail = 'The local model is unavailable.'


class ClassificationResponseAPIError(APIException):
    status_code = 502
    default_code = 'invalid_model_response'
    default_detail = 'The model returned an invalid classification response.'


class ClassificationService:
    """Coordinates the future end-to-end PDF classification pipeline."""

    def __init__(
        self,
        pdf_processing_service: PDFProcessingService | None = None,
        ollama_client: OllamaClient | None = None,
    ):
        self.pdf_processing_service = pdf_processing_service or PDFProcessingService()
        self.ollama_client = ollama_client or OllamaClient()

    def classify(self, pdf_file) -> ClassificationSchema:
        processed_document = self.pdf_processing_service.process_upload(pdf_file)
        prompt = build_classification_prompt(processed_document.cleaned_text)

        try:
            raw_response = self.ollama_client.classify(prompt)
        except OllamaTimeoutError as exc:
            raise ClassificationTimeoutAPIError(str(exc)) from exc
        except OllamaUnavailableError as exc:
            raise ClassificationUnavailableAPIError(str(exc)) from exc
        except OllamaClientError as exc:
            raise ClassificationPipelineError(str(exc)) from exc

        try:
            return validate_classification_response(raw_response)
        except PromptResponseValidationError as exc:
            raise ClassificationResponseAPIError(str(exc)) from exc
