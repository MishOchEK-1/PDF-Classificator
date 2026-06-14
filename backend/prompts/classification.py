from textwrap import dedent

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

CLASSIFICATION_RESPONSE_SCHEMA = {
    'type': 'object',
    'properties': {
        'class': {
            'type': 'string',
            'enum': list(ALLOWED_DOCUMENT_CLASSES),
        },
        'tags': {
            'type': 'array',
            'items': {
                'type': 'string',
                'pattern': '^[a-z0-9_]+$',
                'minLength': 1,
            },
        },
        'confidence': {
            'type': 'number',
            'minimum': 0,
            'maximum': 1,
        },
    },
    'required': ['class', 'tags', 'confidence'],
    'additionalProperties': False,
}


def build_classification_prompt(extracted_text: str) -> str:
    classes_block = '\n'.join(f'- {document_class}' for document_class in ALLOWED_DOCUMENT_CLASSES)
    cleaned_text = extracted_text.strip()

    return dedent(
        f"""
        You are a strict document classification assistant.

        You will receive plain text extracted from a PDF document.
        The original PDF file is not available to you.
        Use only the extracted text as evidence.
        Do not invent facts that are not present in the document text.

        Classify the document into exactly one allowed class.

        Allowed classes:
        {classes_block}

        If the document text is incomplete, ambiguous, or does not clearly fit an allowed class,
        return "unknown" with lower confidence.

        Return exactly one JSON object and nothing else.
        Do not include markdown.
        Do not include code fences.
        Do not include explanations.
        Do not include commentary.
        Do not echo the document text.
        Do not include extra keys.

        Required JSON schema:
        {{
          "class": "one_of_the_allowed_classes",
          "tags": ["lowercase_tag", "lowercase_tag"],
          "confidence": 0.0
        }}

        Requirements:
        - "class" must be exactly one value from the allowed classes list.
        - "tags" must be an array of short lowercase snake_case tags grounded in the document text.
        - "confidence" must be a number from 0 to 1.
        - confidence should be lower when evidence is weak or partial.
        - confidence should be high only when the extracted text strongly supports the chosen class.

        Extracted document text:
        <document_text>
        {cleaned_text}
        </document_text>
        """
    ).strip()
