# draft/urls.py
from django.urls import path
from .views import HomePageView, MockNowView, DraftHistoryView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("mock/", MockNowView.as_view(), name="mock_now"),
    path("my-drafts/", DraftHistoryView.as_view(), name="draft_history"),
]
