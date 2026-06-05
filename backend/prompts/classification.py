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


def build_classification_prompt(extracted_text: str) -> str:
    classes_block = '\n'.join(f'- {document_class}' for document_class in ALLOWED_DOCUMENT_CLASSES)
    cleaned_text = extracted_text.strip()

    return dedent(
        f"""
        You are a document classification assistant.

        Your input is plain text extracted from a PDF document.
        The original PDF file is not available to you.

        Classify the document into exactly one allowed class.

        Allowed classes:
        {classes_block}

        Return JSON only.
        Do not include markdown.
        Do not include code fences.
        Do not include explanations.
        Do not include extra keys.

        Required JSON schema:
        {{
          "class": "one_of_the_allowed_classes",
          "tags": ["lowercase_tag", "lowercase_tag"],
          "confidence": 0.0
        }}

        Requirements:
        - "class" must be exactly one value from the allowed classes list.
        - "tags" must be an array of short lowercase snake_case tags.
        - "confidence" must be a number from 0 to 1.

        Extracted document text:
        \"\"\"
        {cleaned_text}
        \"\"\"
        """
    ).strip()
