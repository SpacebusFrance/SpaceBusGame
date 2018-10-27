import datetime

from direct.showbase.DirectObject import DirectObject
from panda3d.core import LVector3f, LVector4f

from Engine.Utils.utils import read_xml_args


class Step:
    """
    Class representing one step in the scenario.
    """
    step_counter = 0

    def __init__(self, gameEngine, end_conditions=None, event_name="", max_time=None, start_time=None, args_dict=None,
                 win_sound=None, loose_sound=None, fulfill_if_lost=False):
        """

        :param gameEngine: the game object
        :param constraints: a dictionary containing the shuttle states and their expected values e.g  {'joy_0_ax_0': 1, 'control_unlock": True}
        :param start_event: a string
        :param max_time: the maximum time allowed for this step.
        """
        self.shuttle = gameEngine.shuttle
        self.gameEngine = gameEngine
        self.scenario = gameEngine.scenario
        self.sound_player = gameEngine.sound_manager
        self.name = event_name
        self.counter = Step.step_counter
        Step.step_counter += 1

        self.t_max = max_time
        self._to_do_task = None
        self.t_start = start_time if start_time is not None else 0.0

        self.constraints = end_conditions

        self._event_kwargs = args_dict
        self._event_name = event_name
        self._loose_task = None
        self._loose_sound = loose_sound
        self._win_sound = win_sound
        self._fulfill_if_lost = fulfill_if_lost

    def start(self):
        """
        Starts this step.

        :return:
        """
        print('\n\033[94m[' + self.gameEngine.get_time(True) + '] starting step', self.name, "(number", self.counter,
              "starting in : ", self.t_start, ' s.)\033[0m')
        print('\033[94m\ttime_max :', self.t_max, ' \033[0m')
        print('\033[94m\tconditions :', self.constraints, ' \033[0m')

        if self.constraints is None and self.t_max is None:
            print('\033[91m\t(warning) : this step has non ending_conditions nor max time\033[0m')
        if self.t_max is not None:
            self._loose_task = self.gameEngine.taskMgr.doMethodLater(self.t_start + self.t_max, self.end,
                                                                     extraArgs=[False], name=self.name)
        if self._event_name is not None:
            if self.t_start > 0:
                self._to_do_task = self.gameEngine.taskMgr.doMethodLater(self.t_start, self.scenario.event,
                                                                         extraArgs=[self._event_name,
                                                                                    self._event_kwargs], name=self.name)
            else:
                self.scenario.event(self._event_name, self._event_kwargs)

    def force_fulfill(self):
        print('\033[91m\t(warning) : fulfilling step', self.name, '\033[0m')

        if self.constraints is not None:
            for key in self.constraints:
                value = self.constraints[key]
                if isinstance(value, list):
                    value = 0.5 * (value[1] + value[0])
                if not self.gameEngine.update_hard_state(key, value):
                    self.gameEngine.update_soft_state(key, value)
        else:
            self.end(False)

    def is_fulfilled(self):
        """
        Checks if the wining conditions of this step are fulfilled.
        :return: True if all conditions are fulfilled. Else False.
        """
        if self.constraints is not None:
            for key in self.constraints:
                value = self.constraints[key]
                game_value = self.gameEngine.get_soft_state(key)

                if game_value is None:
                    game_value = self.gameEngine.get_hard_state(key)

                if isinstance(value, list):
                    if min(value) > game_value or game_value > max(value):
                        return False
                else:
                    if value != game_value:
                        return False
            return True
        return False

    def kill(self):
        # removing the loose task
        if self._loose_task is not None:
            self.gameEngine.taskMgr.remove(self._loose_task)
        if self._to_do_task is not None:
            self.gameEngine.taskMgr.remove(self._to_do_task)

    def end(self, win):
        """
        Ends the step and starts the next step.

        :param win: a boolean. If True or if the step is passive, the win_function is called (if it exists). If False, the loose_function is called.
        :return:
        """
        if win:
            print('\033[92m', "task won.", '\033[0m')
            if self._win_sound is not None:
                self.sound_player.play(self._win_sound)
        else:
            print('\033[91m', "task lost", '\033[0m')
            if self._loose_sound is not None:
                self.sound_player.play(self._loose_sound)
            if self._fulfill_if_lost:
                self.force_fulfill()

        # removing the loose task
        if self._loose_task is not None:
            self.gameEngine.taskMgr.remove(self._loose_task)
        if self._to_do_task is not None:
            self.gameEngine.taskMgr.remove(self._to_do_task)

        # starting the next step
        self.gameEngine.scenario.start_next_step()


