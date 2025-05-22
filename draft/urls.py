# draft/urls.py
from django.urls import path
from .views import HomePageView, MockSettingsView, MockDraftView, DraftHistoryView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("mock/", MockSettingsView.as_view(), name="mock_settings"),
    path("mock/draft", MockDraftView.as_view(), name="mock_draft"),
    path("my-drafts/", DraftHistoryView.as_view(), name="draft_history"),
]
