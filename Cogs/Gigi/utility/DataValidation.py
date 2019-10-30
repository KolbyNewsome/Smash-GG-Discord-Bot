# DATA VALIDATION
def tourny_validate_data(data):
    if "tournament" not in data["data"] or data["data"]["tournament"] is None:
        return "Tournament does not exist."
    elif data["data"]["tournament"]["participants"]["nodes"] is None:
        return "Player is not registered in this tournament."
    else:
        return "Valid"

def player_sets_validate_data(data):
    if "tournament" not in data["data"] or data["data"]["tournament"] is None:
        return "Tournament does not exist."
    else:
        return "Valid"

def stream_queue_validate_data(data):
    if "tournament" not in data["data"] or data["data"]["tournament"] is None:
        return "Tournament does not exist."
    elif "streamQueue" not in data["data"]["tournament"] or data["data"]["tournament"]["streamQueue"] is None:
        return "Stream Queue for this tournament is empty."
    else:
        return "Valid"

def recent_sets_validate_data(data):
    if "player" not in data["data"] or data["data"]["player"] is None:
        return "Player does not exist."
    elif data["data"]["player"]["recentSets"] is None:
        return "Player has no recent sets logged."
    else:
        return "Valid"

def tourny_streams_validate_data(data):
    if "tournament" not in data["data"] or data["data"]["tournament"] is None:
        return "Tournament does not exist."
    elif data["data"]["tournament"]["streams"] is None:
        return "Tournament has no streams listed on Smash.gg. :pensive:"
    else:
        return "Valid"