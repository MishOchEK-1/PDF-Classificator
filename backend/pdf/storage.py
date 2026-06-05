from dataclasses import dataclass
from pathlib import Path
from time import time
from uuid import uuid4

from django.conf import settings


DEFAULT_TEMP_FILE_TTL_SECONDS = 24 * 60 * 60


@dataclass(slots=True)
class StoredPDFFile:
    original_name: str
    stored_path: Path


class TemporaryPDFStorage:
    def __init__(self, root: Path | None = None, ttl_seconds: int = DEFAULT_TEMP_FILE_TTL_SECONDS):
        self.root = Path(root or settings.TEMP_UPLOAD_ROOT)
        self.ttl_seconds = ttl_seconds

    def cleanup_old_files(self, exclude: Path | None = None) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        now = time()

        for file_path in self.root.glob('*.pdf'):
            if exclude and file_path == exclude:
                continue

            if now - file_path.stat().st_mtime > self.ttl_seconds:
                file_path.unlink(missing_ok=True)

    def save(self, uploaded_file) -> StoredPDFFile:
        self.root.mkdir(parents=True, exist_ok=True)
        self.cleanup_old_files()

        file_name = f'{uuid4().hex}.pdf'
        stored_path = self.root / file_name

        with stored_path.open('wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return StoredPDFFile(original_name=uploaded_file.name, stored_path=stored_path)
