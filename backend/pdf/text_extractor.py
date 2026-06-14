import fitz


class PDFTextExtractor:
    """Builds a single LLM-ready text stream from PDF text blocks."""

    def extract(self, document: fitz.Document) -> str:
        page_texts = []

        for page in document:
            page_text = self._extract_page_text(page)
            if page_text:
                page_texts.append(page_text)

        return '\n\n'.join(page_texts)

    def _extract_page_text(self, page: fitz.Page) -> str:
        page_data = page.get_text('dict', sort=True)
        text_blocks = []

        for block in page_data.get('blocks', []):
            if block.get('type') != 0:
                continue

            lines = []

            for line in block.get('lines', []):
                spans = line.get('spans', [])
                line_text = ''.join(span.get('text', '') for span in spans).strip()

                if line_text:
                    lines.append(line_text)

            if lines:
                text_blocks.append('\n'.join(lines))

        return '\n\n'.join(text_blocks).strip()
