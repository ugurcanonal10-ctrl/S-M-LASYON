"""
Atlas Takimi - FSM Node v2
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32

from .states.base_state import StateID
from .states.lane_follow import LaneFollowState
from .states.red_light import RedLightState
from .states.green_light import GreenLightState
from .states.sign_response import SignResponseState
from .states.static_obstacle import StaticObstacleState
from .states.dynamic_obstacle import DynamicObstacleState
from .states.passenger_pickup import PassengerPickupState
from .states.passenger_dropoff import PassengerDropoffState
from .states.parking_search import ParkingSearchState
from .states.parking_maneuver import ParkingManeuverState
from .states.emergency_stop import EmergencyStopState
from .states.mission_complete import MissionCompleteState

TIMER_PERIOD_SEC = 0.1


class FSMNode(Node):

    def __init__(self):
        super().__init__('fsm_node')
        self.get_logger().info('[FSM] Node baslatiliyor...')

        self._ctx = {
            'traffic_light': 'none',
            'obstacle_type': 'none',
            'sign_detected': False,
            'sign_type': '',
            'distance_to_target': 999.0,
            'mission_event': '',
            'emergency': False,
            'dwa_result': '',
            'parking_spot_available': False,
            'parking_complete': False,
            'intersection_cleared': False,
        }

        self._terminal = False  # Son state'e ulasildiysa True

        log = self.get_logger()
        self._states = {
            StateID.LANE_FOLLOW:       LaneFollowState(log),
            StateID.RED_LIGHT:         RedLightState(log),
            StateID.GREEN_LIGHT:       GreenLightState(log),
            StateID.SIGN_RESPONSE:     SignResponseState(log),
            StateID.STATIC_OBSTACLE:   StaticObstacleState(log),
            StateID.DYNAMIC_OBSTACLE:  DynamicObstacleState(log),
            StateID.PASSENGER_PICKUP:  PassengerPickupState(log),
            StateID.PASSENGER_DROPOFF: PassengerDropoffState(log),
            StateID.PARKING_SEARCH:    ParkingSearchState(log),
            StateID.PARKING_MANEUVER:  ParkingManeuverState(log),
            StateID.EMERGENCY_STOP:    EmergencyStopState(log),
            StateID.MISSION_COMPLETE:  MissionCompleteState(log),
        }

        self._current_state = self._states[StateID.LANE_FOLLOW]
        self._current_state.on_enter()

        # Subscriber'lar
        self.create_subscription(String,  '/perception/traffic_light',
                                 self._cb_traffic_light, 10)
        self.create_subscription(String,  '/perception/obstacle',
                                 self._cb_obstacle, 10)
        self.create_subscription(String,  '/perception/sign',
                                 self._cb_sign, 10)
        self.create_subscription(Float32, '/localization/distance_to_target',
                                 self._cb_distance, 10)
        self.create_subscription(String,  '/mission/event',
                                 self._cb_mission_event, 10)
        self.create_subscription(Bool,    '/safety/emergency',
                                 self._cb_emergency, 10)
        self.create_subscription(String,  '/planning/dwa_result',
                                 self._cb_dwa_result, 10)
        self.create_subscription(Bool,    '/perception/parking_spot',
                                 self._cb_parking_spot, 10)
        self.create_subscription(Bool,    '/planning/parking_complete',
                                 self._cb_parking_complete, 10)
        self.create_subscription(Bool,    '/planning/intersection_cleared',
                                 self._cb_intersection_cleared, 10)

        # Publisher'lar
        self._pub_state = self.create_publisher(
            String, '/planning/current_state', 10)
        self._pub_cmd = self.create_publisher(
            String, '/planning/behavior_command', 10)

        self._timer = self.create_timer(TIMER_PERIOD_SEC, self._timer_cb)
        self.get_logger().info('[FSM] Hazir. Baslangic: LANE_FOLLOW')

    # ------------------------------------------------------------------ #
    #  Subscriber callback'ler                                            #
    # ------------------------------------------------------------------ #

    def _cb_traffic_light(self, msg: String):
        self._ctx['traffic_light'] = msg.data.lower()

    def _cb_obstacle(self, msg: String):
        self._ctx['obstacle_type'] = msg.data.lower()

    def _cb_sign(self, msg: String):
        data = msg.data.strip()
        self._ctx['sign_detected'] = len(data) > 0
        self._ctx['sign_type'] = data

    def _cb_distance(self, msg: Float32):
        self._ctx['distance_to_target'] = msg.data

    def _cb_mission_event(self, msg: String):
        self._ctx['mission_event'] = msg.data.lower()

    def _cb_emergency(self, msg: Bool):
        self._ctx['emergency'] = msg.data
        if msg.data and not self._terminal:
            self._transition_to(StateID.EMERGENCY_STOP)

    def _cb_dwa_result(self, msg: String):
        self._ctx['dwa_result'] = msg.data.lower()

    def _cb_parking_spot(self, msg: Bool):
        # Sadece PARKING_SEARCH state'indeyken isle
        if self._current_state.state_id == StateID.PARKING_SEARCH:
            self._ctx['parking_spot_available'] = msg.data

    def _cb_parking_complete(self, msg: Bool):
        # Sadece PARKING_MANEUVER state'indeyken isle
        if self._current_state.state_id == StateID.PARKING_MANEUVER:
            self._ctx['parking_complete'] = msg.data

    def _cb_intersection_cleared(self, msg: Bool):
        self._ctx['intersection_cleared'] = msg.data

    # ------------------------------------------------------------------ #
    #  Ana dongu                                                          #
    # ------------------------------------------------------------------ #

    def _timer_cb(self):
        # Terminal state'e ulasildiysa timer'i durdur
        if self._terminal:
            return

        self._current_state.execute(self._ctx)

        next_id = self._current_state.check_transitions(self._ctx)
        if next_id is not None:
            self._transition_to(next_id)

        self._publish_state()

    def _transition_to(self, next_id: StateID):
        if next_id == self._current_state.state_id:
            return

        self._current_state.on_exit()
        self._current_state = self._states[next_id]

        # Context'i temizle — eski sinyaller yeni state'i etkilemesin
        self._ctx['dwa_result'] = ''
        self._ctx['parking_spot_available'] = False
        self._ctx['parking_complete'] = False
        self._ctx['intersection_cleared'] = False
        self._ctx['sign_detected'] = False
        self._ctx['mission_event'] = ''

        self._current_state.on_enter()

        # Terminal state kontrolu
        if next_id in (StateID.EMERGENCY_STOP, StateID.MISSION_COMPLETE):
            self._terminal = True
            self._timer.cancel()
            self.get_logger().info(
                f'[FSM] Terminal state: {next_id.name} — timer durduruldu.')

        cmd = String()
        cmd.data = next_id.name
        self._pub_cmd.publish(cmd)

    def _publish_state(self):
        msg = String()
        msg.data = self._current_state.state_id.name
        self._pub_state.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = FSMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
