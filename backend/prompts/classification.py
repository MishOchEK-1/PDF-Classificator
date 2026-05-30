ALLOWED_DOCUMENT_CLASSES = (
    'resume',
    'invoice',
    'contract',
    'academic_paper',
    'technical_documentation',
    'assignment',
    'report',
    'unknown',
)


def build_classification_prompt(extracted_text: str) -> str:
    raise NotImplementedError('Prompt builder will be implemented in Stage 5.')
