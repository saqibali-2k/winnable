from typing import Dict, List, Optional, Tuple
from src.parsers.Frame import Event, Frame
from src.parsers.ParserInterface import Parser
from src.Sample import Sample
from src.features.features import (
    AlivePlayers,
    BuffRemaining,
    DragonKills,
    FeatureKeys,
    GameStat,
    GoldPercentage,
    PlayersWithActiveBuff,
    TeamHasDragonSoul,
    TeamStat,
    TimeStamp,
    TotalTeamLevel,
    TowerKills,
)


class OfflineParser(Parser):
    """An implementation of the Parser interface that enables collection of 'offline' data.

    Parses data from the MATCHv5 endpoint and creates samples for training.
    """

    _lastTimeStamp: int
    # 0 = Nope, 1= Team 1, 2= Team 2
    _frames: List[Frame]
    _isPlayerAlive: List[bool]
    # Dragon info
    _dragonsTaken: Tuple[int, int]
    _dragonSoulTaken: int
    # Elder info
    _edlerBuffDurationInMS: int
    _elderBuffTimeLeft: int
    _playerHasElder: List[bool]
    # Baron info
    _baronBuffDurationInMS: int
    _baronBuffTimeLeft: int
    _playerHasBaron: List[bool]
    _towersTaken: Tuple[int, int]

    def __init__(self, frames: List[Frame]) -> None:
        self.setDefaults()
        self._frames = frames[::-1]

    def setDefaults(self) -> None:
        self._lastTimeStamp = 0
        self._dragonSoulTaken = 0
        self._baronBuffDurationInMS = 180000
        self._edlerBuffDurationInMS = 150000
        self._baronBuffTimeLeft = 0
        self._elderBuffTimeLeft = 0
        self._isPlayerAlive = [True] * 10
        self._playerHasBaron = [False] * 10
        self._playerHasElder = [False] * 10
        self._towersTaken = (0, 0)
        self._dragonsTaken = (0, 0)

    def getTotalGold(self, frame: Frame) -> int:
        totalGold = 0
        for pid in frame.participantFrames:
            totalGold += frame.participantFrames[pid].currentGold
        return totalGold

    def getBaronBuffDurationByTeam(self):
        team1HasBaron = True in self._playerHasBaron[:5]
        team1 = self._baronBuffTimeLeft if team1HasBaron else 0
        team2 = self._baronBuffTimeLeft if not team1HasBaron else 0
        return team1, team2

    def getElderBuffDurationByTeam(self):
        team1HasElder = True in self._playerHasElder[:5]
        team1 = self._elderBuffTimeLeft if team1HasElder else 0
        team2 = self._elderBuffTimeLeft if not team1HasElder else 0
        return team1, team2

    def resetIsPlayerAlive(self):
        self._isPlayerAlive = [True] * 10

    def setBaronBuffTimeLeft(self, elapsed: int):
        if self._baronBuffTimeLeft > 0 and elapsed < self._baronBuffTimeLeft:
            self._baronBuffTimeLeft -= elapsed
        else:
            self._baronBuffTimeLeft = 0
            self._playerHasBaron = [False] * 10

    def setElderBuffTimeLeft(self, elapsed: int):
        if self._elderBuffTimeLeft > 0 and elapsed < self._elderBuffTimeLeft:
            self._elderBuffTimeLeft -= elapsed
        else:
            self._elderBuffTimeLeft = 0
            self._playerHasElder = [False] * 10

    def processTime(self, newTimeStamp: int):
        elapsed = newTimeStamp - self._lastTimeStamp
        if elapsed > 0:
            self.setBaronBuffTimeLeft(elapsed)
            self.setElderBuffTimeLeft(elapsed)
            # Atleast one minute has passed on every update so respawn everyone
            self.resetIsPlayerAlive()

    def processBuildingKill(self, event: Event):
        if event.buildingType == "INHIBITOR_BUILDING":
            return
        # teamId indicates which team the tower belonged too
        # the number of towers destroyed by each team
        team1 = self._towersTaken[0] + int(event.teamId == 200)
        team2 = self._towersTaken[1] + int(event.teamId == 100)
        self._towersTaken = (team1, team2)

    def processChampionKill(self, event: Event):
        player = event.victimId - 1  # type: ignore
        self._isPlayerAlive[player] = False
        self._playerHasBaron[player] = False
        self._playerHasElder[player] = False

    def processEliteMonsterKill(self, event: Event, currTime: int):
        elapsed = currTime - event.timestamp
        playerBuffStatus = []
        if event.monsterType == "BARON_NASHOR":
            self._baronBuffTimeLeft = self._baronBuffDurationInMS - elapsed
            playerBuffStatus = self._playerHasBaron
        elif event.monsterType == "DRAGON" and event.monsterSubType == "ELDER_DRAGON":
            self._elderBuffTimeLeft = self._edlerBuffDurationInMS - elapsed
            playerBuffStatus = self._playerHasElder
        elif event.monsterType == "DRAGON":
            team1 = self._dragonsTaken[0] + int(event.killerTeamId == 100)
            team2 = self._dragonsTaken[1] + int(event.killerTeamId == 200)
            self._dragonsTaken = (team1, team2)
            return
        else:
            # Could also be void grubs - not yet considered
            return

        teamOffset = 0 if event.killerTeamId == 100 else 5
        for player in range(5):
            playerBuffStatus[player + teamOffset] = True

    def processDragonSoulGiven(self, event: Event):
        self._dragonSoulTaken = event.teamId // 100  # type: ignore

    def processEvents(self, frame: Frame):
        for event in frame.events:
            if event.type == "BUILDING_KILL":
                self.processBuildingKill(event)
            elif event.type == "CHAMPION_KILL":
                self.processChampionKill(event)
            elif event.type == "ELITE_MONSTER_KILL":
                self.processEliteMonsterKill(event, frame.timestamp)
            elif event.type == "DRAGON_SOUL_GIVEN":
                self.processDragonSoulGiven(event)
            else:
                # noop - we don't care about the other events (for now)
                pass

    def getNextFrame(self) -> Optional[Sample]:
        if not self._frames:
            return None
        currFrame = self._frames.pop()
        self.resetIsPlayerAlive()
        self.processTime(currFrame.timestamp)
        self.processEvents(currFrame)

        # Gold % (player gold / total gold in game)
        totalGold = self.getTotalGold(currFrame)
        # Total team Lvls
        totalLevelTeam1 = 0
        totalLevelTeam2 = 0
        # # of players alive
        totalPlayersAliveTeam1 = 0
        totalPlayersAliveTeam2 = 0
        # # of players with Baron active
        numOfPlayersWithBaronTeam1 = 0
        numOfPlayersWithBaronTeam2 = 0
        # # of players with Elder active
        numOfPlayersWithElderTeam1 = 0
        numOfPlayersWithElderTeam2 = 0
        goldPercentages: List[GoldPercentage] = []
        for player in range(1, 6):
            enemyPlayer = player + 5
            playerGoldTeam1 = currFrame.participantFrames[str(player)].totalGold
            playerGoldTeam2 = currFrame.participantFrames[str(enemyPlayer)].totalGold
            goldPercentages += [
                GoldPercentage(
                    totalGold,
                    playerGoldTeam1,
                    playerGoldTeam2,
                )
            ]
            totalLevelTeam1 += currFrame.participantFrames[str(player)].level
            totalLevelTeam2 += currFrame.participantFrames[str(enemyPlayer)].level
            totalPlayersAliveTeam1 += self._isPlayerAlive[player - 1]
            totalPlayersAliveTeam2 += self._isPlayerAlive[enemyPlayer - 1]
            numOfPlayersWithBaronTeam1 += int(self._playerHasBaron[player - 1])
            numOfPlayersWithBaronTeam2 += int(self._playerHasBaron[enemyPlayer - 1])
            numOfPlayersWithElderTeam1 += int(self._playerHasElder[player - 1])
            numOfPlayersWithElderTeam2 += int(self._playerHasElder[enemyPlayer - 1])

        # Tower kills
        towerKillsTeam1, towerKillsTeam2 = self._towersTaken
        # Dragon kills (whether a team has dragon soul or not)
        dragonsKilledTeam1, dragonsKillsTeam2 = self._dragonsTaken
        gameFeatures: Dict[FeatureKeys, GameStat] = {
            FeatureKeys.TimeStamp: TimeStamp(timestamp=currFrame.timestamp),
        }
        teamFeatures: Dict[FeatureKeys, TeamStat] = {
            FeatureKeys.GoldPercentageTop: goldPercentages[0],
            FeatureKeys.GoldPercentageJg: goldPercentages[1],
            FeatureKeys.GoldPercentageMid: goldPercentages[2],
            FeatureKeys.GoldPercentageBot: goldPercentages[3],
            FeatureKeys.GoldPercentageSup: goldPercentages[4],
            FeatureKeys.TotalTeamLevel: TotalTeamLevel(
                totalLevelTeam1, totalLevelTeam2
            ),
            FeatureKeys.AlivePlayers: AlivePlayers(
                totalPlayersAliveTeam1, totalPlayersAliveTeam2
            ),
            FeatureKeys.DragonSoul: TeamHasDragonSoul(
                self._dragonSoulTaken == 1, self._dragonSoulTaken == 2
            ),
            FeatureKeys.TowerKills: TowerKills(towerKillsTeam1, towerKillsTeam2),
            FeatureKeys.DragonKills: DragonKills(dragonsKilledTeam1, dragonsKillsTeam2),
            FeatureKeys.PlayersWithElderBuff: PlayersWithActiveBuff(
                numOfPlayersWithElderTeam1, numOfPlayersWithElderTeam2
            ),
            FeatureKeys.PlayersWithBaronBuff: PlayersWithActiveBuff(
                numOfPlayersWithBaronTeam1, numOfPlayersWithBaronTeam2
            ),
            FeatureKeys.BaronBuffRemaining: BuffRemaining(
                *self.getBaronBuffDurationByTeam()
            ),
            FeatureKeys.ElderBuffRemaining: BuffRemaining(
                *self.getElderBuffDurationByTeam()
            ),
        }
        self._lastTimeStamp = currFrame.timestamp
        return Sample(gameFeatures, teamFeatures)
        # Maybe later...
        # - Inhibitor timers (how long until an inhibitor respawns) for each inhibitor
