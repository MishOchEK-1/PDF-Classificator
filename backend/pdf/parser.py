from dataclasses import dataclass
from pathlib import Path

import fitz

from .exceptions import CorruptedPDFError, EmptyPDFError, ScannedPDFError
from .text_extractor import PDFTextExtractor


@dataclass(slots=True)
class ExtractedPDFDocument:
    text: str
    page_count: int


class PDFParser:
    """Extracts textual content from PDF files using PyMuPDF."""

    def __init__(self, text_extractor: PDFTextExtractor | None = None):
        self.text_extractor = text_extractor or PDFTextExtractor()

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

            raw_text = self.text_extractor.extract(document)

            if not raw_text.strip():
                raise ScannedPDFError()

            return ExtractedPDFDocument(text=raw_text, page_count=document.page_count)
        finally:
            document.close()
