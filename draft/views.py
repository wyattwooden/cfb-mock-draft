# draft/views.py
from django.views.generic import TemplateView

class HomePageView(TemplateView):
    template_name = "home.html"

class MockNowView(TemplateView):
    template_name = "mock_now.html"

class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"

