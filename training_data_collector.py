from riotwatcher import LolWatcher, ApiError
from random import choice, randint
from pathlib import Path
import json

API_KEY = 'RGAPI-6e6ac8e6-63c0-4d2d-adab-61b1bb68ec5f'  # FOR TESTING ONLY, REMOVE LATER


def fetch_random_match_id(lol_watcher, region, queue, rank, division, page):
    rank_summoners = lol_watcher.league.entries(region=region, queue=queue, tier=rank, division=division, page=page)
    summoner = choice(rank_summoners)
    summoner_id = summoner['summonerId']

    summoner_info = lol_watcher.summoner.by_id(region=region, encrypted_summoner_id=summoner_id)
    summoner_puuid = summoner_info['puuid']

    summoner_matches = lol_watcher.match.matchlist_by_puuid(region=region, puuid=summoner_puuid, queue=420)
    return choice(summoner_matches)


def fetch_match_info(lol_watcher, region, match_id):
    return lol_watcher.match.by_id(region=region, match_id=match_id)


def fetch_match_timeline(lol_watcher, region, match_id):
    return lol_watcher.match.timeline_by_match(region=region, match_id=match_id)


def generate_data(region, queue, ranks, divisions, min_page,
                  max_page, num_samples, match_info_filepath, match_timeline_filepath):

    lol_watcher = LolWatcher(API_KEY)

    for rank in ranks:
        for div in divisions:
            for i in range(num_samples):
                try:
                    match_id = fetch_random_match_id(lol_watcher, region, queue, rank, div, randint(min_page, max_page))
                    match_info = fetch_match_info(lol_watcher, region, match_id)
                    match_timeline = fetch_match_timeline(lol_watcher, region, match_id)

                    match_info_filepath = match_info_filepath / ('_' + match_id + '.json')
                    match_timeline_filepath = match_timeline_filepath / ('_' + match_id + '.json')

                    with match_info_filepath.open(mode='w', encoding='utf-8') as match_info_f:
                        json.dump(match_info, match_info_f, ensure_ascii=False, indent=4)

                    with match_timeline_filepath.open(mode='w', encoding='utf-8') as match_timeline_f:
                        json.dump(match_timeline, match_timeline_f, ensure_ascii=False, indent=4)
                except ApiError as err:
                    if err.response.status_code == 404:
                        pass


def main():
    region = 'NA1'
    queue = 'RANKED_SOLO_5x5'
    non_apex_ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND']
    divisions = ['I', 'II', 'III', 'IV']

    min_page = 1
    max_page = 10
    num_samples_per_rank = 20

    match_info_filepath = Path.cwd() / 'matches' / 'match_info'
    match_timeline_filepath = Path.cwd() / 'matches' / 'match_timeline'

    generate_data(region, queue, non_apex_ranks, divisions,
                  min_page, max_page, num_samples_per_rank, match_info_filepath, match_timeline_filepath)


if __name__ == "__main__":
    main()
