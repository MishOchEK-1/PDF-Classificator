from django.urls import path

from .views import ClassifyDocumentView, HealthCheckView

app_name = 'api'

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('classify/', ClassifyDocumentView.as_view(), name='classify'),
]
