from django.urls import path

from .views import entries, entry_detail


urlpatterns = [
    # Lista las entradas del usuario o crea una entrada nueva.
    path("entries/", entries),
    # Consulta o actualiza una entrada concreta por su identificador.
    path("entries/<int:entry_id>/", entry_detail),
]
