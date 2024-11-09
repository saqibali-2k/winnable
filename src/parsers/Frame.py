from typing import List, Optional, Dict


class Position:
    """Position of player"""

    x: int
    y: int

    def __init__(self, data: dict):
        self.x = data["x"]
        self.y = data["y"]


class ParticipantFrame:
    """Information about a player"""

    participantId: int
    position: Optional[Position]
    currentGold: int
    totalGold: int
    level: int
    xp: int
    minionsKilled: int
    jungleMinionsKilled: int

    def __init__(self, data: dict):
        self.participantId = data["participantId"]
        self.position = Position(data["position"]) if "position" in data else None
        self.currentGold = data["currentGold"]
        self.totalGold = data["totalGold"]
        self.level = data["level"]
        self.xp = data["xp"]
        self.minionsKilled = data["minionsKilled"]
        self.jungleMinionsKilled = data["jungleMinionsKilled"]


class Event:
    """An event that occurred during the game"""

    type: str
    timestamp: int
    buildingType: Optional[str]
    monsterType: Optional[str]
    monsterSubType: Optional[str]
    position: Optional[Position]
    killerId: Optional[int]
    killerTeamId: Optional[int]
    teamId: Optional[int]
    victimId: Optional[int]
    assistingParticipantIds: List[int]
    wardType: Optional[str]
    creatorId: Optional[int]

    def __init__(self, data: dict):
        self.type = data["type"]
        self.timestamp = data["timestamp"]
        self.position = Position(data["position"]) if "position" in data else None
        self.killerId = data.get("killerId")
        self.killerTeamId = data.get("killerTeamId")
        self.teamId = data.get("teamId")
        self.victimId = data.get("victimId")
        self.assistingParticipantIds = data.get("assistingParticipantIds", [])
        self.wardType = data.get("wardType")
        self.creatorId = data.get("creatorId")
        self.buildingType = data.get("buildingType")
        self.monsterType = data.get("monsterType")
        self.monsterSubType = data.get("monsterSubType")


class Frame:
    """A frame that represents the state of the game and
    the events that occurred from the last frame"""

    timestamp: int
    participantFrames: Dict[str, ParticipantFrame]
    events: List[Event]

    def __init__(self, data: dict):
        self.timestamp = data["timestamp"]

        # Initialize participantFrames as a dictionary of ParticipantFrame objects
        self.participantFrames = {
            pid: ParticipantFrame(frame_data)
            for pid, frame_data in data["participantFrames"].items()
        }

        # Initialize events as a list of Event objects
        self.events = [Event(event_data) for event_data in data["events"]]
