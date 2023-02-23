import datetime
import re
from panda3d.core import LVector3f, WindowProperties

from engine.scenario.scenario_event import Event
from engine.utils.event_handler import EventObject, event, send_event
from engine.utils.global_utils import read_xml_args
from engine.utils.logger import Logger
from engine.scenario.scenario_step import Step


class Scenario(EventObject):
    """
    The class that drives the scenario of the game. The scenario is divided in successive steps.
    Each step is defined as a certain number of conditions.
    Once these conditions are fulfilled, the scenario moves to the next step.
    """
    def __init__(self, game_engine):
        super().__init__()

        self.engine = game_engine
        self.shuttle = None
        self._scenario = None

        self.steps = []
        self.pending_steps = dict()
        self.current_step = 0
        Step.step_counter = 0
        self.game_time = None
        self.last_score = None

        self._paused_tasks = []

    def _new_step(self, id, end_conditions=None, action=None, duration=None, delay=None, args_dict=None,
                  win_sound=None, loose_sound=None, fulfill_if_lost=False, hint_sound=None, hint_time=None):

        if action is not None and len(action) > 0:
            # check some common end conditions
            if end_conditions is None and duration is None:
                if action == "collision":
                    end_conditions = {"alert_screen_unlocked": True}

                elif action in ["shuttle_goto", "shuttle_goto_station", "shuttle_look_at"]:
                    # stop step when shuttle reaches destination
                    end_conditions = {"is_moving": False}

                elif action == "play_sound":
                    # default duration o sound length + 1 second
                    duration = self.engine.sound_manager.get_sound_length(args_dict.get("name", None)) + 1.0

                elif action in ["shuttle_stop", "led_off", "led_on", "restart", "start_game", "show_score",
                                "stop_sound", "sound_volume", "update_software_state"]:
                    # these actions have a default duration to 0.0
                    duration = 0.0

            # if action == "info_text":
            #     if args_dict is None:
            #         args_dict = {}
            #     if "close_time" not in args_dict:
            #         args_dict["close_time"] = duration

            if delay is not None and delay > 0.0:
                if delay in self.pending_steps:
                    Logger.error('there is already a step for delay :', delay)
                # add an Event in delay seconds
                self.pending_steps[delay] = Event(
                    self.engine,
                    id=id,
                    action=action,
                    args_dict=args_dict,
                )
            else:
                # it is a standard blocking step
                self.steps.append(Step(
                    self.engine,
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

    def load_scenario(self, name: str) -> None:
        """
        Load the desired scenario. Creates all step from xml file

        Args:
            name (str): the name of the xml scenario to load
        """
        try:
            with open(self.engine("scenario_path") + name + ".xml", 'r', encoding="utf-8") as file:
                lines = file.readlines()

            self.steps.clear()
            self._scenario = name

            event_counter = 0

            # custom xml file parsing
            def_args = {"action": None, "duration": None, "delay": None, "end_conditions": None, "args_dict": None,
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
                    assert line.startswith('<') and line.endswith('>'), f'Multi-line detected on line : "{line}"'

                    # check if step or action
                    if kind == 'step' and "action=" in line:
                        # it has an action defined
                        # parse arguments
                        args = read_xml_args(line)
                        current["action"] = args.pop("action")
                        current["id"] = args.pop("id", f'step_{len(self.steps)}')
                        current["duration"] = args.pop("duration", None)
                        current["loose_sound"] = args.pop("loose_sound", None)
                        current["win_sound"] = args.pop("win_sound", None)
                        current["fulfill_if_lost"] = args.pop("fulfill_if_lost", False)
                        current["hint_sound"] = args.pop("hint_sound", None)
                        current["hint_time"] = args.pop("hint_time", None)

                        if 'delay' in args:
                            # no delay for steps
                            Logger.warning('delay argument is ignored for steps ! Use a wait step rather.')
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
                        current["action"] = "group" # noqa
                        current["id"] = args.pop("id", f'step_{len(self.steps)}')
                        current["duration"] = 0.0   # noqa
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
                        self._new_step(action=args.pop("action"), delay=args.pop('delay', 0.0),
                                       args_dict=args, id=args.pop("id", f'event_{event_counter}'))
                        # increment event counter
                        event_counter += 1

                    elif "<condition" in line and "key" in line and "value" in line:
                        # a step condition with form <condition key="xxx" value="yyy"/>
                        args = read_xml_args(line)
                        if current['end_conditions'] is None:
                            current["end_conditions"] = dict()  # noqa
                        current["end_conditions"][args.get("key", None)] = args.get("value", None)

        except FileNotFoundError:
            Logger.error('Error while loading file {}. It does not exists !'.format(name))

    def get_scenario(self) -> str:
        """
        Get the  name of the current scenario

        Returns:
            a :obj:`str`
        """
        return self._scenario

    def end_game(self, save_score=True, show_end_screen=True):
        """
        End the current game and write the score in the score file

        Args:
            save_score (bool):
            show_end_screen (bool): if ``True``, the end screen is displayed.
        """
        if self.game_time is not None:
            self.last_score = self.engine.get_time() - self.game_time
        else:
            self.last_score = self.engine.get_time()

        if save_score:
            # write scores, create file if it does not exist
            with open(f'{self.engine("score_folder")}scores_{self._scenario}.txt', 'a+') as file:
                file.write(f'{self.last_score}\n')

        if show_end_screen:            # format time
            hours, minutes, seconds = re.match(r'^(?P<hour>\d+):(?P<mins>\d+):(?P<seconds>\d+).*$',
                                               str(datetime.timedelta(seconds=self.last_score))).groups()
            try:
                with open(f'{self.engine("score_folder")}scores_{self._scenario}.txt', 'r') as f:
                    scores = list(map(float, f.readlines()))
                    position = len(list(filter(lambda x: x < self.last_score, scores)))
                    total = len(scores)
            except FileNotFoundError:
                position = 1
                total = 1
            self.engine.gui.end_screen(player_position=position,
                                       total_players=total,
                                       time_minutes=minutes,
                                       time_seconds=seconds)

    def start_game(self):
        """
        Starts the game. Stops the shuttle, reset the time and starts the first step
        """
        Logger.title('Starting new scenario')
        self.current_step = 0
        self.game_time = self.engine.get_time()
        self.shuttle.stop(play_sound=False)

        # start all pending steps
        for time in self.pending_steps:
            self.do_method_later(time,
                                 self.pending_steps[time].start,
                                 name='event_{}'.format(time))

        if len(self.steps) > 0:
            self.steps[0].start()

    @event(['reset_game', 'reset'])
    def on_reset(self):
        self.engine.reset_game()

    @event('restart')
    def on_restart(self):
        self.engine.reset_game(start=True)

    @event(['start_game', 'start'])
    def on_start(self):
        self.start_game()

    @event(['stop', 'stop_game'])
    def on_stop(self):
        self.steps[min(self.current_step, len(self.steps) - 1)].end(win=False)
        # this avoids to play next step
        self.current_step = len(self.steps)

        # remove all incoming events but keep steps
        self.remove_incoming_events()

    @event('goto_step')
    def on_goto(self, goto_id):
        # stop game
        self.steps[min(self.current_step, len(self.steps) - 1)].end(win=False)

        # remove all incoming events but keep steps
        self.remove_incoming_events()

        # goto next step
        self.current_step = None
        for i, step in enumerate(self.steps):
            if step.id == goto_id:
                # take i - 1 since will call "start_newt_step()" right after that
                self.current_step = i - 1
                break
        if self.current_step is None:
            raise KeyError(f'goto_id "{goto_id}" does not exist !')
        self.start_next_step()

    @event("end_game")
    def on_end_game(self, show_end_screen=True, save_score=True):
        # remove all incoming events
        self.remove_incoming_events()

        # call the end game
        self.end_game(show_end_screen=show_end_screen,
                      save_score=save_score)

    @event('collision_new')
    def on_collision_new(self):
        # The first impact function
        self.engine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
        self.engine.update_soft_state("collision_occurred", True)
        self.engine.sound_manager.stop_bips()

        self.engine.taskMgr.doMethodLater(0.5, self.engine.sound_manager.play_sfx, 'fi3',
                                          extraArgs=['gaz_leak', True, 0.5])
        self.engine.sound_manager.stop("start_music")

        # leds
        self.engine.hardware.set_led_on("l_defficience_moteur1")
        self.engine.hardware.set_led_on("l_defficience_moteur2")
        self.engine.hardware.set_led_on("l_defficience_moteur3")
        self.engine.hardware.set_led_on("l_problem0")
        self.engine.hardware.set_led_on("l_problem1")
        self.engine.hardware.set_led_on("l_problem2")
        self.engine.hardware.set_led_on("l_fuite_O2")
        self.engine.hardware.set_led_on("l_alert0")
        self.engine.hardware.set_led_on("l_alert1")

        self.engine.hardware.set_led_off("l_antenne_com")

        def detection(_=None):
            # energy problems !
            self.engine.update_soft_state("listen_to_hardware", True)
            self.engine.update_hard_state("s_pilote_automatique1", False, silent=True)
            self.engine.update_hard_state("s_pilote_automatique2", False, silent=True)
            self.engine.update_hard_state("s_correction_direction", False, silent=True)
            self.engine.update_hard_state("s_correction_roulis", False, silent=True)
            self.engine.update_hard_state("s_correction_stabilisation", False, silent=True)
            self.engine.update_soft_state("listen_to_hardware", False)

            self.engine.update_soft_state("moteur1", False, silent=True)
            self.engine.update_soft_state("moteur2", False, silent=True)
            self.engine.update_soft_state("moteur3", False, silent=True)
            self.engine.update_soft_state("offset_ps_x", 2, silent=True)
            self.engine.update_soft_state("offset_ps_y", 1, silent=True)

        self.engine.taskMgr.doMethodLater(1, detection, 'fi1')

    @event('collision')
    def on_collision(self):
        self.engine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
        self.engine.update_soft_state("collision_occurred", True)
        self.engine.sound_manager.stop_bips()

        self.engine.taskMgr.doMethodLater(0.5, self.engine.sound_manager.play_sfx, 'fi3',
                                          extraArgs=['gaz_leak', True, 0.5])
        self.engine.sound_manager.stop("start_music")

        # leds
        self.engine.hardware.set_led_on("l_defficience_moteur1")
        self.engine.hardware.set_led_on("l_defficience_moteur2")
        self.engine.hardware.set_led_on("l_defficience_moteur3")
        self.engine.hardware.set_led_on("l_problem0")
        self.engine.hardware.set_led_on("l_problem1")
        self.engine.hardware.set_led_on("l_problem2")
        self.engine.hardware.set_led_on("l_fuite_O2")
        self.engine.hardware.set_led_on("l_alert0")
        self.engine.hardware.set_led_on("l_alert1")

        self.engine.hardware.set_led_off("l_antenne_com")

        def detection(e):
            # energy problems !
            self.engine.update_soft_state("listen_to_hardware", True)
            self.engine.update_hard_state("s_pilote_automatique1", False, silent=True)
            self.engine.update_hard_state("s_pilote_automatique2", False, silent=True)
            self.engine.update_hard_state("s_correction_direction", False, silent=True)
            self.engine.update_hard_state("s_correction_roulis", False, silent=True)
            self.engine.update_hard_state("s_correction_stabilisation", False, silent=True)
            self.engine.update_soft_state("listen_to_hardware", False)

            self.engine.update_soft_state("moteur1", False, silent=True)
            self.engine.update_soft_state("moteur2", False, silent=True)
            self.engine.update_soft_state("moteur3", False, silent=True)
            self.engine.update_soft_state("offset_ps_x", 2, silent=True)
            self.engine.update_soft_state("offset_ps_y", 1, silent=True)

            # self.engine.gui.event("alert_screen")
            # self.engine.gui.event("warning", )

        self.engine.taskMgr.doMethodLater(1, detection, 'fi1')

    @event('asteroid')
    def on_asteroid(self):
        self.engine.asteroid.spawn()

    @event('oxygen_leak')
    def on_oxygen_leak(self):
        send_event("set_gauge_goto_time", gauge="main_O2", time=800)
        self.engine.update_soft_state("main_O2", 0.0)
        self.do_method_later(180,
                             self.engine.sound_manager.play_sfx,
                             name='sound_o2_1',
                             extraArgs=['voice_alert_O2_5_33'])
        self.do_method_later(330,
                             self.engine.sound_manager.play_sfx,
                             name='sound_o2_2',
                             extraArgs=['voice_alert_O2_3_17'])

    @event('oxygen')
    def on_oxygen(self, time=420., value=0.0):
        send_event("set_gauge_goto_time", gauge="main_O2", time=time)
        self.engine.update_soft_state("main_O2", value)

    @event('CO2')
    def on_co2(self, time=420., value=0.0):
        send_event("set_gauge_goto_time", gauge="main_CO2", time=time)
        self.engine.update_soft_state("main_CO2", value)

    # elementary functions
    @event('shuttle_look_at')
    def on_shuttle_look_at(self, time=5.0, x=0.0, y=0.0, z=0.0):
        if time == 0.0:
            self.engine.shuttle.look_at(LVector3f(x, y, z))
        else:
            self.engine.shuttle.dynamic_look_at(LVector3f(x, y, z), time=time)

    @event('shuttle_pos')
    def on_shuttle_pos(self, x=0.0, y=0.0, z=0.0):
        self.engine.shuttle.set_pos(LVector3f(x, y, z))

    @event('shuttle_goto')
    def on_shuttle_goto(self, x=0.0, y=0.0, z=0.0, power=1.0):
        self.engine.shuttle.dynamic_goto(LVector3f(x, y, z), power)

    @event('shuttle_stop')
    def on_shuttle_stop(self, play_sound=True):
        self.engine.shuttle.stop(play_sound)

    @event('shuttle_goto_station')
    def on_shuttle_goto_station(self, power=1.0):
        pos, hpr = self.engine.space_craft.get_connection_pos_and_hpr()

        def _end(t=None):
            self.engine.shuttle.dynamic_goto_hpr(hpr, time=7)

        self.engine.shuttle.dynamic_goto(pos, power=power, t_spin=7.0, end_func=_end)

    @event('wait')
    def on_wait(self):
        pass

    @event('group')
    def on_group(self):
        pass

    @event('boost')
    def on_boost(self, direction=None, power=1.0):
        self.engine.shuttle.boost(direction, power)

    @event('play_sound')
    def on_play_sound(self, name=None, volume=None, loop=False):
        self.engine.sound_manager.play_sfx(name, volume=volume, loop=loop)

    @event('stop_sound')
    def on_stop_sound(self, name=None):
        self.engine.sound_manager.stop(name)

    @event('reset_buttons')
    def on_reset_buttons(self):
        self.engine.reset_hardware()

    @event('reset_leds')
    def on_reset_leds(self):
        self.engine.sound_manager.play_sfx("engine_starts")
        self.engine.hardware.hello_world()
        self.engine.hardware.init_states()

    @event('led_on')
    def on_led_on(self, id=None):
        self.engine.hardware.set_led_on(id)

    @event('led_off')
    def on_led_off(self, id=None):
        self.engine.hardware.set_led_off(id)

    @event('update_hardware_state')
    def on_update_hardware_state(self, name=None, value=None):
        self.engine.update_hard_state(name, value)

    @event('update_software_state')
    def on_update_software_state(self, name=None, value=None):
        self.engine.update_soft_state(name, value)

    def remove_incoming_events(self) -> None:
        """
        Remove all incoming events, ignoring steps
        """
        if hasattr(self, '_taskList'):
            # _taskList attribute is dynamically set when adding a task
            for task in list(self._taskList.values()):
                if not task.get_name().startswith('event'):
                    Logger.info(f'removing task "{task.get_name()}"')
                    self.remove_task(task)
                else:
                    Logger.info(f'keeping task "{task.get_name()}"')

    def pause(self) -> None:
        """
        Pauses the game, removing all incoming tasks
        """
        self._paused_tasks.clear()
        if hasattr(self, '_taskList'):
            # _taskList attribute is dynamically set when adding a task
            for task in list(self._taskList.values()):
                # incoming tasks have a non-null delay and negative elapsed_time which is the time to its start
                if task.get_delay() > 0.0 and task.get_elapsed_time() < 0:
                    self._paused_tasks.append([task, -task.get_elapsed_time()])
                    self.remove_task(task)

    def resume(self) -> None:
        """
        Resume the game paused with :func:`pause`
        """
        for paused_task, delay in self._paused_tasks:
            # set new delay for each task and add them to the task manager
            paused_task.set_delay(delay)
            self.add_task(paused_task)
        # remove all paused tasks
        self._paused_tasks.clear()

    def fulfill_current_step(self):
        """
        Fulfill the current step and starts the next one
        """
        self.steps[self.current_step].force_fulfill()

    def start_next_step(self):
        """
        Starts the next step.

        .. note:: this **does not** fulfill the current one

        See Also
            :func:`fulfill_current_step`
        """
        self.current_step += 1
        if self.current_step < len(self.steps):
            self.steps[self.current_step].start()
        else:
            send_event('end_game')

    def update_scenario(self, wait_end_if_fulfilled=True):
        """
        Checks if the current step can be stopped or not. If yes, passes to the next step. This function is intended to
        be called when the game state has changed and the scenario may pass to the next step.

        Args:
             wait_end_if_fulfilled (bool): if the current task has no ending conditions but has a limited time, setting
                this to :code:`True` will force to wait until the end of the task. Else, the task is considered as done
                and next step is started
        """
        if len(self.steps) > self.current_step >= 0:
            step = self.steps[self.current_step]
            if step.is_fulfilled(wait_end_if_fulfilled=wait_end_if_fulfilled):
                step.end(True)
