from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt
from typing import Optional, Any, ClassVar
from direct.showbase.DirectObject import DirectObject
from engine.utils.event_handler import send_event


class StateType(Enum):
    SOFTWARE = auto()
    BUTTON = auto()
    JOYSTICK = auto()
    SWITCH = auto()
    LED = auto()


@dataclass
class GameState(DirectObject):
    engine: ClassVar
    default_value: Any
    state_type: StateType
    led_id: Optional[str] = None
    power: Optional[float] = None
    hardware_key: Optional[str] = None
    _value: Optional[Any] = None

    def __post_init__(self):
        self._value = self.default_value
        if self.state_type == StateType.LED:
            self.led_id = self.hardware_key
            self.hardware_key = None

        if self.hardware_key is not None:
            self.accept(self.hardware_key, self.set_value)

    @property
    def name(self) -> str:
        for attr_name in vars(GameStateManager):
            if getattr(GameStateManager, attr_name) is self:
                return attr_name
        raise KeyError()

    def reset(self) -> None:
        # special case if we are a switch
        if self.state_type == StateType.SWITCH:
            # in this case, the value set with "self.value = <xxx>"
            # is ignored, we simply set self._value -> not self._value
            # since we want self.default_value at the end, we need to
            # set self._value = not self.default_value here
            self._value = not self.default_value

        # this will trigger all updates in gui
        # together with power update, led on/off
        # and optional sounds
        self.set_value(self.default_value)

    def get_value(self) -> Any:
        return self._value

    def is_on(self) -> bool:
        return self._value in [True, 1, '1']

    def set_value(self, new_value: Any) -> None:
        # if we are a switch, we always receive "True"
        # so we need to reverse the value
        # "new_value" itself is ignored
        if self.state_type == StateType.SWITCH:
            new_value = not self._value
        self._value = new_value

        # on set True
        if self._value in [True, 1]:
            if self.led_id is not None:
                self.engine.hardware.set_led_on(self.led_id)
            # may play a sound
            self.engine.sound_manager.play_sfx(self.name + "_on")
            # self.engine.power.switch_on(self.name)
        elif self._value in [False, 0]:
            # switch off
            if self.led_id is not None:
                self.engine.hardware.set_led_off(self.led_id)
            # may play a sound
            self.engine.sound_manager.play_sfx(self.name + "_off")
            # self.engine.power.switch_off(self.name)

        # send event for gui
        send_event('update_state', key=self.name)

        # tell engine that state is changed
        self.engine.on_game_state_update()

        # and update scenario
        self.engine.scenario.update_scenario()


