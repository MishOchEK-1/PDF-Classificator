from dataclasses import dataclass


@dataclass(slots=True)
class ClassificationResult:
    document_class: str
    tags: list[str]
    confidence: float


class ClassificationService:
    """Coordinates the future end-to-end PDF classification pipeline."""

    def classify(self, pdf_file) -> ClassificationResult:
        raise NotImplementedError('Pipeline implementation is planned for Stage 4-7.')
