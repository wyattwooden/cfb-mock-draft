# test.py
# test.py

def my_players_roster(qb, rb, wr, te, flex, k, dst, bench, my_team):
    roster_spots = qb + rb + wr + te + flex + k + dst + bench
    sorted_team = [None] * roster_spots

    # Count how many starters we can have
    position_slots = {
        'QB': qb,
        'RB': rb,
        'WR': wr,
        'TE': te,
        'FLEX': flex,
        'K': k,
        'DST': dst,
        'BENCH': bench
    }

    flex_eligible = {'RB', 'WR', 'TE'}
    slot_order = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DST', 'BENCH']
    slot_ranges = {}
    start = 0
    for pos in slot_order:
        count = position_slots[pos]
        slot_ranges[pos] = list(range(start, start + count))
        start += count

    filled_slots = set()

    for player in my_team:
        placed = False
        pos = player['position'].upper()

        # Try to place in main position slots
        for i in slot_ranges.get(pos, []):
            if sorted_team[i] is None:
                sorted_team[i] = player
                filled_slots.add(i)
                placed = True
                break

        # Try flex
        if not placed and pos in flex_eligible:
            for i in slot_ranges['FLEX']:
                if sorted_team[i] is None:
                    sorted_team[i] = player
                    filled_slots.add(i)
                    placed = True
                    break

        # Otherwise bench
        if not placed:
            for i in slot_ranges['BENCH']:
                if sorted_team[i] is None:
                    sorted_team[i] = player
                    filled_slots.add(i)
                    break

    return sorted_team


# Hardcoded players to simulate draft picks
player_pool = [
    {"pick": 4, "name": "Marvin Harrison Jr.", "position": "WR", "team": "Ohio State", "player_id": 1004},
    {"pick": 2, "name": "Blake Corum", "position": "RB", "team": "Michigan", "player_id": 1002},
    {"pick": 3, "name": "Raheim Sanders", "position": "RB", "team": "Arkansas", "player_id": 1003},
    {"pick": 1, "name": "Caleb Williams", "position": "QB", "team": "USC", "player_id": 1001},
    
    
    
    {"pick": 5, "name": "Rome Odunze", "position": "WR", "team": "Washington", "player_id": 1005},
    {"pick": 6, "name": "Trey Benson", "position": "RB", "team": "Florida State", "player_id": 1006},  # Flex
    {"pick": 7, "name": "Will Reichard", "position": "K", "team": "Alabama", "player_id": 1007},
    {"pick": 8, "name": "Georgia Defense", "position": "DST", "team": "Georgia", "player_id": 1008},

    # Bench
    {"pick": 9,  "name": "Drake Maye", "position": "QB", "team": "North Carolina", "player_id": 1009},
    {"pick": 10, "name": "Nicholas Singleton", "position": "RB", "team": "Penn State", "player_id": 1010},
    {"pick": 11, "name": "Emeka Egbuka", "position": "WR", "team": "Ohio State", "player_id": 1011},
    {"pick": 12, "name": "Xavier Worthy", "position": "WR", "team": "Texas", "player_id": 1012},
    {"pick": 13, "name": "Brock Bowers", "position": "TE", "team": "Georgia", "player_id": 1013},
    {"pick": 14, "name": "Jordan Travis", "position": "QB", "team": "Florida State", "player_id": 1014},
]

# Roster settings
qb, rb, wr, te, flex, k, dst, bench = 1, 2, 2, 1, 1, 1, 1, 6
my_team = []

# Simulate draft
for pick in player_pool:
    my_team.append(pick)
    sorted_roster = my_players_roster(qb, rb, wr, te, flex, k, dst, bench, my_team)

    print(f"\n✅ Drafted: {pick['name']} ({pick['position']} - {pick['team']})")

    print("📋 Current Roster:")
    for i, player in enumerate(sorted_roster):
        if player:
            print(f"  Slot {i + 1}: {player['name']} ({player['position']} - {player['team']})")
        else:
            print(f"  Slot {i + 1}: [EMPTY]")

