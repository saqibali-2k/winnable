from typing import List, Optional


class Item:
    """
    Represents an item held by a player.

    Attributes:
        itemID (int): The unique ID of the item.
        displayName (str): The display name of the item.
        itemCost (int): The cost of the item.
    """

    itemID: int
    displayName: str
    itemCost: int

    def __init__(self, data: dict, itemsInfo: dict):
        self.itemID = data["itemID"]
        self.displayName = data["displayName"]
        self.itemCost = itemsInfo[itemsInfo["data"][self.itemID]["gold"]["total"]]


class Rune:
    """
    Represents the runes equipped by a player.

    Attributes:
        keystone (int): The keystone rune ID.
        primaryPath (int): The primary rune path ID.
        secondaryPath (int): The secondary rune path ID.
    """

    keystone: int
    primaryPath: int
    secondaryPath: int

    def __init__(self, data: dict):
        self.keystone = data["keystone"]
        self.primaryPath = data["primaryPath"]
        self.secondaryPath = data["secondaryPath"]


class SummonerSpell:
    """
    Represents the summoner spells used by a player.

    Attributes:
        spell1Id (int): The ID of the first summoner spell.
        spell2Id (int): The ID of the second summoner spell.
    """

    spell1Id: int
    spell2Id: int

    def __init__(self, data: dict):
        self.spell1Id = data["spell1Id"]
        self.spell2Id = data["spell2Id"]


class Scores:
    """
    Represents the score statistics of a player.

    Attributes:
        assists (int): The number of assists.
        creepScore (int): The total creep score.
        deaths (int): The number of deaths.
        kills (int): The number of kills.
        wardScore (float): The ward score.
    """

    assists: int
    creepScore: int
    deaths: int
    kills: int
    wardScore: float

    def __init__(self, data: dict):
        self.assists = data["assists"]
        self.creepScore = data["creepScore"]
        self.deaths = data["deaths"]
        self.kills = data["kills"]
        self.wardScore = data["wardScore"]


class Player:
    """
    Represents a player in the game.

    Attributes:
        championName (str): The name of the champion the player is using.
        isBot (bool): Whether the player is a bot.
        isDead (bool): Whether the player is currently dead.
        items (List[Item]): A list of items the player currently holds.
        level (int): The current level of the player.
        position (Optional[str]): The position of the player on the map.
        rawChampionName (str): The raw internal name of the champion.
        respawnTimer (float): The time remaining until the player respawns.
        runes (Rune): The runes equipped by the player.
        scores (Scores): The score statistics of the player.
        skinID (int): The skin ID of the player's champion.
        summonerName (str): The player's summoner name.
        riotId (Optional[str]): The player's Riot ID, if available.
        riotIdGameName (Optional[str]): The game name portion of the Riot ID.
        riotIdTagLine (Optional[str]): The tagline portion of the Riot ID.
        summonerSpells (SummonerSpell): The summoner spells used by the player.
        team (str): The team the player is on (e.g., "ORDER" or "CHAOS").
    """

    championName: str
    isBot: bool
    isDead: bool
    items: List[Item]
    level: int
    position: Optional[str]
    rawChampionName: str
    respawnTimer: float
    runes: Rune
    scores: Scores
    skinID: int
    summonerName: str
    riotId: Optional[str]
    riotIdGameName: Optional[str]
    riotIdTagLine: Optional[str]
    summonerSpells: SummonerSpell
    team: str
    positionIndex: int

    def __init__(self, data: dict, itemsInfo: dict):
        self.championName = data["championName"]
        self.isBot = data["isBot"]
        self.isDead = data["isDead"]
        self.items = [Item(item_data, itemsInfo) for item_data in data["items"]]
        self.level = data["level"]
        self.position = data.get("position")
        self.rawChampionName = data["rawChampionName"]
        self.respawnTimer = data["respawnTimer"]
        self.runes = Rune(data["runes"])
        self.scores = Scores(data["scores"])
        self.skinID = data["skinID"]
        self.summonerName = data["summonerName"]
        self.riotId = data.get("riotId")
        self.riotIdGameName = data.get("riotIdGameName")
        self.riotIdTagLine = data.get("riotIdTagLine")
        self.summonerSpells = SummonerSpell(data["summonerSpells"])
        self.team = data["team"]

    def getTotalItemsValue(self):
        total = 0
        for item in self.items:
            total += item.itemCost
        return total


class LiveEvent:
    """
    Represents Live Event information.
    """

    eventName: str
    eventTime: int
    killerName: Optional[str]
    victimName: Optional[str]
    assisters: Optional[List[str]]
    dragonType: Optional[str]

    def __init__(self, data: dict):
        self.eventName = data["EventName"]
        self.eventTime = data["EventTime"]
        self.killerName = data.get("KillerName")
        self.victimName = data.get("VictimName")
        self.assisters = data.get("Assisters", [])
        self.dragonType = data.get("DragonType")

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, LiveEvent):
            return False
        return value.eventName == self.eventName and value.eventTime == self.eventTime


class LiveFrame:
    """
    Information about the current Live State
    """

    timestamp: int
    events: List[LiveEvent]
    players: List[Player]

    def __init__(
        self, timestamp: int, eventsData: dict, playersData: dict, itemsInfo: dict
    ):
        # Initialize the events list with Event objects
        self.timestamp = timestamp
        self.events = [LiveEvent(eventData) for eventData in eventsData]
        self.players = [Player(playerData, itemsInfo) for playerData in playersData]
