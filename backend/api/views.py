from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.services.classification_service import ClassificationService

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
    """Runs the current end-to-end classification pipeline for a single PDF."""

    classification_service = ClassificationService()

    def post(self, request):
        serializer = ClassifyDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.classification_service.classify(serializer.validated_data['file'])

        return Response(result.to_api_payload(), status=status.HTTP_200_OK)
