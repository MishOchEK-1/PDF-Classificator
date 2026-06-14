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
        text_blocks = []

        for block in page.get_text('blocks', sort=True):
            block_type = block[6] if len(block) > 6 else 0
            if block_type != 0:
                continue

            block_text = block[4].strip()
            if block_text:
                text_blocks.append(block_text)

        return '\n\n'.join(text_blocks).strip()
