# draft/draft_engine.py
# file containing functions used for drafting

# pre-draft functions
def build_empty_draft_board(num_rounds, num_teams):
    """
    Constructs an empty draft board with snake draft order.
    Each cell contains team index, round, pick number, and placeholder for player.
    """
    board = []
    pick_counter = 1  # overall pick number

    for rnd in range(num_rounds):
        row = []
        if rnd % 2 == 0:
            team_order = range(num_teams)  # left to right
        else:
            team_order = reversed(range(num_teams))  # right to left

        for team in team_order:
            row.append({
                "team": team,
                "round": rnd + 1,
                "pick": pick_counter,
                "player": None
            })
            pick_counter += 1
        board.append(row)

    return board

def initialize_draft_teams(num_teams, user_team_index):
    teams = []
    for i in range(num_teams):
        teams.append({
            "team_index": i,
            "is_user": (i == user_team_index),
            "roster": [],
            "strategy": None,  # can add "zero_rb", "hero_rb", etc later
        })
    return teams   

def make_next_pick(session, players):
    draft_board = session["draft_board"]
    drafted_ids = session["drafted_ids"]
    draft_teams = session["draft_teams"]
    num_rounds = len(draft_board)
    picks_per_round = len(draft_teams)

    # Track overall pick number (0-based)
    current_pick_num = session.get("current_pick_num", 0)

    # ✅ End draft if no picks remain
    total_picks = num_rounds * picks_per_round
    if current_pick_num >= total_picks:
        return False

    # Locate current cell from flattened board
    current_round = current_pick_num // picks_per_round
    team_index_in_round = current_pick_num % picks_per_round
    cell = draft_board[current_round][team_index_in_round]
    team_index = cell["team"]
    team = draft_teams[team_index]

    # ✅ Stop for user pick
    if team["is_user"]:
        return False

    # 🧠 Auto-pick next available player
    for player in players:
        if player.id not in drafted_ids:
            drafted_player = player
            break
    else:
        return False  # no available players

    # 🎯 Assign player to cell
    cell["player"] = {
        "id": drafted_player.id,
        "name": drafted_player.player_name,
        "position": drafted_player.position.abbreviation,
        "team": drafted_player.team.team_name if drafted_player.team else "N/A",
    }

    team["roster"].append(drafted_player.id)
    drafted_ids.append(drafted_player.id)

    # 🔁 Advance pick number
    session["current_pick_num"] = current_pick_num + 1

    # 🔐 Save updated session state
    session["draft_board"] = draft_board
    session["draft_teams"] = draft_teams
    session["drafted_ids"] = drafted_ids

    return True
