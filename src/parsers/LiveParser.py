from typing import Dict, List, Optional, Tuple
from src.parsers.LiveFrame import LiveEvent, LiveFrame, Player
from src.Sample import Sample
from src.features.features import (
    AlivePlayers,
    BuffRemaining,
    DragonKills,
    FeatureKeys,
    GameStat,
    GoldPercentage,
    PlayersWithActiveBuff,
    TeamStat,
    TimeStamp,
    TotalTeamLevel,
    TowerKills,
)


class LiveParser:
    """An implementation of the Parser interface that enables collection of 'Live' data.

    NOTE: this is meant for quick testing and isn't written in the most clean way.
    Later, a development flow should test using the browser.
    """

    _lastTimeStamp: int
    _lastEvents: List[LiveEvent]
    # 0 = Nope, 1= Team 1, 2= Team 2
    # Dragon info
    _dragonsTaken: Tuple[int, int]
    _dragonSoulTaken: int
    # Elder info
    _elderBuffDurationInMS: int
    _elderBuffTimeLeft: int
    _playerHasElder: List[bool]
    # Baron info
    _baronBuffDurationInMS: int
    _baronBuffTimeLeft: int
    _playerHasBaron: List[bool]
    _towersTaken: Tuple[int, int]

    def __init__(self) -> None:
        self.setDefaults()

    def setDefaults(self) -> None:
        self._lastTimeStamp = 0
        self._lastEvents = []
        self._dragonSoulTaken = 0
        self._baronBuffDurationInMS = 180000
        self._elderBuffDurationInMS = 150000
        self._baronBuffTimeLeft = 0
        self._elderBuffTimeLeft = 0
        self._playerHasBaron = [False] * 10
        self._playerHasElder = [False] * 10
        self._towersTaken = (0, 0)
        self._dragonsTaken = (0, 0)

    def getTotalGold(self, frame: LiveFrame) -> int:
        totalGold = 0
        for player in frame.players:
            total += player.getTotalItemsValue()
        return totalGold

    def getTeamFromPlayerName(self, name: str, players: List[Player]) -> str:
        team = None
        for player in players:
            if name == player.summonerName:
                team = player.team
                break
        assert team is not None
        return team

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

    def setElderBuffTimeLeft(self, elapsed: int):
        if elapsed < self._elderBuffTimeLeft:
            self._elderBuffTimeLeft -= elapsed
        else:
            self._elderBuffTimeLeft = 0
            self._playerHasElder = [False] * 10

    def setBaronBuffTimeLeft(self, elapsed: int):
        if elapsed < self._baronBuffDurationInMS:
            self._baronBuffTimeLeft -= elapsed
        else:
            self._baronBuffTimeLeft = 0
            self._playerHasBaron = [False] * 10

    def processTime(self, newTimeStamp: int):
        elapsed = newTimeStamp - self._lastTimeStamp
        if elapsed > 0:
            self.setBaronBuffTimeLeft(elapsed)
            self.setElderBuffTimeLeft(elapsed)

    def getOnlyNewEvents(self, currFrame: LiveFrame):
        newEvents: List[LiveEvent] = []
        for event in currFrame.events:
            if event not in self._lastEvents:
                newEvents.append(event)
        return newEvents

    def processBuildingKill(self, event: LiveEvent, players: List[Player]):
        killerTeam = self.getTeamFromPlayerName(event.killerName, players)  # type: ignore
        team1 = self._towersTaken[0] + int(killerTeam == "ORDER")
        team2 = self._towersTaken[1] + int(killerTeam == "CHAOS")
        self._towersTaken = (team1, team2)

    def processChampionKill(self, event: LiveEvent, players: List[Player]):
        playerIndex = -1
        for i, player in enumerate(players):
            if event.victimName == player.summonerName:
                playerIndex = i
                break
        assert playerIndex > -1
        self._playerHasBaron[playerIndex] = False
        self._playerHasElder[playerIndex] = False

    def processDragonKill(self, event: LiveEvent, currTime: int, players: List[Player]):
        elapsed = currTime - event.eventTime
        killerTeam = self.getTeamFromPlayerName(event.killerName, players)  # type: ignore
        if event.dragonType == "Elder":
            self._elderBuffTimeLeft = self._elderBuffDurationInMS - elapsed
            teamOffset = 0 if killerTeam == "ORDER" else 5
            for i in range(5):
                self._playerHasElder[i + teamOffset] = True
        else:
            team1 = self._dragonsTaken[0] + int(killerTeam == "ORDER")
            team2 = self._dragonsTaken[1] + int(killerTeam == "CHAOS")
            self._dragonsTaken = (team1, team2)
            if team1 >= 4 or team2 >= 4:
                self._dragonSoulTaken = 1 if killerTeam == "ORDER" else 2

    def processBaronKill(self, event: LiveEvent, currTime: int, players: List[Player]):
        elapsed = currTime - event.eventTime
        self._baronBuffTimeLeft = self._baronBuffDurationInMS - elapsed
        killerTeam = self.getTeamFromPlayerName(event.killerName, players)  # type: ignore
        teamOffset = 0 if killerTeam == "ORDER" else 5
        for i in range(5):
            self._playerHasBaron[i + teamOffset] = True

    # def processEliteMonsterKill(self, event: LiveEvent, currTime: int):
    #     elapsed = currTime - event.eventTime
    #     playerBuffStatus = []
    #     if event.monsterType == "BARON_NASHOR":
    #         self._baronBuffTimeLeft = self._baronBuffDurationInMS - elapsed
    #         playerBuffStatus = self._playerHasBaron
    #     elif event.monsterType == "DRAGON" and event.monsterSubType == "ELDER_DRAGON":
    #         self._elderBuffTimeLeft = self._edlerBuffDurationInMS - elapsed
    #         playerBuffStatus = self._playerHasElder
    #     elif event.monsterType == "DRAGON":
    #         team1 = self._dragonsTaken[0] + int(event.killerTeamId == 100)
    #         team2 = self._dragonsTaken[1] + int(event.killerTeamId == 200)
    #         self._dragonsTaken = (team1, team2)
    #     else:
    #         # Could also be void grubs - not yet considered
    #         return

    #     teamOffset = 0 if event.killerTeamId == 100 else 5
    #     for player in range(1, 6):
    #         playerBuffStatus[player + teamOffset] = True

    # def processDragonSoulGiven(self, event: Event):
    #     self._dragonSoulTaken = event.teamId // 100  # type: ignore

    def processEvents(self, frame: LiveFrame):
        newEvents = self.getOnlyNewEvents(currFrame=frame)
        for event in newEvents:
            if event.eventName == "TurretKilled":
                self.processBuildingKill(event, frame.players)
            elif event.eventName == "ChampionKill":
                self.processChampionKill(event, frame.players)
            elif event.eventName == "DragonKill":
                self.processDragonKill(event, frame.timestamp, frame.players)
            elif event.eventName == "BaronKill":
                self.processBaronKill(event, frame.timestamp, frame.players)
            else:
                # noop - we don't care about the other events (for now)
                pass

    def getNextFrame(self, currFrame: LiveFrame) -> Optional[Sample]:
        self.processTime(currFrame.timestamp)

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
        for player in range(5):
            enemyPlayer = player + 5
            playerGoldTeam1 = currFrame.players[player].getTotalItemsValue()
            playerGoldTeam2 = currFrame.players[enemyPlayer].getTotalItemsValue()
            goldPercentages += [
                GoldPercentage(
                    totalGold,
                    playerGoldTeam1,
                    playerGoldTeam2,
                )
            ]
            totalLevelTeam1 += currFrame.players[player].level
            totalLevelTeam2 += currFrame.players[enemyPlayer].level
            totalPlayersAliveTeam1 += currFrame.players[player].isDead
            totalPlayersAliveTeam2 += currFrame.players[enemyPlayer].isDead
            numOfPlayersWithBaronTeam1 += self._playerHasBaron[player]
            numOfPlayersWithBaronTeam2 += self._playerHasBaron[enemyPlayer]
            numOfPlayersWithElderTeam1 += self._playerHasElder[player]
            numOfPlayersWithElderTeam2 += self._playerHasElder[enemyPlayer]

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
        self._lastEvents = currFrame.events
        self._lastTimeStamp = currFrame.timestamp
        return Sample(gameFeatures, teamFeatures)
        # Maybe later...
        # - Inhibitor timers (how long until an inhibitor respawns) for each inhibitor
