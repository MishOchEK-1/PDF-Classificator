from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ClassifyDocumentRequestSerializer, HealthCheckSerializer


class HealthCheckView(APIView):
    """Lightweight endpoint used by the frontend and local orchestration."""

    def get(self, request):
        payload = HealthCheckSerializer(
            {
                'status': 'ok',
                'service': 'pdf-classification-backend',
                'ollama_url': settings.OLLAMA_URL,
            }
        )
        return Response(payload.data, status=status.HTTP_200_OK)


class ClassifyDocumentView(APIView):
    """
    Stage 1 stub for the future document classification pipeline.

    The full upload, parsing, prompt generation, and Ollama integration will
    be implemented in later stages of the plan.
    """

    def post(self, request):
        serializer = ClassifyDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                'detail': 'Classification pipeline is not implemented yet.',
                'expected_response': {
                    'class': 'technical_documentation',
                    'tags': ['python', 'backend', 'api'],
                    'confidence': 0.92,
                },
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
