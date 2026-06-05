import json
import re

from backend.models.schemas import ClassificationSchema

from .classification import ALLOWED_DOCUMENT_CLASSES

TAG_PATTERN = re.compile(r'^[a-z0-9_]+$')


class PromptResponseValidationError(ValueError):
    """Raised when the model output does not match the expected JSON contract."""


def validate_classification_response(raw_response: str | dict) -> ClassificationSchema:
    payload = _parse_payload(raw_response)
    _validate_required_fields(payload)

    document_class = payload['class']
    tags = payload['tags']
    confidence = payload['confidence']

    if document_class not in ALLOWED_DOCUMENT_CLASSES:
        raise PromptResponseValidationError('Response contains an unsupported document class.')

    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise PromptResponseValidationError('Confidence must be a numeric value.')

    confidence = float(confidence)
    if confidence < 0 or confidence > 1:
        raise PromptResponseValidationError('Confidence must be within the range 0 to 1.')

    normalized_tags = _validate_and_normalize_tags(tags)

    return ClassificationSchema(
        document_class=document_class,
        tags=normalized_tags,
        confidence=confidence,
    )


def _parse_payload(raw_response: str | dict) -> dict:
    if isinstance(raw_response, dict):
        return raw_response

    if not isinstance(raw_response, str):
        raise PromptResponseValidationError('Model response must be a JSON string or dictionary.')

    candidate = raw_response.strip()
    if '```' in candidate:
        raise PromptResponseValidationError('Markdown-formatted responses are not allowed.')

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise PromptResponseValidationError('Model response is not valid JSON.') from exc

    if not isinstance(parsed, dict):
        raise PromptResponseValidationError('Model response JSON must be an object.')

    return parsed


def _validate_required_fields(payload: dict) -> None:
    required_fields = {'class', 'tags', 'confidence'}
    missing_fields = required_fields - payload.keys()

    if missing_fields:
        joined = ', '.join(sorted(missing_fields))
        raise PromptResponseValidationError(f'Model response is missing required fields: {joined}.')


def _validate_and_normalize_tags(tags: object) -> list[str]:
    if not isinstance(tags, list):
        raise PromptResponseValidationError('Tags must be provided as an array.')

    normalized_tags = []
    for tag in tags:
        if not isinstance(tag, str):
            raise PromptResponseValidationError('Each tag must be a string.')

        normalized_tag = re.sub(r'\s+', '_', tag.strip().lower())
        if not normalized_tag:
            raise PromptResponseValidationError('Tags cannot be empty.')

        if not TAG_PATTERN.fullmatch(normalized_tag):
            raise PromptResponseValidationError(
                'Tags must contain only lowercase letters, numbers, and underscores.'
            )

        normalized_tags.append(normalized_tag)

    return normalized_tags
