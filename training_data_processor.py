import json
from pathlib import Path
from tslearn.utils import to_time_series_dataset
import features
import numpy as np


def generate_time_series_features(timeline, features_list):
    time_series = []

    feature_manager = features.TimelineFeatureManager(features_list)

    for frame in timeline['info']['frames']:
        feature_manager.frame = frame
        feature_manager.calculate_features_for_frame()

        time_series_row = [frame['timestamp']] + feature_manager.feature_values
        time_series.append(time_series_row)

        feature_manager.reset_feature_values()

    return time_series


def generate_dataset_from_files(match_info_dir, match_timeline_dir):
    X = []
    y = []

    features_list = [features.TimelineTotalCSDiff(), features.GeneralStatDiff("totalGold"),
                     features.GeneralStatDiff("level")]

    for match_info_filepath in match_info_dir.iterdir():
        try:
            if match_info_filepath.is_file():
                with match_info_filepath.open(mode='r', encoding='utf-8') as match_info_f:
                    match_info = json.load(match_info_f)

                match_id = match_info['metadata']['matchId']
                match_timeline_filepath = match_timeline_dir / ("match_timeline_" + match_id + '.json')

                with match_timeline_filepath.open(mode='r', encoding='utf-8') as match_timeline_f:
                    match_timeline = json.load(match_timeline_f)

                sample = generate_time_series_features(match_timeline, features_list)
                X.append(sample)

                sample_label = int(match_info['info']['participants'][1]['win'])
                y.append(sample_label)
        except IOError:
            pass

    X = to_time_series_dataset(X)
    return X, y


def main():
    match_info_dir = Path.cwd() / 'matches' / 'match_info'
    match_timeline_dir = Path.cwd() / 'matches' / 'match_timeline'

    X, y = generate_dataset_from_files(match_info_dir, match_timeline_dir)

    dataset_filepath = Path.cwd() / 'matches' / 'dataset' / 'dataset_good'
    dataset_labels_filepath = Path.cwd() / 'matches' / 'dataset' / 'dataset_labels_good'

    np.save(dataset_filepath, X)
    np.save(dataset_labels_filepath, y)


if __name__ == "__main__":
    main()
