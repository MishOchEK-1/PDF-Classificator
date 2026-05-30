from dataclasses import dataclass


@dataclass(slots=True)
class ClassificationSchema:
    document_class: str
    tags: list[str]
    confidence: float