class EventHandler(DirectObject):
    """
    The class that drives the scenario of the game. The scenario is divided in successive steps.
    Each step is defined as a certain number of conditions.
    Once these conditions are fulfilled, the scenario moves to the next step.
    """

    def __init__(self, gameEngine):
        DirectObject.__init__(self)

        self.gameEngine = gameEngine
        self.shuttle = None

        self.steps = []
        self.current_step = 0
        Step.step_counter = 0
        self.start_time = None
        self.last_score = None

    def _new_step(self, end_conditions=None, event=None, time_max=None, start_time=None, args_dict=None, win_sound=None,
                  loose_sound=None, fulfill_if_lost=False):
        if event is not None and len(event) > 0:
            # check some common end conditions
            if end_conditions is None and time_max is None:
                if event == "control_screen_event":
                    if args_dict.get("name", None) == "crew_lock_screen":
                        end_conditions = {"crew_screen_unlocked": True}
                    elif args_dict.get("name", None) == "target_screen":
                        end_conditions = {"target_screen_unlocked": True}
                elif event == "info_text":
                    end_conditions = {"info_text": False}
                elif event == "collision":
                    end_conditions = {"alert_screen_unlocked": True}
                elif event in ["shuttle_goto", "shuttle_goto_station", "shuttle_look_at"]:
                    end_conditions = {"is_moving": False}
                elif event in ["shuttle_stop", "led_off", "led_on", "show_score", "start_game", "restart", "end_game"]:
                    time_max = 0.0
                elif event == "play_sound":
                    time_max = self.gameEngine.sound_manager.get_sound_length(args_dict.get("name", None)) + 1.0

            if event == "info_text":
                if args_dict is None:
                    args_dict = {}
                if "close_time" not in args_dict:
                    args_dict["close_time"] = time_max

            self.steps.append(Step(self.gameEngine,
                                   end_conditions=end_conditions,
                                   event_name=event,
                                   max_time=time_max,
                                   start_time=start_time,
                                   args_dict=args_dict,
                                   loose_sound=loose_sound,
                                   win_sound=win_sound,
                                   fulfill_if_lost=fulfill_if_lost
                                   ))

    def reset(self):
        if self.shuttle is None:
            self.shuttle = self.gameEngine.shuttle

        # stop steps
        try:
            self.steps[self.current_step].kill()
        except IndexError:
            pass

        self.current_step = 0
        Step.step_counter = 0
        self.start_time = None
        self.last_score = None

    def load_scenario(self, name="default"):
        try:
            file = open(self.gameEngine.params("scenario_path") + name + ".xml")
            lines = file.readlines()
            file.close()

            self.steps.clear()

            current = {"event": None, "time_max": None, "start_time": None, "end_conditions": None, "args_dict": None,
                       "loose_sound": None, "win_sound": None, "fulfill_if_lost": False}
            for line in lines:
                if not line.strip().startswith('<!--'):
                    if "<step" in line and "event=" in line:
                        args = read_xml_args(line)
                        current["event"] = args.pop("event")
                        current["time_max"] = args.pop("time_max", None)
                        current["start_time"] = args.pop("start_time", None)
                        current["loose_sound"] = args.pop("loose_sound", None)
                        current["win_sound"] = args.pop("win_sound", None)
                        current["fulfill_if_lost"] = args.pop("fulfill_if_lost", False)
                        if len(args) > 0:
                            current["args_dict"] = args.copy()
                        if "/>" in line:
                            self._new_step(**current)
                            current = {"event": None, "time_max": None, "start_time": None, "end_conditions": None,
                                       "args_dict": None, "loose_sound": None, "win_sound": None,
                                       "fulfill_if_lost": False}
                    if "</step>" in line:
                        self._new_step(**current)
                        current = {"event": None, "time_max": None, "start_time": None, "end_conditions": None,
                                   "args_dict": None, "loose_sound": None, "win_sound": None, "fulfill_if_lost": False}
                    elif "<end_conditions>" in line:
                        current["end_conditions"] = dict()
                    elif "<condition" in line and "key" in line and "value" in line:
                        args = read_xml_args(line)
                        current["end_conditions"][args.get("key", None)] = args.get("value", None)

        except FileNotFoundError:
            print("Error while loading file", name, "file does not exists")

    def end_game(self):
        if self.start_time is not None:
            self.last_score = self.gameEngine.get_time() - self.start_time
        else:
            self.last_score = self.gameEngine.get_time()
        # file = open(self.gameEngine.params("score_file"))
        # scores = [float(l) for l in file.readlines()]
        # file.close()
        # scores.append(self.last_score)
        # scores.sort()

        file = open(self.gameEngine.params("score_file"), 'a')
        file.write(str(self.last_score) + "\n")
        file.close()

    def get_score(self):
        if self.last_score is not None:
            file = open(self.gameEngine.params("score_file"))
            scores = [float(l) for l in file.readlines()]
            file.close()
            scores.sort()
            return scores.index(self.last_score) + 1, len(scores), str(datetime.timedelta(seconds=self.last_score))
        return None, None, None

    def start_game(self):
        self.current_step = 0
        self.start_time = self.gameEngine.get_time()
        self.shuttle.stop(play_sound=False)

        if len(self.steps) > 0:
            self.steps[0].start()

    def event(self, event_name, arg_dict=None):
        """
        :param event_name: a string identifying the event
        :param arg_dict: a dictionary (packed) containing eventual arguments. It is not passed as **kwargs since it must be compatible with the doMethodLater sending only list of args.
        """
        arg_dict = arg_dict if arg_dict is not None else {}

        if event_name == "reset_game":
            self.gameEngine.reset_game()

        elif event_name == "restart":
            self.gameEngine.reset_game()
            self.start_game()

        elif event_name == "start_game":
            """
            restarts the chrono
            """
            self.gameEngine.start_time = self.gameEngine.get_time()

        elif event_name == "end_game":
            self.end_game()

        elif event_name == "raw_collision":
            self.gameEngine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
            self.gameEngine.update_soft_state("collision_occurred", True)
            self.gameEngine.sound_manager.stop_bips()
            self.gameEngine.taskMgr.doMethodLater(2.0,
                                                  self.gameEngine.sound_manager.play,
                                                  'fi3',
                                                  extraArgs=['gaz_leak', True, 0.5])
            self.gameEngine.sound_manager.stop("start_music")

            # leds
            self.gameEngine.hardware.set_led_on("l_defficience_moteur1")
            self.gameEngine.hardware.set_led_on("l_defficience_moteur2")
            self.gameEngine.hardware.set_led_on("l_defficience_moteur3")
            self.gameEngine.hardware.set_led_on("l_problem0")
            self.gameEngine.hardware.set_led_on("l_problem1")
            self.gameEngine.hardware.set_led_on("l_problem2")
            self.gameEngine.hardware.set_led_on("l_fuite_O2")
            self.gameEngine.hardware.set_led_on("l_alert0")
            self.gameEngine.hardware.set_led_on("l_alert1")

            self.gameEngine.hardware.set_led_off("l_antenne_com")

            self.gameEngine.update_soft_state("listen_to_hardware", True)
            self.gameEngine.update_hard_state("s_pilote_automatique1", False, silent=True)
            self.gameEngine.update_hard_state("s_pilote_automatique2", False, silent=True)
            self.gameEngine.update_hard_state("s_correction_direction", False, silent=True)
            self.gameEngine.update_hard_state("s_correction_roulis", False, silent=True)
            self.gameEngine.update_hard_state("s_correction_stabilisation", False, silent=True)
            self.gameEngine.update_soft_state("listen_to_hardware", False)

            self.gameEngine.update_soft_state("moteur1", False, silent=True)
            self.gameEngine.update_soft_state("moteur2", False, silent=True)
            self.gameEngine.update_soft_state("moteur3", False, silent=True)
            self.gameEngine.update_soft_state("offset_ps_x", 2, silent=True)
            self.gameEngine.update_soft_state("offset_ps_y", 1, silent=True)

            self.gameEngine.taskMgr.doMethodLater(3, self.gameEngine.sound_manager.play,
                                                  'fi2',
                                                  extraArgs=['voice_alert'])

        elif event_name == "collision":
            """
            The first impact function
            """
            self.gameEngine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
            self.gameEngine.update_soft_state("collision_occurred", True)
            self.gameEngine.sound_manager.stop_bips()
            # self.gameEngine.sound_manager.play("gaz_leak", loop=True)
            self.gameEngine.taskMgr.doMethodLater(0.5, self.gameEngine.sound_manager.play, 'fi3',
                                                  extraArgs=['gaz_leak', True, 0.5])
            self.gameEngine.sound_manager.stop("start_music")

            # leds
            self.gameEngine.hardware.set_led_on("l_defficience_moteur1")
            self.gameEngine.hardware.set_led_on("l_defficience_moteur2")
            self.gameEngine.hardware.set_led_on("l_defficience_moteur3")
            self.gameEngine.hardware.set_led_on("l_problem0")
            self.gameEngine.hardware.set_led_on("l_problem1")
            self.gameEngine.hardware.set_led_on("l_problem2")
            self.gameEngine.hardware.set_led_on("l_fuite_O2")
            self.gameEngine.hardware.set_led_on("l_alert0")
            self.gameEngine.hardware.set_led_on("l_alert1")

            self.gameEngine.hardware.set_led_off("l_antenne_com")

            def detection(e):
                # energy problems !
                # self.gameEngine.update_soft_state("pilote_automatique", False, silent=True)
                self.gameEngine.update_soft_state("listen_to_hardware", True)
                self.gameEngine.update_hard_state("s_pilote_automatique1", False, silent=True)
                self.gameEngine.update_hard_state("s_pilote_automatique2", False, silent=True)
                self.gameEngine.update_hard_state("s_correction_direction", False, silent=True)
                self.gameEngine.update_hard_state("s_correction_roulis", False, silent=True)
                self.gameEngine.update_hard_state("s_correction_stabilisation", False, silent=True)
                self.gameEngine.update_soft_state("listen_to_hardware", False)

                self.gameEngine.update_soft_state("moteur1", False, silent=True)
                self.gameEngine.update_soft_state("moteur2", False, silent=True)
                self.gameEngine.update_soft_state("moteur3", False, silent=True)
                self.gameEngine.update_soft_state("offset_ps_x", 2, silent=True)
                self.gameEngine.update_soft_state("offset_ps_y", 1, silent=True)

                self.gameEngine.control_screen.event("alert_screen")

            self.gameEngine.taskMgr.doMethodLater(1, detection, 'fi1')

        elif event_name == "asteroid":
            self.gameEngine.asteroid.spawn()

        elif event_name == "oxygen_leak":
            self.gameEngine.control_screen.event("set_gauge_goto_time", gauge="main_O2", time=800)
            self.gameEngine.update_soft_state("main_O2", 0.0)
            self.gameEngine.task_mgr.do_method_later(180,
                                                     self.gameEngine.sound_manager.play,
                                                     name='sound_o2_1',
                                                     extraArgs=['voice_alert_O2_5_33'])
            self.gameEngine.task_mgr.do_method_later(330,
                                                     self.gameEngine.sound_manager.play,
                                                     name='sound_o2_2',
                                                     extraArgs=['voice_alert_O2_3_17'])

        elif event_name == "info_text":
            self.gameEngine.control_screen.info_text(arg_dict.get("text", ""),
                                                     close_time=arg_dict.get("close_time", None))

        elif event_name == "oxygen":
            self.gameEngine.control_screen.event("set_gauge_goto_time", gauge="main_O2",
                                                 time=arg_dict.get("time", 420.0))
            self.gameEngine.update_soft_state("main_O2", arg_dict.get("value", 0.0))

        elif event_name == "CO2":
            self.gameEngine.control_screen.event("set_gauge_goto_time", gauge="main_CO2",
                                                 time=arg_dict.get("time", 420.0))
            self.gameEngine.update_soft_state("main_CO2", arg_dict.get("value", 0.0))

        # elementary functions

        elif event_name == "shuttle_look_at":
            if arg_dict.get("time", 5.0) == 0.0:
                self.gameEngine.shuttle.look_at(
                    LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)))
            else:
                self.gameEngine.shuttle.dynamic_look_at(
                    LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)),
                    time=arg_dict.get("time", 5.0))

        elif event_name == "suttle_pos":
            self.gameEngine.shuttle.set_pos(LVector3f(arg_dict.get("x", 0.0),
                                                      arg_dict.get("y", 0.0),
                                                      arg_dict.get("z", 0.0))
                                            )

        elif event_name == "shuttle_goto":
            self.gameEngine.shuttle.dynamic_goto(
                LVector3f(arg_dict.get("x", 0.0), arg_dict.get("y", 0.0), arg_dict.get("z", 0.0)),
                arg_dict.get("power", 1.0))

        elif event_name == "shuttle_stop":
            self.gameEngine.shuttle.stop(arg_dict.get("play_sound", True))

        elif event_name == "shuttle_goto_station":
            pos, hpr = self.gameEngine.space_craft.get_connection_pos_and_hpr()

            def _end(t=None):
                self.gameEngine.shuttle.dynamic_goto_hpr(hpr, time=7)

            self.gameEngine.shuttle.dynamic_goto(pos, power=arg_dict.get("power", 1.0), t_spin=7.0, end_func=_end)
            # self.gameEngine.shuttle.dynamic_goto_hpr(hpr, time=7)

        elif event_name == "wait":
            pass

        elif event_name == "control_screen_event":
            self.gameEngine.control_screen.event(arg_dict.get("name", ""), **arg_dict)

        elif event_name == "show_score":
            score, tot, time = self.get_score()
            t = time.split(":")[1] + " minutes, " + time.split(":")[2].split(".")[0] + " secondes."
            self.gameEngine.control_screen.event("image_screen_text",
                                                 text="Bravo équipage !\n\nVotre temps : " + t + "\nVous êtes " + str(
                                                     score) + "ème sur " + str(tot),
                                                 size=4,
                                                 color=LVector4f(0.886, 0.725, 0.443, 1.0),
                                                 alpha_time=arg_dict.get("alpha_time", 3.0)
                                                 )

        elif event_name == "boost":
            self.gameEngine.shuttle.boost(arg_dict.get("direction", None), arg_dict.get("power", 1))

        elif event_name == "play_sound":
            self.gameEngine.sound_manager.play(arg_dict.get("name", None), volume=arg_dict.get("volume", None))

        elif event_name == "stop_sound":
            self.gameEngine.sound_manager.stop(arg_dict.get("name", None))

        elif event_name == "leds_init":
            self.gameEngine.sound_manager.play("engine_starts")
            self.gameEngine.hardware.hello_world()
            self.gameEngine.hardware.init_states()

        # elif event_name == "start_on_enter":
        #     self.gameEngine.hardware.hello_world()

        elif event_name == "led_on":
            self.gameEngine.hardware.set_led_on(arg_dict.get("id", None))

        elif event_name == "led_off":
            self.gameEngine.hardware.set_led_off(arg_dict.get("id", None))

        elif event_name == "update_hardware_state":
            self.gameEngine.update_hard_state(arg_dict.get("name", None), arg_dict.get("value", None))

        elif event_name == "update_software_state":
            self.gameEngine.update_soft_state(arg_dict.get("name", None), arg_dict.get("value", None))

        elif event_name == "end_game":
            print("game won !")

    def fulfill_current_step(self):
        self.steps[self.current_step].force_fulfill()

    def start_next_step(self):
        self.current_step += 1
        if self.current_step < len(self.steps):
            self.steps[self.current_step].start()
        else:
            self.event("end_game")

    def update_shuttle_state(self):
        """
        Checks if the current step can be stopped or not. If yes, passes to the next step.

        :return:
        """
        if len(self.steps) > self.current_step >= 0:
            step = self.steps[self.current_step]
            if step.is_fulfilled():
                step.end(True)
