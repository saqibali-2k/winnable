import json
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import schedule
from src.parsers.Sample import SampleFormatting
from src.parsers.LiveFrame import LiveFrame
from src.parsers.LiveParser import LiveParser
from src.utils import load_model

CERT_PATH = Path.cwd() / "matches" / "riotgames.pem"
ITEM_DATA_PATH = Path.cwd() / "datadragon" / "item.json"
load_dotenv()
HOST = "127.0.0.1" if os.getenv("ENV") != "DOCKER" else "host.docker.internal"


def collect_live_data(model):

    with open(ITEM_DATA_PATH, "r", encoding="utf-8") as f:
        itemsJson = json.load(f)

    # Starting loop to establish connection and get the first frame right at the start of the game
    team = ""
    while True:
        try:
            team = getPlayerTeam()
            break
        except requests.exceptions.ConnectionError:
            print(
                f"Could not establish a connection to the League of Legends Live Client Data API {HOST}. Retrying..."
            )
        except requests.exceptions.HTTPError:
            print("HTTP error. Retrying...")

    parser = LiveParser(team != "ORDER")
    schedule.every(10).seconds.do(
        add_current_frame_to_time_series,
        parser=parser,
        itemsJson=itemsJson,
        model=model,
    )

    # When the first connection has been made in the previous loop, create frames every minute
    while True:
        try:
            schedule.run_pending()
        except requests.exceptions.ConnectionError:
            print(
                "Could not establish a connection to the League of Legends Live Client Data API. Retrying..."
            )
        except requests.exceptions.HTTPError:
            print("HTTP error. Retrying...")


def getPlayerTeam():
    nameReq = requests.get(
        f"https://{HOST}:2999/liveclientdata/activeplayername", verify=False, timeout=10
    )
    playerListReq = requests.get(
        f"https://{HOST}:2999/liveclientdata/playerlist", verify=False, timeout=10
    )
    nameReq.raise_for_status()
    playerListReq.raise_for_status()
    name = nameReq.json()
    for player in playerListReq.json():
        if player["riotId"] == name:
            return player["team"]
    # Should always find player in playerList
    assert False


def add_current_frame_to_time_series(
    parser,
    itemsJson,
    model,
):
    response_game_info = requests.get(
        f"https://{HOST}:2999/liveclientdata/gamestats", verify=False, timeout=10
    )
    response_player_info = requests.get(
        f"https://{HOST}:2999/liveclientdata/playerlist", verify=False, timeout=10
    )
    response_event_info = requests.get(
        f"https://{HOST}:2999/liveclientdata/eventdata", verify=False, timeout=10
    )

    response_game_info.raise_for_status()
    response_player_info.raise_for_status()

    game_info = response_game_info.json()
    player_info = response_player_info.json()
    events_info = response_event_info.json()

    frame = LiveFrame(
        game_info["gameTime"],
        events_info,
        player_info,
        itemsJson,
    )

    sample = parser.getNextFrame(frame)
    obs = sample.getValue(SampleFormatting.TAKE_DIFF)
    print(model.predict_proba(obs)[0][1])


def get_prediction(frame, model):
    return model.predict_proba(frame)[1]


def main():
    model = load_model("./models/xgboost")
    collect_live_data(model)


if __name__ == "__main__":
    main()
