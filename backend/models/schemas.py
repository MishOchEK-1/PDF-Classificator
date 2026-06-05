from dataclasses import dataclass


@dataclass(slots=True)
class ClassificationSchema:
    document_class: str
    tags: list[str]
    confidence: float

    def to_api_payload(self) -> dict:
        return {
            'class': self.document_class,
            'tags': self.tags,
            'confidence': self.confidence,
        }
