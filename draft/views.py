# draft/views.py
from django.views.generic import TemplateView, FormView
from django.urls import reverse_lazy
from .forms import MockDraftSettingsForm
from .models import Player
from .draft_engine import make_next_pick, build_empty_draft_board, initialize_draft_teams
from django.core.paginator import Paginator
from django.db.models import F, Value, BooleanField, ExpressionWrapper, Case, When
from django.conf import settings

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
    user_team_index = int(request.session.get("mock_settings", {}).get("draft_slot", 1)) - 1

    if not draft_board or not draft_teams:
        return JsonResponse({"success": False, "error": "Draft not initialized."})

    # calculate current cell (snake draft logic)
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

    # check if it's the user's turn
    if not team["is_user"]:
        return JsonResponse({"success": False, "error": "Not your turn."})

    # prevent duplicate picks
    if int(player_id) in drafted_ids:
        return JsonResponse({"success": False, "error": "Player already drafted."})

    # check if valid player is being selected
    try:
        player = Player.objects.select_related("team", "position").get(id=player_id)
    except Player.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid player."})

    # store selected player's info in the current draft board cell
    cell["player"] = {
        "id": player.id,
        "name": player.player_name,
        "position": player.position.abbreviation,
        "team": player.team.team_name if player.team else "N/A",
    }

    team["roster"].append(player.id)
    drafted_ids.append(player.id)
    session["current_pick_num"] = current_pick_num + 1

    # save session
    session["draft_board"] = draft_board
    session["draft_teams"] = draft_teams
    session["drafted_ids"] = drafted_ids

    # DEBUG DELETE LATER
    request.session.modified = True
    print("Saving drafted IDs:", session["drafted_ids"])  # Debugging

    # track updated cells
    updated_cells = [{
        "pick": cell["pick"],
        "name": player.player_name,
        "position": player.position.abbreviation,
        "team": player.team.team_name if player.team else "N/A",
        "player_id": player.id,
        "round": ((cell["pick"] - 1) // picks_per_round) + 1,
        "pick_in_round": ((cell["pick"] - 1) % picks_per_round) + 1,
    }]


    # auto-draft others
    all_players = Player.objects.select_related("position", "team").filter(adp__isnull=False).order_by('adp')

    # call to make the next draft pick
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
                "team": auto_cell["player"]["team"],
                "player_id": auto_cell["player"]["id"],
                "round": ((cell["pick"] - 1) // picks_per_round) + 1,
                "pick_in_round": ((cell["pick"] - 1) % picks_per_round) + 1
            })

    # get user's drafted players
    user_team = draft_teams[user_team_index]
    user_roster_ids = user_team["roster"]
    user_players = Player.objects.filter(id__in=user_roster_ids).select_related("team", "position")

    # preserve order
    user_players_dict = {p.id: p for p in user_players}
    ordered_user_players = [user_players_dict[pid] for pid in user_roster_ids if pid in user_players_dict]

    picks_per_round = len(draft_teams)  # add this line near the top of the function if not already defined

    user_roster_data = []
    for p in ordered_user_players:
        round_num, pick_in_round = get_player_pick_info(draft_board, p.id, picks_per_round)
        user_roster_data.append({
            "name": p.player_name,
            "position": p.position.abbreviation,
            "team": p.team.team_name if p.team else "N/A",
            "round": round_num,
            "pick_in_round": pick_in_round,
        })

    # Prepare user roster ordered by position using helper function
    user_roster_ordered = sort_user_roster(user_roster_data, request.session.get("mock_settings", {}))

    return JsonResponse({
        "success": True,
        "updated_cells": updated_cells,
        "user_roster": user_roster_data,
    })

