from dataclasses import dataclass
from pathlib import Path

import fitz

from .exceptions import CorruptedPDFError, EmptyPDFError, ScannedPDFError


@dataclass(slots=True)
class ExtractedPDFDocument:
    text: str
    page_count: int


class PDFParser:
    """Extracts textual content from PDF files using PyMuPDF."""

    def extract_text(self, pdf_path: str | Path) -> ExtractedPDFDocument:
        path = Path(pdf_path)
        document = None

        try:
            document = fitz.open(path)
        except Exception as exc:
            raise CorruptedPDFError() from exc

        try:
            if document.page_count == 0:
                raise EmptyPDFError('The uploaded PDF does not contain any pages.')

            text_fragments = [page.get_text('text') for page in document]
            raw_text = '\n'.join(text_fragments)

            if not raw_text.strip():
                raise ScannedPDFError()

            return ExtractedPDFDocument(text=raw_text, page_count=document.page_count)
        finally:
            document.close()
