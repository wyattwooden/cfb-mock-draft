# draft/views.py
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import MockDraftSettingsForm
from .models import Player

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

from django.db.models import F, Value, BooleanField, ExpressionWrapper, Case, When

class MockDraftView(TemplateView):
    template_name = "mock-draft/draft_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        settings = request.session.get("mock_settings", {})
        num_teams = int(settings.get("num_teams", 12))

        num_rounds = sum([
            int(settings.get("qb", 0)),
            int(settings.get("rb", 0)),
            int(settings.get("wr", 0)),
            int(settings.get("te", 0)),
            int(settings.get("flex", 0)),
            int(settings.get("k", 0)),
            int(settings.get("dst", 0)),
            int(settings.get("bench", 0)),
        ])

        draft_board = []
        for rnd in range(1, num_rounds + 1):
            row = []
            for team in range(1, num_teams + 1):
                pick_number = f"{rnd}.{str(team).zfill(2)}"
                row.append({
                    "team": team,
                    "round": rnd,
                    "pick": pick_number,
                    "player": None
                })
            draft_board.append(row)

        # 🟨 Position filter from GET
        selected_position = request.GET.get("position")

        players_qs = Player.objects.all()
        if selected_position:
            players_qs = players_qs.filter(position__abbreviation=selected_position)


        # Sort by: has_adp DESC, adp ASC, name ASC
        players = players_qs.annotate(
            has_adp=Case(
                When(adp__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-has_adp', 'adp', 'player_name')

        context.update({
            "settings": settings,
            "num_teams": num_teams,
            "num_rounds": num_rounds,
            "draft_board": draft_board,
            "players": players,
            "selected_position": selected_position,
        })
        return context



class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"

