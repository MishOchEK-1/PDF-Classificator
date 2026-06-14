from django.conf import settings


class PDFTextOptimizer:
    """Limits extracted PDF text before it is sent to the prompt builder."""

    def __init__(
        self,
        chunk_size: int | None = None,
        max_chunks: int | None = None,
        max_characters: int | None = None,
    ):
        self.chunk_size = max(1, chunk_size or settings.PDF_TEXT_CHUNK_SIZE)
        self.max_chunks = max(1, max_chunks or settings.PDF_TEXT_MAX_CHUNKS)
        self.max_characters = max(1, max_characters or settings.PDF_TEXT_MAX_CHARACTERS)

    def optimize(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return ''

        chunks = self.chunk_text(normalized)
        limited_chunks = []
        current_length = 0

        for chunk in chunks[: self.max_chunks]:
            separator_length = 2 if limited_chunks else 0
            available = self.max_characters - current_length - separator_length

            if available <= 0:
                break

            if len(chunk) <= available:
                limited_chunks.append(chunk)
                current_length += len(chunk) + separator_length
                continue

            limited_chunks.append(self._truncate_chunk(chunk, available))
            break

        return '\n\n'.join(chunk for chunk in limited_chunks if chunk).strip()

    def chunk_text(self, text: str) -> list[str]:
        chunks = []
        current_parts = []
        current_length = 0

        for section in self._split_sections(text):
            section_length = len(section)
            separator_length = 2 if current_parts else 0

            if current_parts and current_length + separator_length + section_length > self.chunk_size:
                chunks.append('\n\n'.join(current_parts))
                current_parts = [section]
                current_length = section_length
                continue

            current_parts.append(section)
            current_length += separator_length + section_length

        if current_parts:
            chunks.append('\n\n'.join(current_parts))

        return chunks

    def _split_sections(self, text: str) -> list[str]:
        sections = []

        for block in text.split('\n\n'):
            cleaned_block = block.strip()
            if not cleaned_block:
                continue

            if len(cleaned_block) <= self.chunk_size:
                sections.append(cleaned_block)
                continue

            sections.extend(self._split_large_block(cleaned_block))

        return sections

    def _split_large_block(self, block: str) -> list[str]:
        chunks = []
        remaining = block

        while remaining:
            if len(remaining) <= self.chunk_size:
                chunks.append(remaining)
                break

            split_at = remaining.rfind('\n', 0, self.chunk_size + 1)
            if split_at <= 0:
                split_at = self.chunk_size

            chunk = remaining[:split_at].strip()
            if chunk:
                chunks.append(chunk)

            remaining = remaining[split_at:].strip()

        return chunks

    def _truncate_chunk(self, chunk: str, max_length: int) -> str:
        truncated = chunk[:max_length].rstrip()
        if not truncated:
            return ''

        split_at = truncated.rfind('\n')
        if split_at > max_length // 2:
            return truncated[:split_at].rstrip()

        return truncated
