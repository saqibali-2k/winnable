from typing import Dict, List, Literal, Optional, Tuple
from src.parsers.LiveFrame import LiveEvent, LiveFrame, Player
from src.parsers.Sample import Sample
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

positionToIndex = {
    "TOP": 0,
    "JUNGLE": 1,
    "MIDDLE": 2,
    "BOTTOM": 3,
    "UTILITY": 4,  # OMEGALUL
}


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

    _flipTeam: bool

    def __init__(self, flipTeam=False) -> None:
        self._flipTeam = flipTeam
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
            totalGold += player.getTotalItemsValue()
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

    def processBuildingKill(self, event: LiveEvent):
        teamOfTurret = getTeamFromTurretName(event.turretKilled)  # type: ignore
        team1 = self._towersTaken[0] + int(teamOfTurret == "CHAOS")
        team2 = self._towersTaken[1] + int(teamOfTurret == "ORDER")
        self._towersTaken = (team1, team2)

    def processChampionKill(self, event: LiveEvent, players: List[Player]):
        playerIndex = -1
        for i, player in enumerate(players):
            if (
                event.victimName == player.summonerName
                or event.victimName == player.riotIdGameName
            ):
                playerIndex = i
                break
        assert playerIndex > -1
        self._playerHasBaron[playerIndex] = False
        self._playerHasElder[playerIndex] = False

    def processDragonKill(self, event: LiveEvent, currTime: int, players: List[Player]):
        elapsed = currTime - event.eventTime
        killerTeam = getTeamFromPlayerName(event.killerName, players)  # type: ignore
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
        killerTeam = getTeamFromPlayerName(event.killerName, players)  # type: ignore
        teamOffset = 0 if killerTeam == "ORDER" else 5
        for i in range(5):
            self._playerHasBaron[i + teamOffset] = True

    def processEvents(self, frame: LiveFrame):
        newEvents = self.getOnlyNewEvents(currFrame=frame)
        for event in newEvents:
            if event.eventName == "TurretKilled":
                self.processBuildingKill(event)
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
        goldPercentages: List[GoldPercentage] = [None] * 5  # type: ignore
        for player in getOrderPlayers(currFrame.players):
            playerIndex = positionToIndex[player.position]
            enemyPlayer = getPlayer("CHAOS", player.position, currFrame.players)
            enemyPlayerIndex = playerIndex + 5
            playerGoldTeam1 = player.getTotalItemsValue()
            playerGoldTeam2 = enemyPlayer.getTotalItemsValue()
            goldPercentages[playerIndex] = GoldPercentage(
                totalGold, playerGoldTeam1, playerGoldTeam2
            )
            totalLevelTeam1 += player.level
            totalLevelTeam2 += enemyPlayer.level
            totalPlayersAliveTeam1 += not player.isDead
            totalPlayersAliveTeam2 += not enemyPlayer.isDead
            numOfPlayersWithBaronTeam1 += self._playerHasBaron[playerIndex]
            numOfPlayersWithBaronTeam2 += self._playerHasBaron[enemyPlayerIndex]
            numOfPlayersWithElderTeam1 += self._playerHasElder[playerIndex]
            numOfPlayersWithElderTeam2 += self._playerHasElder[enemyPlayerIndex]

        # Tower kills
        towerKillsTeam1, towerKillsTeam2 = self._towersTaken
        # Dragon kills (whether a team has dragon soul or not)
        dragonsKilledTeam1, dragonsKillsTeam2 = self._dragonsTaken
        gameFeatures: Dict[FeatureKeys, GameStat] = {
            # FeatureKeys.TimeStamp: TimeStamp(timestamp=currFrame.timestamp),
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
        self._lastEvents = currFrame.events
        self._lastTimeStamp = currFrame.timestamp
        return Sample(gameFeatures, teamFeatures, self._flipTeam, debug=True)
        # Maybe later...
        # - Inhibitor timers (how long until an inhibitor respawns) for each inhibitor


def getOrderPlayers(players: List[Player]) -> List[Player]:
    orderPlayers = []
    for player in players:
        if player.team == "ORDER":
            orderPlayers += [player]
    assert len(orderPlayers) == 5
    return orderPlayers


def getPlayer(
    team: Literal["ORDER", "CHAOS"], position: str, players: List[Player]
) -> Player:
    for player in players:
        if player.team == team and player.position == position:
            return player
    assert False


team1TurretPrefix = "Turret_T1"
team2TurretPrefix = "Turret_T2"


def getTeamFromTurretName(turretName: str):
    if turretName.startswith(team1TurretPrefix):
        return "ORDER"
    elif turretName.startswith(team2TurretPrefix):
        return "CHAOS"
    assert False


def getTeamFromPlayerName(name: str, players: List[Player]) -> str:
    for player in players:
        if name == player.summonerName or name == player.riotIdGameName:
            return player.team
    assert False
