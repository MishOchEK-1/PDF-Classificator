from dataclasses import dataclass
from pathlib import Path

from backend.pdf.cleaner import clean_extracted_text
from backend.pdf.exceptions import EmptyPDFError
from backend.pdf.parser import PDFParser
from backend.pdf.storage import TemporaryPDFStorage


@dataclass(slots=True)
class ProcessedPDFDocument:
    original_name: str
    stored_path: Path
    page_count: int
    cleaned_text: str


class PDFProcessingService:
    def __init__(self, storage: TemporaryPDFStorage | None = None, parser: PDFParser | None = None):
        self.storage = storage or TemporaryPDFStorage()
        self.parser = parser or PDFParser()

    def process_upload(self, uploaded_file) -> ProcessedPDFDocument:
        stored_file = self.storage.save(uploaded_file)

        try:
            extracted_document = self.parser.extract_text(stored_file.stored_path)
            cleaned_text = clean_extracted_text(extracted_document.text)

            if not cleaned_text:
                raise EmptyPDFError('The uploaded PDF does not contain usable text after cleaning.')

            self.storage.cleanup_old_files(exclude=stored_file.stored_path)

            return ProcessedPDFDocument(
                original_name=stored_file.original_name,
                stored_path=stored_file.stored_path,
                page_count=extracted_document.page_count,
                cleaned_text=cleaned_text,
            )
        except Exception:
            stored_file.stored_path.unlink(missing_ok=True)
            raise
