# draft/views.py
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import MockDraftSettingsForm

class HomePageView(TemplateView):
    template_name = "home.html"

class MockSettingsView(FormView):
    template_name = "mock-draft/mock_settings.html"
    form_class = MockDraftSettingsForm
    success_url = reverse_lazy("mock_draft") # URL name for actual draft view

    def form_valid(self, form):
        total_positions = sum([
            form.cleaned_data.get("qb", 0),
            form.cleaned_data.get("rb", 0),
            form.cleaned_data.get("wr", 0),
            form.cleaned_data.get("te", 0),
            form.cleaned_data.get("flex", 0),
            form.cleaned_data.get("k", 0),
            form.cleaned_data.get("dst", 0),
            form.cleaned_data.get("bench", 0),
        ])

        if total_positions == 0:
            form.add_error(None, "You must select at least one roster position.")
            return self.form_invalid(form)

        # store the settings in session or pass via GET params
        self.request.session["mock_settings"] = form.cleaned_data
        return super().form_valid(form)

class MockDraftView(TemplateView):
    template_name = "mock-draft/draft_board.html" # change html name later

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = self.request.session.get("mock_settings", {})
        context["settings"] = settings
        return context

class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"

