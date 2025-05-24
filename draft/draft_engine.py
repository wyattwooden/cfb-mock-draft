# draft/draft_engine.py
# file containing functions used for drafting

# pre-draft functions
def build_empty_draft_board(num_rounds, num_teams):
    """
    Constructs an empty draft board matrix: draft_board[round][team]
    Each cell contains basic pick metadata and a placeholder for the drafted player.
    """
    board = []
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
        board.append(row)
    return board

def run_auto_draft():
    """
    @param players: list of available players to draft
    @param settings: dict of settings (num_teams, draft_slot, rounds, etc?)
    """
    print("Inside of the run_auto_draft function")