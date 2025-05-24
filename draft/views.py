# draft/views.py
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import MockDraftSettingsForm
from .models import Player
from .draft_engine import make_next_pick, build_empty_draft_board, initialize_draft_teams
from django.core.paginator import Paginator
from django.db.models import F, Value, BooleanField, ExpressionWrapper, Case, When

from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@require_POST
def draft_player_ajax(request):
    data = json.loads(request.body)
    player_id = data.get("player_id")

    session = request.session
    draft_board = session.get("draft_board")
    draft_teams = session.get("draft_teams")
    drafted_ids = session.get("drafted_ids", [])
    current_pick_num = session.get("current_pick_num", 0)

    if not draft_board or not draft_teams:
        return JsonResponse({"success": False, "error": "Draft not initialized."})

    # 🧠 Calculate current cell (snake draft logic)
    picks_per_round = len(draft_teams)
    num_rounds = len(draft_board)
    total_picks = picks_per_round * num_rounds

    if current_pick_num >= total_picks:
        return JsonResponse({"success": False, "error": "Draft is complete."})

    current_round = current_pick_num // picks_per_round
    team_index_in_round = current_pick_num % picks_per_round
    cell = draft_board[current_round][team_index_in_round]
    team_index = cell["team"]
    team = draft_teams[team_index]

    # ❌ Check if it's the user's turn
    if not team["is_user"]:
        return JsonResponse({"success": False, "error": "Not your turn."})

    # 🚫 Prevent duplicate picks
    if int(player_id) in drafted_ids:
        return JsonResponse({"success": False, "error": "Player already drafted."})

    try:
        player = Player.objects.select_related("team", "position").get(id=player_id)
    except Player.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid player."})

    # ✅ Draft the player
    cell["player"] = {
        "id": player.id,
        "name": player.player_name,
        "position": player.position.abbreviation,
        "team": player.team.team_name if player.team else "N/A",
    }

    team["roster"].append(player.id)
    drafted_ids.append(player.id)
    session["current_pick_num"] = current_pick_num + 1

    # 🔐 Save session
    session["draft_board"] = draft_board
    session["draft_teams"] = draft_teams
    session["drafted_ids"] = drafted_ids

    # ✅ Track updated cells
    updated_cells = [{
        "pick": cell["pick"],
        "name": player.player_name,
        "position": player.position.abbreviation,
        "team": player.team.team_name if player.team else "N/A",
    }]

    # 🤖 Auto-draft others
    all_players = Player.objects.select_related("position", "team").all().order_by('-adp')
    while make_next_pick(session, all_players):
        cur_pick = session["current_pick_num"] - 1
        cur_round = cur_pick // picks_per_round
        team_index_in_round = cur_pick % picks_per_round
        auto_cell = draft_board[cur_round][team_index_in_round]
        if auto_cell["player"]:
            updated_cells.append({
                "pick": auto_cell["pick"],
                "name": auto_cell["player"]["name"],
                "position": auto_cell["player"]["position"],
                "team": auto_cell["player"]["team"]
            })

    return JsonResponse({
        "success": True,
        "updated_cells": updated_cells,
    })

class HomePageView(TemplateView):
    template_name = "home.html"

class MockSettingsView(FormView):
    template_name = "mock-draft/mock_settings.html"
    form_class = MockDraftSettingsForm
    success_url = reverse_lazy("mock_draft") 

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
    template_name = "mock-draft/draft_board.html"

    # called automatically by django, if other functions needed they are called in here and defined below this function
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # extract draft settings and key values
        settings, num_teams, draft_slot, user_team_index, num_rounds = self.get_draft_settings()

        # initialize draft teams only once per session
        if "draft_teams" not in self.request.session:
            self.request.session["draft_teams"] = initialize_draft_teams(num_teams, user_team_index)

        # initializing an empty draft board structure (rounds x teams)
        if "draft_board" not in self.request.session:
            self.request.session["draft_board"] = build_empty_draft_board(num_rounds, num_teams)

        self.request.session.setdefault("drafted_ids", [])
        self.request.session.setdefault("current_team", 0)
        self.request.session.setdefault("current_round", 0)

        # 🔁 Run auto-draft loop until user's pick or draft ends
        all_players = self.get_all_sorted_players()
 
        self.reset_draft_session(num_rounds, num_teams, user_team_index)

        while make_next_pick(self.request.session, all_players):
            continue

        # retrieve filtered, sorted, and paginated players for display
        page_obj, selected_position = self.get_display_players()

        context.update({
            "settings": settings,
            "num_teams": num_teams,
            "num_rounds": num_rounds,
            "draft_board": self.request.session["draft_board"],
            "players": page_obj.object_list,
            "page_obj": page_obj,
            "selected_position": selected_position,
            "user_team_index": user_team_index,
        })

        return context

    def reset_draft_session(self, num_rounds, num_teams, user_team_index):
        self.request.session["draft_board"] = build_empty_draft_board(num_rounds, num_teams)
        self.request.session["drafted_ids"] = []
        self.request.session["draft_teams"] = initialize_draft_teams(num_teams, user_team_index)
        self.request.session["current_team"] = 0
        self.request.session["current_round"] = 0
        self.request.session["current_pick_num"] = 0

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

    def get_all_sorted_players(self):
        players = Player.objects.all().annotate(
            has_adp=Case(
                When(adp__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-has_adp', 'adp', 'player_name')
        return players

    def get_draft_settings(self):
        settings = self.request.session.get("mock_settings", {})
        num_teams = int(settings.get("num_teams", 12))
        draft_slot = int(settings.get("draft_slot", 1))  # 1-based (e.g. pick 6)
        user_team_index = draft_slot - 1                # Convert to 0-based
        num_rounds = settings.get("num_rounds", 15)

        return settings, num_teams, draft_slot, user_team_index, num_rounds

  

class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"

