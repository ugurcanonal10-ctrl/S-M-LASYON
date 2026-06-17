"""
Atlas Takimi - Base State Sinifi
Tum state'ler bu siniftan turetilir.
ROS2 Foxy / Ubuntu 20.04 uyumlu
"""

from enum import Enum, auto


class StateID(Enum):
    """FSM'deki tum state kimlikleri."""
    LANE_FOLLOW       = auto()
    RED_LIGHT         = auto()
    GREEN_LIGHT       = auto()
    SIGN_RESPONSE     = auto()
    STATIC_OBSTACLE   = auto()
    DYNAMIC_OBSTACLE  = auto()
    PASSENGER_PICKUP  = auto()
    PASSENGER_DROPOFF = auto()
    PARKING_SEARCH    = auto()
    PARKING_MANEUVER  = auto()
    EMERGENCY_STOP    = auto()
    MISSION_COMPLETE  = auto()


class BaseState:
    """
    Tum state'lerin ata sinifi.

    Her state su metotlari override eder:
        on_enter()            - state'e girildiginde bir kez calisir
        execute(context)      - her timer tick'te calisir
        on_exit()             - state'ten cikildiginde bir kez calisir
        check_transitions(context) -> StateID | None
                              - gecis kosulunu kontrol eder,
                                gecis yoksa None doner
    """

    def __init__(self, state_id: StateID, logger=None):
        self.state_id = state_id
        self.logger = logger

    def on_enter(self) -> None:
        if self.logger:
            self.logger.info(f'[FSM] ENTER -> {self.state_id.name}')

    def execute(self, context: dict) -> None:
        """Her tick'te calisir. context: paylasilan sensor verisi."""
        pass

    def on_exit(self) -> None:
        if self.logger:
            self.logger.info(f'[FSM] EXIT  <- {self.state_id.name}')

    def check_transitions(self, context: dict):
        """
        Gecis kosullarini kontrol eder.
        Gecis varsa StateID doner, yoksa None.
        """
        return None
