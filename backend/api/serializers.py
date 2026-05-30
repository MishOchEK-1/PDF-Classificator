from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()
    ollama_url = serializers.CharField(required=False, allow_blank=True)


class ClassifyDocumentRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
