from pathlib import Path

from django.conf import settings
from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    ollama_url = serializers.CharField(required=False, allow_blank=True)


class ClassifyDocumentRequestSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        suffix = Path(value.name).suffix.lower()

        if suffix != '.pdf':
            raise serializers.ValidationError('Only PDF files are supported.')

        if value.size == 0:
            raise serializers.ValidationError('The uploaded PDF is empty.')

        if value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes.'
            )

        return value
