import json
from pathlib import Path
from tslearn.utils import to_time_series_dataset
import features
import numpy as np


def generate_time_series_features(timeline, features_list):
    """Generate a multivariate time series with the given features as individual variables

    :param timeline: Dict containing the match timeline
    :param features_list: Iterable containing instances of ParticipantFeature or derived classes corresponding to
    features to be added to the time series
    :return: Time series as a 2D list, where columns correspond to feature observations (with the first column being
    the timestamp), and rows corresponding to the timestamp of the observations
    """
    time_series = []

    feature_manager = features.TimelineFeatureManager(features_list)

    for frame in timeline['info']['frames']:
        feature_manager.frame = frame
        feature_manager.calculate_features_for_frame()

        time_series_row = [frame['timestamp']] + feature_manager.feature_values
        time_series.append(time_series_row)

        feature_manager.reset_feature_values()

    return time_series


def generate_dataset_from_files(match_info_dir, match_timeline_dir, features_list):
    """Generate dataset of multivariate time series with labels, with the given features as variables

    :param match_info_dir: Path to the directory containing the match info JSON files
    :param match_timeline_dir: Path to the directory containing the match timeline JSON files
    :param features_list: Iterable containing instances of ParticipantFeature or derived classes corresponding to
    features to be added to the time series
    :return: Tuple (X, y), where X is a 3D numpy array with shape (number of time series, max length of the time series,
    dimension), and Y is a 1D list of labels
    """
    X = []
    y = []

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

    features_list = [features.TimelineTotalCSDiff(), features.GeneralStatDiff("totalGold"),
                     features.GeneralStatDiff("level")]

    X, y = generate_dataset_from_files(match_info_dir, match_timeline_dir, features_list)

    dataset_filepath = Path.cwd() / 'matches' / 'dataset' / 'dataset_good'
    dataset_labels_filepath = Path.cwd() / 'matches' / 'dataset' / 'dataset_labels_good'

    np.save(dataset_filepath, X)
    np.save(dataset_labels_filepath, y)


if __name__ == "__main__":
    main()
