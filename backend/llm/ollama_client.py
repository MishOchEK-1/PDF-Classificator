class OllamaClient:
    """Thin client wrapper for the local Ollama runtime."""

    def classify(self, prompt: str) -> dict:
        raise NotImplementedError('Ollama integration will be implemented in Stage 6.')
