from random import choice, randint
from pathlib import Path
import json
import os
from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv
from tqdm import tqdm


def fetch_random_match_id(lol_watcher: LolWatcher, region, queue, rank, division, page):
    """Fetch a random match ID based on the given parameters

    :param lol_watcher: LolWatcher instance
    :param region: String indicating match region
    :param queue: String indicating match queue type
    :param rank: String indicating match rank
    :param division: String indicating the division of the match rank
    :param page: Integer indicating the page number to fetch the match from
    :return: Random match ID
    """
    rank_summoners = lol_watcher.league.entries(
        region=region, queue=queue, tier=rank, division=division, page=page
    )
    summoner = choice(rank_summoners)  # type: ignore
    summoner_id = summoner["summonerId"]

    summoner_info = lol_watcher.summoner.by_id(
        region=region, encrypted_summoner_id=summoner_id
    )
    summoner_puuid = summoner_info["puuid"]  # type: ignore

    summoner_matches = lol_watcher.match.matchlist_by_puuid(
        region=region, puuid=summoner_puuid, queue=420
    )
    return choice(summoner_matches)  # type: ignore


def fetch_match_info(lol_watcher: LolWatcher, region, match_id):
    """Fetch match info from a given match ID

    :param lol_watcher: LolWatcher instance
    :param region: String indicating match region
    :param match_id: String indicating match ID
    :return:
    """
    return lol_watcher.match.by_id(region=region, match_id=match_id)


def fetch_match_timeline(lol_watcher: LolWatcher, region, match_id):
    """Fetch match timeline from a given match ID

    :param lol_watcher: LolWatcher instance
    :param region: String indicating match region
    :param match_id: String indicating match ID
    :return:
    """
    return lol_watcher.match.timeline_by_match(region=region, match_id=match_id)


def generate_data(
    lol_watcher: LolWatcher,
    region,
    queue,
    ranks,
    divisions,
    min_page,
    max_page,
    num_samples,
    match_info_dir,
    match_timeline_dir,
):
    """Fetch num_samples number of match infos and match timelines for each combination of ranks and divisions,
    saving each match info to a file named 'match_info_[ID].json' and each match timeline to a file named
    'match_timeline_[ID].json'.

    :param region: String indicating match region
    :param queue: String indicating match queue type
    :param ranks: Iterable indicating all ranks to fetch matches from
    :param divisions: Iterable indicating all rank divisions to fetch matches from
    :param min_page: Lower bound (inclusive) on the range of pages to randomly choose matches from
    :param max_page: Upper bound (inclusive) on the range of pages to randomly choose matches from
    :param num_samples: Number of random matches to fetch from each combination of ranks and divisions
    :param match_info_dir: Path to the directory to save the match info JSON files to
    :param match_timeline_dir: Path to the directory to save the match timeline JSON files to
    :return: None
    """

    for rank in ranks:
        for div in divisions:
            for _ in tqdm(range(num_samples), desc=f"{rank}+{div}"):
                try:
                    match_id = fetch_random_match_id(
                        lol_watcher,
                        region,
                        queue,
                        rank,
                        div,
                        randint(min_page, max_page),
                    )
                    match_info = fetch_match_info(lol_watcher, region, match_id)
                    match_timeline = fetch_match_timeline(lol_watcher, region, match_id)

                    match_info_filepath = match_info_dir / (
                        "match_info_" + match_id + ".json"
                    )
                    match_timeline_filepath = match_timeline_dir / (
                        "match_timeline_" + match_id + ".json"
                    )

                    with match_info_filepath.open(
                        mode="w", encoding="utf-8"
                    ) as match_info_f:
                        json.dump(
                            match_info, match_info_f, ensure_ascii=False, indent=4
                        )

                    with match_timeline_filepath.open(
                        mode="w", encoding="utf-8"
                    ) as match_timeline_f:
                        json.dump(
                            match_timeline,
                            match_timeline_f,
                            ensure_ascii=False,
                            indent=4,
                        )
                except ApiError as err:
                    if err.response.status_code == 404:
                        pass
                    else:
                        print("APIError: " + str(err.response.status_code))
                        return


def main():
    region = "NA1"
    queue = "RANKED_SOLO_5x5"
    non_apex_ranks = [
        # "IRON",
        # "BRONZE",
        # "SILVER",
        # "GOLD",
        # "PLATINUM",
        # "EMERALD",
        "DIAMOND",
    ]
    divisions = ["I", "II", "III", "IV"]

    min_page = 1
    max_page = 10
    num_samples_per_rank = 100

    match_info_dir = Path.cwd() / "matches" / "match_info"

    try:
        match_info_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print(
            "The specified path to the match info directory already \
                  exists exists and is not a directory."
        )

    match_timeline_dir = Path.cwd() / "matches" / "match_timeline"

    try:
        match_timeline_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print(
            "The specified path to the match timeline directory already \
                  exists and is not a directory."
        )

    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        print("Missing API Key in .env")
        return
    lol_watcher = LolWatcher(API_KEY)
    generate_data(
        lol_watcher,
        region,
        queue,
        non_apex_ranks,
        divisions,
        min_page,
        max_page,
        num_samples_per_rank,
        match_info_dir,
        match_timeline_dir,
    )


if __name__ == "__main__":
    main()