class GameStateManager:
    @classmethod
    def states(cls) -> dict:
        return {attr_name: getattr(cls, attr_name) for attr_name in vars(cls)
                if isinstance(getattr(cls, attr_name), GameState)}

    @classmethod
    def reset(cls):
        for item in cls.states().values():
            item.reset()

    # id, hardware_key, type, led_id, initial_value, power, defines_a_state, test_key
    crew_screen_unlocked = GameState(False, StateType.SOFTWARE)
    alert_screen_unlocked = GameState(False, StateType.SOFTWARE)
    target_screen_unlocked = GameState(False, StateType.SOFTWARE)
    collision_occurred = GameState(False, StateType.SOFTWARE)
    pilote_automatique_failed = GameState(False, StateType.SOFTWARE)
    listen_to_hardware = GameState(False, StateType.SOFTWARE)

    is_moving = GameState(False, StateType.SOFTWARE)
    freq_comm = GameState(270, StateType.SOFTWARE)
    offset_ps_x = GameState(0, StateType.SOFTWARE)
    offset_ps_y = GameState(0, StateType.SOFTWARE)
    main_power = GameState(100, StateType.SOFTWARE)
    main_O2 = GameState(100, StateType.SOFTWARE)
    main_CO2 = GameState(50, StateType.SOFTWARE)
    sp_power = GameState(10, StateType.SOFTWARE)
    sp_max_power = GameState(68.28, StateType.SOFTWARE)
    target_name = GameState('NT', StateType.SOFTWARE)
    pilote_automatique = GameState(True, StateType.SOFTWARE, led_id='21', power=-78.28)
    full_pilote_automatique = GameState(True, StateType.SOFTWARE)

    admin = GameState(False, StateType.BUTTON, hardware_key='joystick1-button6')
    freq_moins = GameState(False, StateType.BUTTON, hardware_key='joystick1-button4')
    freq_plus = GameState(False, StateType.BUTTON, hardware_key='joystick1-button3')

    copilote_h = GameState(False, StateType.JOYSTICK)
    copilote_v = GameState(False, StateType.JOYSTICK)
    pilote_h = GameState(False, StateType.JOYSTICK)
    sp_orientation_h = GameState(False, StateType.JOYSTICK, hardware_key='joystick2-axis0')
    sp_orientation_v = GameState(False, StateType.JOYSTICK, hardware_key='joystick2-axis1')

    problem0 = GameState(False, StateType.LED, hardware_key='0')
    problem1 = GameState(False, StateType.LED, hardware_key='1')
    problem2 = GameState(False, StateType.LED, hardware_key='2')
    ps_nominal = GameState(True, StateType.LED, hardware_key='31')
    defficience_moteur1 = GameState(False, StateType.LED, hardware_key='14')
    defficience_moteur2 = GameState(False, StateType.LED, hardware_key='13')
    defficience_moteur3 = GameState(False, StateType.LED, hardware_key='10')
    main_O2_up = GameState(False, StateType.LED, hardware_key='23')
    main_O2_down = GameState(False, StateType.LED, hardware_key='26')
    main_O2_low = GameState(False, StateType.LED, hardware_key='29')
    main_power_up = GameState(False, StateType.LED, hardware_key='24')
    main_power_down = GameState(False, StateType.LED, hardware_key='27')
    main_power_low = GameState(False, StateType.LED, hardware_key='30')
    main_CO2_up = GameState(False, StateType.LED, hardware_key='22')
    main_CO2_down = GameState(False, StateType.LED, hardware_key='25')
    main_CO2_high = GameState(False, StateType.LED, hardware_key='28')
    antenne_com = GameState(False, StateType.LED, hardware_key='32')
    surpression1 = GameState(False, StateType.LED)
    surpression2 = GameState(False, StateType.LED)
    surpression3 = GameState(False, StateType.LED)
    fuite_O2 = GameState(False, StateType.LED, hardware_key='6')
    fuite_CO2 = GameState(False, StateType.LED, hardware_key='3')
    alert0 = GameState(False, StateType.LED, hardware_key='54')
    alert1 = GameState(False, StateType.LED, hardware_key='55')
    acceleration = GameState(False, StateType.LED)

    batterie1 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button0', led_id='33', power=20)
    batterie2 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button1', led_id='34', power=20)
    batterie3 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button2', led_id='35', power=20)
    batterie4 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button9', led_id='36', power=20)
    batteries = GameState(True, StateType.SWITCH, hardware_key='joystick0-button3', power=5)

    correction_direction = GameState(True, StateType.SWITCH, hardware_key='joystick1-button1', led_id='19')
    correction_roulis = GameState(True, StateType.SWITCH, hardware_key='joystick1-button2', led_id='18')
    correction_stabilisation = GameState(True, StateType.SWITCH, hardware_key='joystick1-button0', led_id='20')

    moteur1 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button6', led_id='17', power=100)
    moteur2 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button7', led_id='15', power=100)
    moteur3 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button4', led_id='16', power=100)

    oxygen_secteur1 = GameState(True, StateType.SWITCH, hardware_key='joystick1-button8', led_id='37', power=-20)
    oxygen_secteur2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button0', led_id='38', power=-20)
    oxygen_secteur3 = GameState(True, StateType.SWITCH, hardware_key='joystick1-button9', led_id='39', power=-20)

    pilote_automatique1 = GameState(True, StateType.SWITCH, hardware_key='joystick0-button5')
    pilote_automatique2 = GameState(True, StateType.SWITCH, hardware_key='joystick1-button7')

    recyclage_CO2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button7', led_id='48', power=-20)
    recyclage_H2O = GameState(True, StateType.SWITCH, hardware_key='joystick2-button8', led_id='47', power=-20)
    recyclage_O2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button9', led_id='46', power=-20)

    tension_secteur1 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button1', led_id='40', power=-20)
    tension_secteur2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button2', led_id='41', power=-20)
    tension_secteur3 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button3', led_id='42', power=-20)

    thermique_secteur1 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button4', led_id='43', power=-20)
    thermique_secteur2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button5', led_id='44', power=-20)
    thermique_secteur3 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button6', led_id='45', power=-20)

    verrouillage_secteur1 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button6', led_id='4')
    verrouillage_secteur2 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button6', led_id='5')
    verrouillage_secteur3 = GameState(True, StateType.SWITCH, hardware_key='joystick2-button6', led_id='11')

    joystick_pilote = GameState(0, StateType.SWITCH, hardware_key='joystick0-button4')
    joystick_copilote = GameState(0, StateType.SWITCH, hardware_key='joystick1-button5')