import datetime
import re
import pandas as pd
from direct.showbase.DirectObject import DirectObject
from panda3d.core import LVector3f, LVector4f

from engine.scenario.scenario_event import Event
from engine.utils.global_utils import read_xml_args
from engine.utils.logger import Logger
from engine.scenario.scenario_step import Step


class Scenario(DirectObject):
    """
    The class that drives the scenario of the game. The scenario is divided in successive steps.
    Each step is defined as a certain number of conditions.
    Once these conditions are fulfilled, the scenario moves to the next step.
    """
    def __init__(self, game_engine):
        DirectObject.__init__(self)

        self.engine = game_engine
        self.shuttle = None
        self._scenario = None

        self.steps = []
        self.pending_steps = dict()
        self.current_step = 0
        Step.step_counter = 0
        self.start_time = None
        self.last_score = None

    def _new_step(self, id, end_conditions=None, action=None, time_max=None, start_time=None, args_dict=None,
                  win_sound=None, loose_sound=None, fulfill_if_lost=False, hint_sound=None, hint_time=None):
        if action is not None and len(action) > 0:
            # check some common end conditions
            if end_conditions is None and time_max is None:
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
                    time_max = self.engine.sound_manager.get_sound_length(args_dict.get("name", None)) + 1.0
                elif action in ["shuttle_stop", "led_off", "led_on", "restart", "end_game", "start_game", "show_score",
                                "stop_sound", "sound_volume"]:
                    time_max = 0.0

            if action == "info_text":
                if args_dict is None:
                    args_dict = {}
                if "close_time" not in args_dict:
                    args_dict["close_time"] = time_max

            if start_time is not None and start_time > 0.0:
                if start_time in self.pending_steps:
                    Logger.error('there is already a step for delay :', start_time)
                self.pending_steps[start_time] = Event(self.engine,
                                                       id=id,
                                                       action=action,
                                                       args_dict=args_dict,
                                                       )
            else:
                self.steps.append(Step(self.engine,
                                       end_conditions=end_conditions,
                                       action=action,
                                       max_time=time_max,
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
        Reset the game. Remove all running, tasks, stops the current step if is it playing and reset time
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
        self.start_time = None
        self.last_score = None

    def load_scenario(self, name):
        """
        Load the desired scenario

        Args:
            name (str): the name of the scenario to load
        """
        try:
            with open(self.engine("scenario_path") + name + ".xml", 'r', encoding="utf-8") as file:
                lines = file.readlines()

            self.steps.clear()
            self._scenario = name

            event_counter = 0

            # custom xml file parsing
            def_args = {"action": None, "time_max": None, "start_time": None, "end_conditions": None, "args_dict": None,
                        "loose_sound": None, "win_sound": None, "fulfill_if_lost": False, "hint_sound": None,
                        "hint_time": None}
            current = def_args.copy()

            for line in lines:
                line = line.strip()
                if not line.startswith('<!--'):
                    kind = re.search(r'<\s*(\w*)\s', line).group(1) if re.search(r'<\s*(\w*)\s', line) is not None else None
                    if kind == 'step' and "action=" in line:
                        args = read_xml_args(line)
                        current["action"] = args.pop("action")
                        current["id"] = args.pop("id", 'step_{}'.format(len(self.steps)))
                        current["time_max"] = args.pop("time_max", None)
                        # current["start_time"] = args.pop("start_time", None)
                        current["loose_sound"] = args.pop("loose_sound", None)
                        current["win_sound"] = args.pop("win_sound", None)
                        current["fulfill_if_lost"] = args.pop("fulfill_if_lost", False)
                        current["hint_sound"] = args.pop("hint_sound", None)
                        current["hint_time"] = args.pop("hint_time", None)
                        if 'start_time' in args:
                            Logger.warning('start_time argument is ignored for steps !')
                        if len(args) > 0:
                            current["args_dict"] = args.copy()
                        if "/>" in line:
                            self._new_step(**current)
                            current = def_args.copy()
                    if "</step>" in line:
                        self._new_step(**current)
                        current = def_args.copy()
                    if kind == 'event' and 'action=' in line:
                        args = read_xml_args(line)
                        self._new_step(action=args.pop("action"), start_time=args.pop('start_time', 0.0),
                                       args_dict=args, id=args.pop("id", 'event_{}'.format(event_counter)))
                        event_counter += 1
                    # elif "<end_conditions>" in line:
                    #     current["end_conditions"] = dict()
                    elif "<condition" in line and "key" in line and "value" in line:
                        args = read_xml_args(line)
                        if current['end_conditions'] is None:
                            current["end_conditions"] = dict()
                        current["end_conditions"][args.get("key", None)] = args.get("value", None)
        except FileNotFoundError:
            Logger.error('Error while loading file {}. It does not exists !'.format(name))

    def get_scenario(self):
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
        if self.start_time is not None:
            self.last_score = self.engine.get_time() - self.start_time
        else:
            self.last_score = self.engine.get_time()

        if save_score:
            # write score
            with open(self.engine("score_file"), 'a') as file:
                file.write(str(self.last_score) + "\n")

        if show_end_screen:
            print(self.last_score, str(datetime.timedelta(seconds=self.last_score)))
            # format time
            hours, minutes, seconds = re.match(r'^(?P<hour>\d+):(?P<mins>\d+):(?P<seconds>\d+).*$',
                                               str(datetime.timedelta(seconds=self.last_score))).groups()
            with open(self.engine("score_file"), 'r') as f:
                scores = list(map(float, f.readlines()))
                position = len(list(filter(lambda x: x < self.last_score, scores)))
                total = len(scores)
            self.engine.gui.end_screen(player_position=position,
                                       total_players=total,
                                       time_minutes=minutes,
                                       time_seconds=seconds)

    # def get_score(self):
    #     """
    #     Get the last registered score.
    #
    #     Returns:
    #         the position of the last game ad an :obj:`int`, the total number of games (:obj:`int`) and the score
    #         itself representing the time as a :obj:`str` as ``HH:MM``
    #     """
    #     if self.last_score is not None:
    #         results = pd.read_csv(self.engine('score_file'))
    #         position = len(results.sort_values('score').loc[lambda x: x.score < self.last_score])
    #         tot_games = len(results) + 1
    #
    #         # append new score and save file
    #         results.append(pd.DataFrame({'score': [self.last_score],
    #                                     'time': [pd.to_datetime('today').strftime('%Y-%m-%d %H:%M')]}),
    #                        sort=False).to_csv(self.engine('score_file'), index=False)
    #
    #         hours, minutes, seconds = re.match(r'^(?P<hour>\d+):(?P<mins>\d+):(?P<seconds>\d+)$',
    #                                            str(datetime.timedelta(seconds=self.last_score))).groups()
    #         return position, tot_games, '{}:{}'.format(minutes, seconds)
    #         # return scores.index(self.last_score) + 1, len(scores), str(datetime.timedelta(seconds=self.last_score))
    #     return None, None, None

    def start_game(self):
        """
        Starts the game. Stops the shuttle, reset the time and starts the first step
        """
        self.current_step = 0
        self.start_time = self.engine.get_time()
        self.shuttle.stop(play_sound=False)

        # start all pending steps
        for time in self.pending_steps:
            self.do_method_later(time,
                                 self.pending_steps[time].start,
                                 name='event_{}'.format(time))

        if len(self.steps) > 0:
            self.steps[0].start()

    def event(self, event_name, arg_dict=None):
        """
        Call a scenario event

        So far, possible events are:

        - *start_game*
        - *reset_game*
        - *restart*
        - *end_game*
        - *show_score*
        - *raw_collision*
        - *collision*
        - *asteroid*
        - *oxygen_leak*
        - *oxygen*
        - *CO2*
        - *info_text*
        - *shuttle_look_at*
        - *shuttle_pos*
        - *shuttle_goto*
        - *shuttle_stop*
        - *shuttle_goto_station*
        - *shuttle_goto_station*
        - *boost*
        - *wait*
        - *control_screen_event*
        - *terminal_start_session*
        - *terminal_print_file*
        - *terminal_question*
        - *play_sound*
        - *stop_sound*
        - *reset_buttons*
        - *reset_leds*
        - *led_on*
        - *led_off*
        - *update_hardware_state*
        - *update_software_state*

        Args:
            event_name (str): the name of the event
            arg_dict (dict): optional arguments passed to the event
        """
        arg_dict = arg_dict if arg_dict is not None else {}

        if event_name in ["reset_game", 'reset']:
            self.engine.reset_game()

        elif event_name == "restart":
            self.engine.reset_game()
            self.start_game()

        elif event_name in ["start_game", 'start']:
            self.start_game()

        elif event_name in ['stop', 'stop_game']:
            self.steps[min(self.current_step, len(self.steps) - 1)].end(win=False)
            # this avoid to play next step
            self.current_step = len(self.steps)
            # remove all incoming tasks but keep steps
            for task in list(self._taskList.values()):
                if not task.get_name().startswith('event'):
                    self.remove_task(task)

        elif event_name == 'goto_step':
            # stop game
            self.steps[min(self.current_step, len(self.steps) - 1)].end(win=False)

            # remove all incoming tasks but keep steps
            for task in list(self._taskList.values()):
                if not task.get_name().startswith('event'):
                    self.remove_task(task)

            # goto next step
            target_step = arg_dict['goto_id']
            self.current_step = None
            for i, step in enumerate(self.steps):
                if step.id == target_step:
                    self.current_step = i - 1
                    break
            if self.current_step is None:
                raise KeyError('goto_id {} does not exist !'.format(target_step))
            self.start_next_step()

        elif event_name == "end_game":
            # remove all incoming events
            for task in list(self._taskList.values()):
                if not task.get_name().startswith('event'):
                    self.remove_task(task)

            # call the end game
            self.end_game(show_end_screen=arg_dict.get('show_end_screen', True),
                          save_score=arg_dict.get('save_score', True))

        elif event_name == "collision_new":
            """
            The first impact function
            """
            self.engine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
            self.engine.update_soft_state("collision_occurred", True)
            self.engine.sound_manager.stop_bips()

            self.engine.taskMgr.doMethodLater(0.5, self.engine.sound_manager.play, 'fi3',
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

        elif event_name == "collision":
            """
            The first impact function
            """
            self.engine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
            self.engine.update_soft_state("collision_occurred", True)
            self.engine.sound_manager.stop_bips()

            self.engine.taskMgr.doMethodLater(0.5, self.engine.sound_manager.play, 'fi3',
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

        elif event_name == "asteroid":
            self.engine.asteroid.spawn()

        elif event_name == "oxygen_leak":
            self.engine.gui.event("set_gauge_goto_time", gauge="main_O2", time=800)
            self.engine.update_soft_state("main_O2", 0.0)
            self.do_method_later(180,
                                 self.engine.sound_manager.play,
                                 name='sound_o2_1',
                                 extraArgs=['voice_alert_O2_5_33'])
            self.do_method_later(330,
                                 self.engine.sound_manager.play,
                                 name='sound_o2_2',
                                 extraArgs=['voice_alert_O2_3_17'])

        # elif event_name == "info_text":
        #     self.engine.gui.info_text(arg_dict.get("text", ""),
        #                                          close_time=arg_dict.get("close_time", None))

        elif event_name == "oxygen":
            self.engine.gui.event("set_gauge_goto_time", gauge="main_O2", time=arg_dict.get("time", 420.0))
            self.engine.update_soft_state("main_O2", arg_dict.get("value", 0.0))

        elif event_name == "CO2":
            self.engine.gui.event("set_gauge_goto_time", gauge="main_CO2", time=arg_dict.get("time", 420.0))
            self.engine.update_soft_state("main_CO2", arg_dict.get("value", 0.0))

        # elementary functions

        elif event_name == "shuttle_look_at":
            if arg_dict.get("time", 5.0) == 0.0:
                self.engine.shuttle.look_at(
                    LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)))
            else:
                self.engine.shuttle.dynamic_look_at(
                    LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)),
                    time=arg_dict.get("time", 5.0))

        elif event_name == "shuttle_pos":
            self.engine.shuttle.set_pos(
                LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)))

        elif event_name == "shuttle_goto":
            self.engine.shuttle.dynamic_goto(LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0),
                                                       arg_dict.get("z", 0.0)), arg_dict.get("power", 1.0))

        elif event_name == "shuttle_stop":
            self.engine.shuttle.stop(arg_dict.get("play_sound", True))

        elif event_name == "shuttle_goto_station":
            pos, hpr = self.engine.space_craft.get_connection_pos_and_hpr()

            def _end(t=None):
                self.engine.shuttle.dynamic_goto_hpr(hpr, time=7)

            self.engine.shuttle.dynamic_goto(pos, power=arg_dict.get("power", 1.0), t_spin=7.0, end_func=_end)

        elif event_name == "wait":
            pass

        # elif event_name == "show_score":
        #     score, tot, time = self.get_score()
        #     t = time.split(":")[1] + " minutes, " + time.split(":")[2].split(".")[0] + " secondes."
        #     self.engine.gui.event("image_screen_text",
        #                           text="Bravo équipage !\n\nVotre temps : " + t +"\nVous êtes " + str(score) + "ème sur " + str(tot),
        #                           pos_y=0.2,
        #                           size=6,
        #                           color=LVector4f(0.886, 0.725, 0.443, 1.0),
        #                           alpha_time=arg_dict.get("alpha_time", 3.0)
        #                           )

        elif event_name == "boost":
            self.engine.shuttle.boost(arg_dict.get("direction", None), arg_dict.get("power", 1))

        elif event_name == "play_sound":
            self.engine.sound_manager.play(arg_dict.get("name", None),
                                           volume=arg_dict.get("volume", None),
                                           loop=arg_dict.get('loop', False))

        elif event_name == "stop_sound":
            self.engine.sound_manager.stop(arg_dict.get("name", None))

        elif event_name == "reset_buttons":
            self.engine.reset_hardware()

        elif event_name == "reset_leds":
            self.engine.sound_manager.play("engine_starts")
            self.engine.hardware.hello_world()
            self.engine.hardware.init_states()

        elif event_name == "led_on":
            self.engine.hardware.set_led_on(arg_dict.get("id", None))

        elif event_name == "led_off":
            self.engine.hardware.set_led_off(arg_dict.get("id", None))

        elif event_name == "update_hardware_state":
            self.engine.update_hard_state(arg_dict.get("name", None), arg_dict.get("value", None))

        elif event_name == "update_software_state":
            self.engine.update_soft_state(arg_dict.get("name", None), arg_dict.get("value", None))

        else:
            # pass to gui
            if 'time_max' in arg_dict and arg_dict['time_max'] is not None:
                # remove the window at the end
                arg_dict['close_time'] = min(arg_dict.get('close_time', 1E3), arg_dict.pop('time_max'))
            self.engine.gui.event(event_name, **arg_dict)

        # self.update_scenario()

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
            self.event("end_game")

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
