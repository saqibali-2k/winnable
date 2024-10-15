from enum import Enum, unique
from typing import Dict, List, Union
import numpy as np
from src.features.features import FeatureKeys, GameStat, TeamStat


@unique
class SampleFormatting(Enum):
    """Formatting strategies for generating samples"""

    TAKE_DIFF = 0
    BY_TEAM = 1


class Sample:
    """A sample that represents the game state at a particular moment in the game.

    The features decide what data is relevant; however, Sample decides how to arrange
    this information to feed into the model.
    """

    teamValues: np.ndarray
    gameValues: np.ndarray

    def __init__(
        self,
        gameFeatures: Dict[FeatureKeys, GameStat],
        teamFeatures: Dict[FeatureKeys, TeamStat],
        flipTeam=False,
    ):
        team1Features: List[Union[float, int]] = []
        team2Features: List[Union[float, int]] = []
        gameValues: List[Union[float, int]] = []
        for key in FeatureKeys:
            if key in gameFeatures:
                gameValues += [gameFeatures[key].getValue()]
            else:
                team1, team2 = teamFeatures[key].getValue(flipTeam=flipTeam)
                team1Features += [team1]
                team2Features += [team2]
        self.teamValues = np.array([team1Features, team2Features])
        self.gameValues = np.array(gameValues)

    def getValue(self, strategy: SampleFormatting) -> np.ndarray:
        if strategy == SampleFormatting.BY_TEAM:
            return np.hstack(
                [np.vstack([self.gameValues, self.gameValues]), self.teamValues]
            )
        elif strategy == SampleFormatting.TAKE_DIFF:
            return np.hstack(
                [self.gameValues, self.teamValues[0] - self.teamValues[1]]
            ).reshape(1, -1)
        else:
            # Should be unreachable
            assert False
