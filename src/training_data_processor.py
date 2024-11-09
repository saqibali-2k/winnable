import json
from pathlib import Path
from typing import List
import numpy as np
from tqdm import tqdm

from src.parsers.Sample import SampleFormatting
from src.parsers.OfflineParser import OfflineParser
from src.parsers.Frame import Frame

processed_dataset_dir = Path.cwd() / "matches" / "dataset"
DATASET_FILEPATH = processed_dataset_dir / "dataset_good.npy"
DATASET_LABELS_FILEPATH = processed_dataset_dir / "dataset_labels_good.npy"


def generate_time_series_features(timeline):
    """Generate a multivariate time series with the given features as individual variables

    :param timeline: Dict containing the match timeline
    :param features_list: Iterable containing instances of ParticipantFeature or derived classes corresponding to
    features to be added to the time series
    :return: Time series as a 2D list, where columns correspond to feature observations (with the first column being
    the timestamp), and rows corresponding to the timestamp of the observations
    """
    time_series = []
    frames: List[Frame] = [Frame(frame) for frame in timeline["info"]["frames"]]
    parser = OfflineParser(frames)
    sample = parser.getNextFrame()
    while sample:
        time_series += [sample.getValue(SampleFormatting.TAKE_DIFF)]
        sample = parser.getNextFrame()
    return time_series


def generate_dataset_from_files(
    match_info_dir: Path, match_timeline_dir: Path, time_series=True
):
    """Generate dataset of multivariate time series with labels, with the given features as variables

    :param match_info_dir: Path to the directory containing the match info JSON files
    :param match_timeline_dir: Path to the directory containing the match timeline JSON files
    :return: Tuple (X, y), where X is a 3D numpy array with shape (number of time series, max length of the time series,
    dimension), and Y is a 1D list of labels
    """
    X = []
    y = []

    for match_info_filepath in tqdm(match_info_dir.iterdir()):
        try:
            if match_info_filepath.is_file():
                with match_info_filepath.open(
                    mode="r", encoding="utf-8"
                ) as match_info_f:
                    match_info = json.load(match_info_f)

                match_id = match_info["metadata"]["matchId"]
                match_timeline_filepath = match_timeline_dir / (
                    "match_timeline_" + match_id + ".json"
                )

                with match_timeline_filepath.open(
                    mode="r", encoding="utf-8"
                ) as match_timeline_f:
                    match_timeline = json.load(match_timeline_f)

                sample = generate_time_series_features(match_timeline)
                sample_label = int(match_info["info"]["participants"][1]["win"])
                if not time_series:
                    X.extend(sample)
                    y.extend([sample_label] * len(sample))
                else:
                    X.append(sample)
                    y.append(sample_label)
        except IOError:
            pass
    return X, y


def main():
    match_info_dir = Path.cwd() / "matches" / "match_info"
    match_timeline_dir = Path.cwd() / "matches" / "match_timeline"

    X, y = generate_dataset_from_files(
        match_info_dir, match_timeline_dir, time_series=False
    )

    processed_dataset_dir.mkdir(parents=True, exist_ok=True)

    print(f"Number of Samples and labels {len(X)},{len(y)}")
    print(f"Shape of features: {X[0].shape}")
    np.save(DATASET_FILEPATH, X)
    np.save(DATASET_LABELS_FILEPATH, y)


if __name__ == "__main__":
    main()
