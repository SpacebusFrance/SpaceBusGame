from dataclasses import dataclass
from typing import Optional
import re

from engine.utils.global_utils import read_xml_args


@dataclass
class ScenarioStep:
    step_id: str
    end_conditions: Optional[dict] = None
    action: Optional[str] = None
    duration: Optional[float] = None
    delay: Optional[float] = None
    args_dict: Optional[dict] = None
    win_sounds: Optional[str] = None
    loose_sound: Optional[str] = None
    fulfill_if_lost: bool = False
    hint_sound: Optional[str] = None
    hint_time: Optional[float] = None


def _new_step(self, id, end_conditions=None, action=None, duration=None, delay=None, args_dict=None,
              win_sound=None, loose_sound=None, fulfill_if_lost=False, hint_sound=None, hint_time=None):
    if action is not None and len(action) > 0:
        # check some common end conditions
        if end_conditions is None and duration is None:
            if action == "control_screen_event":
                if args_dict.get("name", None) == "crew_lock_screen":
                    end_conditions = {"crew_screen_unlocked": True}
                elif args_dict.get("name", None) == "target_screen":
                    end_conditions = {"target_screen_unlocked": True}
            elif action == "info_text":
                end_conditions = {"info_text": False}
            elif action == "collision":
                end_conditions = {"alert_screen_unlocked": True}
            elif action in ["shuttle_goto", "shuttle_goto_station", "shuttle_look_at"]:
                end_conditions = {"is_moving": False}
            elif action == "play_sound":
                duration = self.engine.sound_manager.get_sound_length(args_dict.get("name", None)) + 1.0
            elif action in ["shuttle_stop", "led_off", "led_on", "restart", "start_game", "show_score",
                            "stop_sound", "sound_volume"]:
                duration = 0.0
            # elif action == 'end_game':

        if action == "info_text":
            if args_dict is None:
                args_dict = {}
            if "close_time" not in args_dict:
                args_dict["close_time"] = duration

        if delay is not None and delay > 0.0:
            if delay in self.pending_steps:
                Logger.error('there is already a step for game_time :', delay)
            self.pending_steps[delay] = Event(self.engine,
                                                   id=id,
                                                   action=action,
                                                   args_dict=args_dict,
                                                   )
        else:
            self.steps.append(Step(self.engine,
                                   end_conditions=end_conditions,
                                   action=action,
                                   max_time=duration,
                                   id=id,
                                   args_dict=args_dict,
                                   loose_sound=loose_sound,
                                   win_sound=win_sound,
                                   fulfill_if_lost=fulfill_if_lost,
                                   hint_sound=hint_sound,
                                   hint_time=hint_time
                                   ))


def reset(self):
    """
    Reset the game. Remove all running, tasks, stops the current step if is it playing and reset time.

    This does not clear steps.
    """
    if self.shuttle is None:
        self.shuttle = self.engine.shuttle

    # removing tasks
    self.remove_all_tasks()

    # stop steps
    try:
        self.steps[self.current_step].kill()
    except IndexError:
        pass

    self.current_step = 0
    Step.step_counter = 0
    self.game_time = None
    self.last_score = None


def read_scenario(engine, name: str) -> None:
    """
    Load the desired scenario. Creates all step from xml file

    Args:
        name (str): the name of the xml scenario to load
    """
    try:
        with open(engine("scenario_path") + name + ".xml", 'r', encoding="utf-8") as file:
            lines = file.readlines()

        # self.steps.clear()
        # self._scenario = name

        event_counter = 0

        # custom xml file parsing
        def_args = {"action": None, "duration": None, "game_time": None, "end_conditions": None, "args_dict": None,
                    "loose_sound": None, "win_sound": None, "fulfill_if_lost": False, "hint_sound": None,
                    "hint_time": None}
        current = def_args.copy()

        for line in lines:
            line = line.strip()
            # parse each line
            if not line.startswith('<!--') and len(line) > 0:
                # line is not a comment
                # read line kind defined as "<XXXX", can be 'group' or 'step' or 'event'
                kind = re.search(r'<\s*(\w*)\s', line).group(1) if re.search(r'<\s*(\w*)\s', line) is not None \
                    else None

                # all lines should start with "<" and end with ">", no multi-line supported
                assert line.startswith('<') and line.endswith('>'), f'Parsing error on line : "{line}"'

                # check if step or action
                if kind == 'step' and "action=" in line:
                    # read arguments
                    args = read_xml_args(line)
                    current["action"] = args.pop("action")
                    current["id"] = args.pop("id", f'step_{len(self.steps)}')
                    current["duration"] = args.pop("duration", None)
                    current["loose_sound"] = args.pop("loose_sound", None)
                    current["win_sound"] = args.pop("win_sound", None)
                    current["fulfill_if_lost"] = args.pop("fulfill_if_lost", False)
                    current["hint_sound"] = args.pop("hint_sound", None)
                    current["hint_time"] = args.pop("hint_time", None)
                    if 'game_time' in args:
                        # no game_time for steps
                        Logger.warning('game_time argument is ignored for steps !')
                    if len(args) > 0:
                        # store remaining arguments in args_dict argument
                        current["args_dict"] = args.copy()  # noqa
                    if "/>" in line:
                        # end of line, add a new step with current arguments
                        self._new_step(**current)
                        # and reset current arguments
                        current = def_args.copy()
                if kind == 'group':
                    # it is a group, we add it as an empty step
                    args = read_xml_args(line)
                    current["action"] = "group"  # noqa
                    current["id"] = args.pop("id", 'step_{}'.format(len(self.steps)))
                    current["duration"] = 0.0  # noqa
                    # idem, add a new step
                    self._new_step(**current)
                    # and reset arguments
                    current = def_args.copy()
                if "</step>" in line:
                    # enf od step, store a new one
                    self._new_step(**current)
                    # and reset current arguments
                    current = def_args.copy()
                if kind == 'event' and 'action=' in line:
                    # it is an event
                    args = read_xml_args(line)
                    # simply add a new step
                    self._new_step(action=args.pop("action"), delay=args.pop('game_time', 0.0),
                                   args_dict=args, id=args.pop("id", f'event_{event_counter}'))
                    # increment event counter
                    event_counter += 1
                elif "<condition" in line and "key" in line and "value" in line:
                    # a step condition with form <condition key="xxx" value="yyy"/>
                    args = read_xml_args(line)
                    if current['end_conditions'] is None:
                        current["end_conditions"] = dict()
                    current["end_conditions"][args.get("key", None)] = args.get("value", None)
    except FileNotFoundError:
        Logger.error('Error while loading file {}. It does not exists !'.format(name))