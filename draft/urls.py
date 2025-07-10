# draft/urls.py
from django.urls import path
from .views import HomePageView, MockSettingsView, MockDraftView, DraftHistoryView, draft_player_ajax, filter_players_ajax

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("mock/", MockSettingsView.as_view(), name="mock_settings"),
    path("mock/draft", MockDraftView.as_view(), name="mock_draft"),
    path("mock/draft/pick/", draft_player_ajax, name="draft_player_ajax"),
    path("mock/filter_players/", filter_players_ajax, name="filter_players_ajax"),
    path("my-drafts/", DraftHistoryView.as_view(), name="draft_history"),
]