def get_player_pick_info(draft_board, player_id, picks_per_round):
    for round_idx, round_picks in enumerate(draft_board):
        for pick_idx, cell in enumerate(round_picks):
            if cell.get("player") and cell["player"]["id"] == player_id:
                overall_pick = cell["pick"]  # overall pick number (1-based)
                round_num = ((overall_pick - 1) // picks_per_round) + 1
                pick_in_round = ((overall_pick - 1) % picks_per_round) + 1
                return round_num, pick_in_round
    return None, None

def get_user_roster_ordered(session, draft_teams, settings):
    try:
        draft_slot = int(session.get("mock_settings", {}).get("draft_slot", 1))
        user_team_index = draft_slot - 1
    except Exception:
        user_team_index = 0

    user_team = draft_teams[user_team_index]
    user_roster_ids = user_team.get("roster", [])

    user_players = list(
        Player.objects.filter(id__in=user_roster_ids)
            .select_related("team", "position")
    )

    positions_order = ['qb', 'rb', 'wr', 'te', 'flex', 'bench']
    flex_eligible_positions = ['rb', 'wr', 'te']

    players_by_position = {pos: [] for pos in positions_order}

    id_to_player = {p.id: p for p in user_players}

    for pid in user_roster_ids:
        p = id_to_player.get(pid)
        if not p:
            continue
        pos = p.position.abbreviation.lower()
        if pos in players_by_position:
            players_by_position[pos].append({
                "name": p.player_name,
                "position": p.position.abbreviation,
                "team": p.team.team_name if p.team else "N/A",
            })
        else:
            if pos in flex_eligible_positions:
                players_by_position['flex'].append({
                    "name": p.player_name,
                    "position": p.position.abbreviation,
                    "team": p.team.team_name if p.team else "N/A",
                })

    user_roster_ordered = []
    for pos in positions_order:
        count = int(settings.get(pos, 0))
        user_roster_ordered.extend(players_by_position[pos][:count])

    return user_roster_ordered    

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

        # clearing old draft session variables before starting a new draft
        for key in [
            "draft_board", "draft_teams", "drafted_ids",
            "current_team", "current_round", "current_pick_num"
        ]:
            self.request.session.pop(key, None)

        # store the settings in session or pass via GET params
        self.request.session["mock_settings"] = form.cleaned_data
        return super().form_valid(form)



class MockDraftView(TemplateView):
    template_name = "mock-draft/draft_board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        settings, num_teams, draft_slot, user_team_index, num_rounds = self.get_draft_settings()

        if self.request.GET.get('reset') == '1':
            self.reset_draft_session(num_rounds, num_teams, user_team_index)

        if "draft_teams" not in self.request.session:
            self.request.session["draft_teams"] = initialize_draft_teams(num_teams, user_team_index)

        if "draft_board" not in self.request.session:
            self.request.session["draft_board"] = build_empty_draft_board(num_rounds, num_teams)

        self.request.session.setdefault("drafted_ids", [])
        self.request.session.setdefault("current_team", 0)
        self.request.session.setdefault("current_round", 0)
        self.request.session.setdefault("current_pick_num", 0)

        all_players = self.get_all_sorted_players()

        while make_next_pick(self.request.session, all_players):
            continue

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
        return Player.objects.annotate(
            has_adp=Case(
                When(adp__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by('-has_adp', 'adp', 'player_name')

    def get_draft_settings(self):
        draft_settings = self.request.session.get("mock_settings", {})
        num_teams = int(draft_settings.get("num_teams", 12))
        draft_slot = int(draft_settings.get("draft_slot", 1))
        user_team_index = draft_slot - 1
        num_rounds = draft_settings.get("num_rounds", 15)
        return draft_settings, num_teams, draft_slot, user_team_index, num_rounds

  

class DraftHistoryView(TemplateView):
    template_name = "draft_history.html"



from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator

@require_GET
def filter_players_ajax(request):
    selected_position = request.GET.get("position")
    drafted_ids = request.session.get("drafted_ids", [])

    players_qs = Player.objects.all()

    if selected_position:
        players_qs = players_qs.filter(position__abbreviation=selected_position)

    # Always exclude drafted players
    if drafted_ids:
        players_qs = players_qs.exclude(id__in=drafted_ids)

    players = players_qs.annotate(
        has_adp=Case(
            When(adp__isnull=False, then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).order_by('-has_adp', 'adp', 'player_name')[:100]

    html = render_to_string("mock-draft/player_list.html", {"players": players})
    return JsonResponse({"html": html})



# HELPER FUNCTIONS
def sort_user_roster(players, settings):
    """
    Sort drafted players into roster slots based on the settings.
    Input: list of player dicts, and settings dict
    Output: ordered list of players
    """
    slots = {
        "qb": settings.get("qb", 0),
        "rb": settings.get("rb", 0),
        "wr": settings.get("wr", 0),
        "te": settings.get("te", 0),
        "flex": settings.get("flex", 0),
        "k": settings.get("k", 0),
        "dst": settings.get("dst", 0),
        "bench": settings.get("bench", 0),
    }

    positions_order = ["qb", "rb", "wr", "te", "flex", "k", "dst", "bench"]
    flex_eligible = {"rb", "wr", "te"}

    filled = {pos: 0 for pos in positions_order}
    sorted_team = [None] * sum(slots.values())

    for p in players:
        pos = p["position"].lower()

        # Try main position
        if pos in slots and filled[pos] < slots[pos]:
            index = sum(slots[o] for o in positions_order[:positions_order.index(pos)]) + filled[pos]
            sorted_team[index] = p
            filled[pos] += 1
        # Try FLEX
        elif pos in flex_eligible and filled["flex"] < slots["flex"]:
            index = sum(slots[o] for o in positions_order[:positions_order.index("flex")]) + filled["flex"]
            sorted_team[index] = p
            filled["flex"] += 1
        # Otherwise, go to bench
        elif filled["bench"] < slots["bench"]:
            index = sum(slots[o] for o in positions_order[:positions_order.index("bench")]) + filled["bench"]
            sorted_team[index] = p
            filled["bench"] += 1

    return [p for p in sorted_team if p]  # Remove None slots
