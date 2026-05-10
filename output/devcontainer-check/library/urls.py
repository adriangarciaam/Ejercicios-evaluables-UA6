from django.urls import path

from .views import entries, entry_detail


urlpatterns = [
    path("entries/", entries),
    path("entries/<int:entry_id>/", entry_detail),
]
