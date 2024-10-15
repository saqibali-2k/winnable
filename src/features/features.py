from enum import Enum, auto, unique
from typing import Tuple, Union


class TeamStat:
    """A feature that has seperate value for each team"""

    team1: Union[float, int]
    team2: Union[float, int]

    def getValue(self, flipTeam=False) -> Tuple[Union[float, int], Union[float, int]]:
        if flipTeam:
            return (self.team2, self.team1)
        else:
            return (self.team1, self.team2)


class GameStat:
    """A feature that defines a value for the game so only one value is needed"""

    val: Union[float, int]

    def getValue(self) -> Union[float, int]:
        return self.val


class TimeStamp(GameStat):
    """Game time (the in-game time)"""

    def __init__(self, timestamp: int) -> None:
        super()
        self.val = timestamp


class GoldPercentage(TeamStat):
    """Gold % (player gold / total gold in game)"""

    def __init__(self, totalGold: int, player1Gold: int, player2Gold: int) -> None:
        super()
        self.team1 = player1Gold / max(totalGold, 1)
        self.team2 = player2Gold / max(totalGold, 1)


class TotalTeamLevel(TeamStat):
    """Total team XP"""

    def __init__(self, totalLevelTeam1: int, totalLevelTeam2: int) -> None:
        super()
        self.team1 = totalLevelTeam1
        self.team2 = totalLevelTeam2


class AlivePlayers(TeamStat):
    """Number of players alive"""

    def __init__(self, alivePlayersTeam1: int, alivePlayersTeam2: int) -> None:
        super()
        self.team1 = alivePlayersTeam1
        self.team2 = alivePlayersTeam2


class TowerKills(TeamStat):
    """Tower kills"""

    def __init__(self, towerKillsTeam1: int, towerKillsTeam2: int) -> None:
        super()
        self.team1 = towerKillsTeam1
        self.team2 = towerKillsTeam2


class DragonKills(TeamStat):
    """Dragon kills"""

    def __init__(self, dragonKillsTeam1: int, dragonKillsTeam2: int) -> None:
        super()
        self.team1 = dragonKillsTeam1
        self.team2 = dragonKillsTeam2


class TeamHasDragonSoul(TeamStat):
    """Whether a team has dragon soul or not"""

    def __init__(self, teamOneHasSoul: bool, teamTwoHasSoul: bool) -> None:
        super()
        self.team1 = int(teamOneHasSoul)
        self.team2 = int(teamTwoHasSoul)


class PlayersWithActiveBuff(TeamStat):
    """Number of players with an active buff (baron, elder)"""

    def __init__(
        self, playersWithActiveTeam1: int, playersWithActiveTeam2: int
    ) -> None:
        super()
        self.team1 = playersWithActiveTeam1
        self.team2 = playersWithActiveTeam2


class BuffRemaining(TeamStat):
    """Baron/Elder timers (time until buff expires for the team)"""

    def __init__(self, durationTeam1: int, durationTeam2: int) -> None:
        super()
        self.team1 = durationTeam1
        self.team2 = durationTeam2


# Maybe later ..
# - Herald trinket in Inventory
# - Inhibitor timers (how long until an inhibitor respawns) for each inhibitor


@unique
class FeatureKeys(Enum):
    """The feature keys of a feature map"""

    # auto will assign a unique value to each key
    TimeStamp = auto()
    GoldPercentageTop = auto()
    GoldPercentageJg = auto()
    GoldPercentageMid = auto()
    GoldPercentageBot = auto()
    GoldPercentageSup = auto()
    TotalTeamLevel = auto()
    AlivePlayers = auto()
    TowerKills = auto()
    DragonSoul = auto()
    DragonKills = auto()
    PlayersWithElderBuff = auto()
    ElderBuffRemaining = auto()
    PlayersWithBaronBuff = auto()
    BaronBuffRemaining = auto()
