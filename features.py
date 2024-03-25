from abc import ABC, abstractmethod
import json


class ParticipantFeature(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def calculate_value(self, participant):
        pass

    @abstractmethod
    def reset_class_values(self):
        pass


class Diff(ParticipantFeature):
    @abstractmethod
    def __init__(self):
        self.value = 0
        self.team_multiplier = 1

    @abstractmethod
    def calculate_value(self, participant):
        pass

    def calculate_team_multiplier(self, participant_id):
        if int(participant_id) > 5:
            self.team_multiplier = -1

    def reset_class_values(self):
        self.value = 0
        self.team_multiplier = 1


class GeneralStatDiff(Diff):
    def __init__(self, stat):
        super().__init__()
        self.stat = stat

    def calculate_value(self, participant):
        self.value += participant.get(self.stat) * self.team_multiplier


class TimelineChampionStatDiff(Diff):
    def __init__(self, stat):
        super().__init__()
        self.stat = stat

    def calculate_value(self, participant):
        self.value += participant['championStats'].get(self.stat) * self.team_multiplier


class TimelineDamageStatDiff(Diff):
    def __init__(self, stat):
        super().__init__()
        self.stat = stat

    def calculate_value(self, participant):
        self.value += participant['damageStats'].get(self.stat) * self.team_multiplier


class TimelineTotalCSDiff(Diff):
    def __init__(self):
        super().__init__()

    def calculate_value(self, participant):
        self.value += (participant.get('jungleMinionsKilled') +
                       participant.get('minionsKilled')) * self.team_multiplier


class LiveScoreDiff(Diff):
    def __init__(self, stat):
        super().__init__()
        self.stat = stat

    def calculate_value(self, participant):
        self.value += participant['scores'].get(self.stat) * self.team_multiplier


class LiveItemCostDiff(Diff):
    def __init__(self, item_data_path):
        super().__init__()

        with open(item_data_path, "r", encoding="utf-8") as f:
            self.item_data = json.load(f)

    def calculate_value(self, participant):
        total_item_cost = 0
        for item in participant["items"]:
            item_id = str(item['itemID'])
            total_item_cost += self.item_data['data'][item_id]['gold']['total']

        self.value += total_item_cost * self.team_multiplier


class FeatureManager(ABC):
    def __init__(self, features):
        self.frame = None
        self.features = features
        self.feature_values = []

    @abstractmethod
    def calculate_features_for_frame(self):
        pass

    def reset_feature_values(self):
        for feature in self.features:
            feature.reset_class_values()


class TimelineFeatureManager(FeatureManager):
    def calculate_features_for_frame(self):
        for participant_id, participant in self.frame['participantFrames'].items():
            for feature in self.features:
                feature.calculate_team_multiplier(participant_id)
                feature.calculate_value(participant)

        self.feature_values = [feature.value for feature in self.features]


class LiveFeatureManager(FeatureManager):
    def calculate_features_for_frame(self):
        for participant_id, participant in enumerate(self.frame['playerInfo']):
            for feature in self.features:
                feature.calculate_team_multiplier(participant_id)
                feature.calculate_value(participant)

        self.feature_values = [feature.value for feature in self.features]






