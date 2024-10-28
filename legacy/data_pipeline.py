from pathlib import Path
from random import randint
from dotenv import load_dotenv
import numpy as np
from riotwatcher import ApiError
from training_data_collector import fetch_random_match_id, fetch_match_timeline, fetch_match_info
from training_data_processor import generate_time_series_features
import features

processed_dataset_dir = Path.cwd() / 'matches' / 'dataset';
DATASET_FILEPATH = processed_dataset_dir / 'dataset_good.npy'
DATASET_LABELS_FILEPATH = processed_dataset_dir / 'dataset_labels_good.npy'

def generate_data(region, queue, ranks, divisions, min_page,
                  max_page, num_samples, feature_list, time_series=True):
    """Fetch num_samples number of match infos and match timelines for each combination of ranks and divisions, and extract
    features as specified in feature_list.

    :param region: String indicating match region
    :param queue: String indicating match queue type
    :param ranks: Iterable indicating all ranks to fetch matches from
    :param divisions: Iterable indicating all rank divisions to fetch matches from
    :param min_page: Lower bound (inclusive) on the range of pages to randomly choose matches from
    :param max_page: Upper bound (inclusive) on the range of pages to randomly choose matches from
    :param num_samples: Number of random matches to fetch from each combination of ranks and divisions
    :param feature_list: The features to extract from raw data for training set
    :return: None
    """
    X, y = [], []
    for rank in ranks:
        for div in divisions:
            for _ in range(num_samples):
                try:
                    # Get data from API
                    match_id = fetch_random_match_id(region, queue, rank, div, randint(min_page, max_page))
                    match_info = fetch_match_info(region, match_id)
                    match_timeline = fetch_match_timeline(region, match_id)

                    # Process features
                    sample = generate_time_series_features(match_timeline, feature_list)
                    sample_label = int(match_info['info']['participants'][1]['win'])
                    if not time_series:
                        X.extend(sample);
                        y.extend([sample_label] * len(sample))
                    else:
                        X.append(sample)           
                        y.append(sample_label)
                except ApiError as err:
                    if err.response.status_code == 404:
                        pass
    np.save(DATASET_FILEPATH, X)
    np.save(DATASET_LABELS_FILEPATH, y)
    return X,y

def main():
    region = 'NA1'
    queue = 'RANKED_SOLO_5x5'
    non_apex_ranks = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND']
    divisions = ['I', 'II', 'III', 'IV']

    min_page = 1
    max_page = 10
    num_samples_per_rank = 50

    features_list = [features.TimelineTotalCSDiff(), features.GeneralStatDiff("totalGold"),
                     features.GeneralStatDiff("level")]
    
    generate_data(region, queue, non_apex_ranks, divisions, min_page, max_page, num_samples_per_rank, features_list)

if __name__ == "__main__":
    main()
    
