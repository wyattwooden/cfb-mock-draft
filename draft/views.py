# draft/views.py
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import MockDraftSettingsForm
from .models import Player
from .draft_engine import run_auto_draft, build_empty_draft_board
from django.core.paginator import Paginator

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

    # called automatically by django, if other functions needed they are called in here and defined below this function
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Extract draft settings and key values
        settings, num_teams, draft_slot, user_team_index, num_rounds = self.get_draft_settings()

        # initializing an empty draft board structure (rounds x teams)
        draft_board = build_empty_draft_board(num_rounds, num_teams)

        # retrieve filtered, sorted, and paginated players for display
        page_obj, selected_position = self.get_display_players()

        # calling function to start the draft
        run_auto_draft()

        context.update({
            "settings": settings,
            "num_teams": num_teams,
            "num_rounds": num_rounds,
            "draft_board": draft_board,
            "players": page_obj.object_list,
            "page_obj": page_obj,
            "selected_position": selected_position,
            "user_team_index": user_team_index,
        })

        return context

    def get_display_players(self):
        selected_position = self.request.GET.get("position")
        players_qs = Player.objects.all()

        if selected_position:
            players_qs = players_qs.filter(position__abbreviation=selected_position)

        players = players_qs.annotate(
            has_adp=Case(
                When(adp__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-has_adp', 'adp', 'player_name')

        paginator = Paginator(players, 100)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return page_obj, selected_position

    def get_draft_settings(self):
        settings = self.request.session.get("mock_settings", {})
        num_teams = int(settings.get("num_teams", 12))
        draft_slot = int(settings.get("draft_slot", 1))  # 1-based (e.g. pick 6)
        user_team_index = draft_slot - 1                # Convert to 0-based
        num_rounds = settings.get("num_rounds", 15)

        return settings, num_teams, draft_slot, user_team_index, num_rounds

  


class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"

