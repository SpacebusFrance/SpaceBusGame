import datetime
import inspect
import re

from direct.showbase.DirectObject import DirectObject
from panda3d.core import LVector3f, WindowProperties

from engine.gui.windows.button_window import ButtonWindow
from engine.scenario.scenario_event import ScenarioStep
from engine.utils.event_handler import EventObject, event, send_event
from engine.utils.global_utils import read_xml_args
from engine.utils.logger import Logger


class IncomingGameEvents(DirectObject):
    _count = 0

    def __init__(self):
        super().__init__()
        self._events = dict()
        self._paused_tasks = []

    def add_event(self, time, method) -> str:
        name = f'scenario_event_{IncomingGameEvents._count}'
        Logger.info(f'adding event {name} in {time:.2f} seconds')
        self._events[name] = self.doMethodLater(
            time, method, name=name)
        IncomingGameEvents._count += 1
        return name

    def is_event_alive(self, name: str) -> bool:
        task = self._events.get(name, None)
        if task is not None:
            return task.is_alive()
        return False

    def remove_all_events(self):
        for _event in self._events.values():
            self.remove_task(_event)
        self._events.clear()

    def remove_event(self, name):
        task = self._events.pop(name, None)
        if task is not None:
            self.remove_task(task)

    def pause(self) -> None:
        """
        Pauses the game, removing all incoming tasks
        """
        self._paused_tasks.clear()
        for task in self._events.values():
            # incoming tasks have a non-null delay and negative elapsed_time which is the time to its start
            if task.get_delay() > 0.0 and task.get_elapsed_time() < 0:
                self._paused_tasks.append([task, max(0, -task.get_elapsed_time())])
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

        self.event_manager = IncomingGameEvents()
        self.steps = []
        self.pending_steps = dict()
        self.current_step = 0
        self.game_time = None
        self.last_score = None

        self._paused_tasks = []

    def _new_step(self, id, end_conditions=None, action=None, duration=None, delay=None, args_dict=None,
                  blocking=True,
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

                elif action in ["shuttle_stop", "led_off", "led_on", "start_game", "show_score",
                                "set_screen", "stop_sound", "sound_volume", "disable_hardware", "play_music",
                                "enable_hardware"] and duration is None:
                    # these actions have a default duration to 0.0
                    duration = 0.0

                elif action in ['restart']:
                    # for this specific event, we set
                    # a high duration in order to
                    # ensure that it will be considered
                    # as blocking and won't call
                    # `start_next_step` in its init.
                    # In all cases, it will be removed in
                    # when "restart" event is triggered
                    duration = 100

            if delay is None:
                # no delay is a 0.0 delay
                delay = 0.0

            if duration == 0.0 and delay == 0.0 and end_conditions is None:
                # if both duration and delay are zeros
                # together with no end conditions
                # it means that this step is not blocking.
                blocking = False

            # check that we don't have simultaneously
            # end conditions and a duration
            assert duration is None or end_conditions is None, \
                f'step {action} with id {id} has both duration ({duration}) and ' \
                f'end conditions {end_conditions}. Cannot have both simultaneously.'

            # check that this step is either blocking or has a zero
            # duration and no end conditions
            assert blocking or ((duration == 0.0 or duration is None) and end_conditions is None), \
                f'step {action} with id {id} is not blocking but has a duration ({duration}) and/or ' \
                f'end conditions {end_conditions}'

            self.steps.append(ScenarioStep(
                self.engine,
                end_conditions=end_conditions,
                action=action,
                duration=duration,
                blocking=blocking,
                delay=delay,
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
        # self.remove_all_tasks()
        self.event_manager.remove_all_events()

        # stop steps
        try:
            self.steps[self.current_step].kill()
        except IndexError:
            pass

        self.current_step = 0
        self.game_time = None
        self.last_score = None

    def load_scenario(self, name: str) -> None:
        """
        Load the desired scenario. Creates all step from xml file

        Args:
            name (str): the name of the xml scenario to load
        """
        try:
            with open(self.engine.get_option("scenario_path") + name + ".xml", 'r', encoding="utf-8") as file:
                lines = file.readlines()

            self.steps.clear()
            self._scenario = name

            event_counter = 0

            # custom xml file parsing
            def_args = {"action": None, "duration": None, "delay": None, "end_conditions": None, "args_dict": None,
                        "loose_sound": None, "win_sound": None, "fulfill_if_lost": False, "hint_sound": None,
                        "hint_time": None, 'blocking': True}
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

                        if len(args) > 0:
                            # store remaining arguments in args_dict argument
                            current["args_dict"] = args.copy()  # noqa
                        if "/>" in line:
                            # end of line, add a new step with current arguments
                            self._new_step(**current)
                            # and reset current arguments
                            current = def_args.copy()

                    elif kind == 'group':
                        # it is a group, we add it as an empty step
                        args = read_xml_args(line)
                        current["action"] = "group" # noqa
                        current["id"] = args.pop("id", f'step_{len(self.steps)}')
                        current["duration"] = 0.0   # noqa
                        # idem, add a new step
                        self._new_step(**current)
                        # and reset arguments
                        current = def_args.copy()

                    elif "</step>" in line:
                        # enf od step, store a new one
                        self._new_step(**current)
                        # and reset current arguments
                        current = def_args.copy()

                    elif kind == 'event' and 'action=' in line:
                        # it is an event
                        args = read_xml_args(line)
                        # simply add a new step
                        self._new_step(
                            action=args.pop("action"),
                            delay=args.pop('delay', 0.0),
                            args_dict=args,
                            blocking=False,
                            duration=0,
                            id=args.pop("id", f'event_{event_counter}')
                        )
                        # and reset arguments
                        current = def_args.copy()

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
            with open(f'{self.engine.get_option("score_folder")}scores_{self._scenario}.txt', 'a+') as file:
                file.write(f'{self.last_score}\n')

        if show_end_screen:            # format time
            hours, minutes, seconds = re.match(r'^(?P<hour>\d+):(?P<mins>\d+):(?P<seconds>\d+).*$',
                                               str(datetime.timedelta(seconds=self.last_score))).groups()
            try:
                with open(f'{self.engine.get_option("score_folder")}scores_{self._scenario}.txt', 'r') as f:
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
        Logger.info('-'*20)
        Logger.info('Starting new scenario')
        Logger.info('-'*20)
        Logger.info('')
        self.current_step = 0
        self.game_time = self.engine.get_time()
        # self.shuttle.stop(play_sound=False)

        # # start all pending steps
        # for time in self.pending_steps:
        #     self.do_method_later(time,
        #                          self.pending_steps[time].start,
        #                          name='event_{}'.format(time))

        if len(self.steps) > 0:
            self.steps[0].start()

    @event('reset_to_menu')
    def on_reset_to_menu(self):
        self.engine.reset_game()

    @event('restart')
    def on_restart(self):
        # we must kill current step
        self.steps[min(self.current_step, len(self.steps) - 1)].end(
            win=False,
            start_next_step=False
        )
        # and reset game
        self.engine.reset_game(start=True)

    @event(['start_game', 'start'])
    def on_start(self):
        self.start_game()

    # @event(['stop', 'stop_game'])
    # def on_stop(self):
    #     self.steps[min(self.current_step, len(self.steps) - 1)].end(win=False)
    #     # this avoids to play next step
    #     self.current_step = len(self.steps)
    #
    #     # remove all incoming events but keep steps
    #     self.
    #     self.remove_incoming_events()

    @event('goto_step')
    def on_goto(self, goto_id):
        # stop current step
        self.steps[min(self.current_step, len(self.steps) - 1)].end(
            win=False,
            start_next_step=False
        )

        # remove all programmed events that have been set in
        # the previous branch of the game
        self.event_manager.remove_all_events()

        # goto desired step
        self.current_step = None
        # iterate over steps to find the one with
        # corresponding ID
        for i, step in enumerate(self.steps):
            if step.id == goto_id:
                # take i - 1 since will call
                # "start_next_step()" right after that
                # we thus stick to the previous step to
                # start the next (desired) one
                self.current_step = i - 1
                break
        if self.current_step is None:
            raise KeyError(f'goto_id "{goto_id}" does not exist !')
        # and start the next step, which
        # basically increment "current_step"
        # and starts the new step
        self.start_next_step()

    @event("end_game")
    def on_end_game(self, show_end_screen=True, save_score=True):
        # # remove all incoming events
        # self.event_manager.remove_all_events()

        # call the end game
        self.end_game(
            show_end_screen=show_end_screen,
            save_score=save_score
        )

    @event('collision')
    def on_collision(self):
        # The first impact function
        self.engine.taskMgr.add(self.shuttle.impact, name="shake shuttle")
        # self.engine.state_manager.collision_occurred.set_value(True)
        self.engine.state_manager.collision_occurred.set_value(True)
        self.engine.sound_manager.stop_bips()

        self.event_manager.add_event(
            time=0.5,
            method=lambda *args: self.engine.sound_manager.play_sfx(
                'gaz_leak',
                loop=True,
                volume=0.5
            )
        )
        self.engine.sound_manager.stop("start_music")

        # leds
        self.engine.state_manager.defficience_moteur1.set_led_on()
        self.engine.state_manager.defficience_moteur2.set_led_on()
        self.engine.state_manager.defficience_moteur3.set_led_on()
        self.engine.state_manager.problem0.set_led_on()
        self.engine.state_manager.problem1.set_led_on()
        self.engine.state_manager.problem2.set_led_on()
        self.engine.state_manager.fuite_O2.set_led_on()
        self.engine.state_manager.alert0.set_led_on()
        self.engine.state_manager.alert1.set_led_on()

        self.engine.state_manager.antenne_com.set_led_off()

        def detection(_=None):
            kwargs = dict(
                silent=True,
                update_power=False,
                update_scenario=False
            )

            # energy problems !
            self.engine.state_manager.pilote_automatique1.set_value(False, **kwargs)
            self.engine.state_manager.pilote_automatique2.set_value(False, **kwargs)
            self.engine.state_manager.correction_direction.set_value(False, **kwargs)
            self.engine.state_manager.correction_roulis.set_value(False, **kwargs)
            self.engine.state_manager.correction_stabilisation.set_value(False, **kwargs)

            self.engine.state_manager.moteur1.set_value(False, **kwargs)
            self.engine.state_manager.moteur2.set_value(False, **kwargs)
            self.engine.state_manager.moteur3.set_value(False, **kwargs)
            self.engine.state_manager.offset_ps_x.set_value(2, **kwargs)
            self.engine.state_manager.offset_ps_y.set_value(1, **kwargs)

            self.engine.state_manager.main_O2.set_value(0.1, **kwargs)

            # finally, update power
            self.engine.update_power()

        self.event_manager.add_event(
            time=1,
            method=detection
        )

    @event('asteroid')
    def on_asteroid(self):
        self.engine.asteroid.spawn()

    # elementary functions
    @event('shuttle_look_at')
    def on_shuttle_look_at(self, time=5.0, x=0.0, y=0.0, z=0.0):
        if time == 0.0:
            self.engine.shuttle.look_at(LVector3f(x, y, z))
        else:
            self.engine.shuttle.dynamic_look_at(LVector3f(x, y, z), time=time)

    # @event('shuttle_pos')
    # def on_shuttle_pos(self, x=0.0, y=0.0, z=0.0):
    #     self.engine.shuttle.set_pos(LVector3f(x, y, z))

    @event('shuttle_goto')
    def on_shuttle_goto(self, x=0.0, y=0.0, z=0.0, power=1.0):
        self.engine.shuttle.dynamic_goto(LVector3f(x, y, z), power=power)

    # @event('shuttle_stop')
    # def on_shuttle_stop(self, play_sound=True):
    #     self.engine.shuttle.stop(play_sound)

    # @event('shuttle_goto_station')
    # def on_shuttle_goto_station(self, power=1.0):
    #     pos, hpr = self.engine.space_craft.get_connection_pos_and_hpr()
    #
    #     def _end(t=None):
    #         self.engine.shuttle.dynamic_goto_hpr(hpr, time=7)
    #
    #     self.engine.shuttle.dynamic_goto(pos, power=power, t_spin=7.0, end_func=_end)

    @event('keyboard')
    def on_keyboard(self, key):
        send_event('info',
                   icon='hourglass',
                   title='Keyboard',
                   text=f'Pour lancer le jeu, appuyez sur: \n\n\t"{key}"',
                   duration=None,
                   text_size=0.06,
                   close_on_enter=False
                   )
        self.accept_once(key, self.engine.gui.close_window_and_go)

    @event('wait')
    def on_wait(self):
        pass

    @event('group')
    def on_group(self):
        pass

    # @event('boost')
    # def on_boost(self, direction=None, power=1.0):
    #     self.engine.shuttle.boost(direction, power)

    @event('play_music')
    def on_play_music(self, name, loop=True):
        self.engine.sound_manager.play_music(name, loop=loop)

    @event('stop_music')
    def on_stop_music(self):
        self.engine.sound_manager.stop_music()

    @event('play_sound')
    def on_play_sound(self, name=None, volume=None, loop=False):
        Logger.info(f'playing SFX {name}')
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
        self.engine.state_manager.reset()
        # self.engine.hardware.init_states()

    @event('led_on')
    def on_led_on(self, led):
        self.engine.state_manager.get_state(led).set_led_on()

    @event('led_off')
    def on_led_off(self, led):
        self.engine.state_manager.get_state(led).set_led_off()

    # def remove_incoming_events(self) -> None:
    #     """
    #     Remove all incoming events, ignoring steps
    #     """
    #     if hasattr(self, '_taskList'):
    #         # _taskList attribute is dynamically set when adding a task
    #         for task in list(self._taskList.values()):
    #             if not task.get_name().startswith('event'):
    #                 Logger.info(f'removing task "{task.get_name()}"')
    #                 self.remove_task(task)
    #             else:
    #                 Logger.info(f'keeping task "{task.get_name()}"')

    def pause(self) -> None:
        """
        Pauses the game, removing all incoming tasks
        """
        self.event_manager.pause()

    def resume(self) -> None:
        """
        Resume the game paused with :func:`pause`
        """
        self.event_manager.resume()

    def fulfill_current_step(self):
        """
        Fulfill the current step and starts the next one
        """
        # stop current sounds
        self.engine.sound_manager.stop_sfx()
        # and start new step
        self.steps[self.current_step].force_fulfill()

    def start_next_step(self):
        """
        Starts the next step.

        .. note:: this **does not** fulfill the current one

        See Also
            :func:`fulfill_current_step`
        """
        Logger.info('')
        Logger.info('='*10)
        Logger.info(f'starting next step {self.current_step} -> {self.current_step+1}')
        Logger.info('='*10)
        # curframe = inspect.currentframe()
        # calframe = inspect.getouterframes(curframe, 2)
        # Logger.info(f'called by {calframe[1][3]}')
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
            # Logger.info('updating scenario ...')
            step = self.steps[self.current_step]
            if step.can_end_step(wait_end_if_fulfilled=wait_end_if_fulfilled):
                # Logger.info('ending current step')
                step.end(True)
            # else:
                # Logger.info('current step is not fulfilled yet. Continuing')

