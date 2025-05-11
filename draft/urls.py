# draft/urls.py
from django.urls import path
from .views import home, mock_now, draft_history

urlpatterns = [
    path("", home, name="home"),
    path("mock_now/", mock_now, name="mock_now"),
    path("draft_history/", draft_history, name="draft_history"),
]