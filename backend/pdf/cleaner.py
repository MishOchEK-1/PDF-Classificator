import re


def clean_extracted_text(text: str) -> str:
    normalized = text.replace('\x00', ' ').replace('\ufeff', ' ').replace('\f', '\n')
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')

    cleaned_lines = []
    blank_pending = False

    for raw_line in normalized.split('\n'):
        line = re.sub(r'[ \t]+', ' ', raw_line).strip()

        if not line:
            if cleaned_lines:
                blank_pending = True
            continue

        if blank_pending:
            cleaned_lines.append('')
            blank_pending = False

        cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines).strip()
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text
