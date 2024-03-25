import requests
from pathlib import Path
import schedule
import features
import math

CERT_PATH = Path.cwd() / 'matches' / 'riotgames.pem'
ITEM_DATA_PATH = Path.cwd() / 'datadragon' / 'item.json'


def collect_live_data():

    live_time_series = []

    features_list = [features.LiveScoreDiff('creepScore'),
                     features.LiveItemCostDiff(ITEM_DATA_PATH),
                     features.GeneralStatDiff('level')]

    # Starting loop to establish connection and get the first frame right at the start of the game
    while True:
        try:
            requests.get('https://127.0.0.1:2999/liveclientdata/activeplayername', verify=CERT_PATH)

            break
        except requests.exceptions.ConnectionError:
            print('Could not establish a connection to the League of Legends Live Client Data API. Retrying...')
        except requests.exceptions.HTTPError:
            print('HTTP error. Retrying...')

    schedule.every().minute.do(add_current_frame_to_time_series, features_list=features_list, time_series=live_time_series)
    live_time_series = add_current_frame_to_time_series(features_list, live_time_series)

    # When the first connection has been made in the previous loop, create frames every minute
    while True:
        try:
            schedule.run_pending()
        except requests.exceptions.ConnectionError:
            print('Could not establish a connection to the League of Legends Live Client Data API. Retrying...')
        except requests.exceptions.HTTPError:
            print('HTTP error. Retrying...')


def add_current_frame_to_time_series(features_list, time_series):
    response_game_info = requests.get('https://127.0.0.1:2999/liveclientdata/gamestats', verify=CERT_PATH)
    response_player_info = requests.get('https://127.0.0.1:2999/liveclientdata/playerlist', verify=CERT_PATH)

    response_game_info.raise_for_status()
    response_player_info.raise_for_status()

    game_info = response_game_info.json()
    player_info = response_player_info.json()

    frame = {'gameInfo': game_info, 'playerInfo': player_info}

    obs = observation_from_frame(frame, features_list)
    time_series.append(obs)

    print(time_series)

    return time_series


def observation_from_frame(frame, features_list):
    feature_manager = features.LiveFeatureManager(features_list)
    feature_manager.frame = frame
    feature_manager.calculate_features_for_frame()

    obs = [math.floor(frame['gameInfo']['gameTime'] * 60000)] + feature_manager.feature_values

    return obs


def main():
    collect_live_data()
