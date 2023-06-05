from engine.utils.event_handler import send_event
from engine.utils.logger import Logger


class Step:
    """
    Class representing one step in the scenario.
    """
    step_counter = 0

    def __init__(self, engine,
                 id,
                 end_conditions=None,
                 action="",
                 max_time=None,
                 delay=None,
                 args_dict=None,
                 win_sound=None,
                 loose_sound=None,
                 fulfill_if_lost=False,
                 hint_sound=None,
                 hint_time=None):
        """
        Instantiate a :class:`Step`

        Args:
            engine (class:`GameEngine`): the main _engine
            end_conditions (:obj:`dict`, optional): define the conditions to fulfill to end this step. Keys of the
                dictionary should be *game states* (both *hard* or *soft*) and values can be
                    - a single value : in this case, the state must equal the value to fulfill the condition
                    - a tuple with two elements : in this case, the state value must lie in the range of these values
            action (str): the name of the event to call in :func:`Scenario.event`
            max_time (:obj:`float`, optional): if not :code:`None`, specifies the time in seconds from the starting of
                the step when the task will be *lost*
            delay (:obj:`float`, optional): if specified, define the time between the call of this step and its
                effective start (in seconds)
            args_dict (:obj:`dict`, optional): optional arguments to send to the :func:`Scenario.event` call
            win_sound (:obj:`str`, optional): the name of the sound to play when the task is won
            loose_sound (:obj:`str`, optional): the name of the sound to play when the task is lost
            fulfill_if_lost (:obj:`bool`, optional): specifies if this task must be fulfilled if it is lost
            hint_sound (:obj:`str`, optional): the name of hint sound to play
            hint_time (:obj:`float`, optional): specifies the time (in seconds from the start of the task) when the
                :code:`hint_sound` sound should be played
        """
        self.shuttle = engine.shuttle
        self.engine = engine
        self.scenario = engine.scenario
        self.sound_player = engine.sound_manager
        self.name = action
        self.id = id
        self.counter = Step.step_counter
        Step.step_counter += 1

        self._hint_task = None
        self._hint_sound = hint_sound
        self._hint_time = hint_time
        self.t_max = max_time
        self._to_do_task = None
        self.t_start = delay if delay is not None else 0.0

        self.constraints = end_conditions

        self._event_kwargs = args_dict if args_dict is not None else {}
        self._event_kwargs.update({'duration': self.t_max})
        self._event_name = action
        self._loose_task = None
        self._loose_sound = loose_sound
        self._win_sound = win_sound
        self._fulfill_if_lost = fulfill_if_lost

    def start(self):
        """
        Start this step
        """
        Logger.print(f'\n[{self.engine.get_time(True)}] starting step "{self.name}" (id "{self.id}", '
                     f'n° {self.counter}, starts in {self.t_start:.2f} seconds',
                     color='blue')
        Logger.print(f'\t- time max \t\t: {self.t_max if self.t_max is not None else "infinity"} seconds.',
                     color='blue')
        Logger.print(f'\t- conditions\t: {self.constraints}', color='blue')

        if self.constraints is None and self.t_max is None:
            Logger.warning('this step has no end conditions nor max time')
        if self.t_max is not None:
            self._loose_task = self.scenario.doMethodLater(
                self.t_start + self.t_max,
                self.end,
                extraArgs=[False],
                name=self.name)
        if self._event_name is not None:
            if self.t_start > 0:
                self._to_do_task = self.scenario.doMethodLater(
                    self.t_start,
                    lambda *args: send_event(self._event_name, **self._event_kwargs),
                    name=self.name)
            else:
                send_event(self._event_name, **self._event_kwargs)
                # self.scenario.event(self._event_name, self._event_kwargs)
        if self._hint_sound is not None and self._hint_time is not None:
            self._hint_task = self.scenario.doMethodLater(
                self.t_start + self._hint_time,
                self.engine.sound_manager.play_sfx,
                name=self.name + "_hint")

    def force_fulfill(self):
        """
        Fulfill this step. If there are wining conditions, these conditions will be forced
        """
        Logger.warning('fulfilling step', self.name)

        if self.constraints is not None:
            for key, value in self.constraints.items():
                if self.engine.state_manager.get_state(key).get_value() != value:
                    Logger.warning(f'- forcing {key}={value}')
                    # if isinstance(value, list):
                    #     value = 0.5 * (value[1] + value[0])
                    self.engine.state_manager.get_state(key).set_value(value, update_power=False)
                # if not self.engine.update_hard_state(key, value):
                #     self.engine.update_soft_state(key, value, force_power=True)
        else:
            self.end(False)
        Logger.warning('- step forced')

    def is_fulfilled(self, wait_end_if_fulfilled=True):
        """
        Checks if the wining conditions of this step are fulfilled.

        Returns
            a :obj:`bool`
        """
        if self.constraints is not None:
            for key in self.constraints:
                value = self.constraints[key]
                game_value = self.engine.state_manager.get_state(key).get_value()

                # if game_value is None:
                #     game_value = self.engine.get_hard_state(key)

                if isinstance(value, list):
                    if min(value) > game_value or game_value > max(value):
                        return False
                else:
                    if value != game_value:
                        return False
            return True
        if wait_end_if_fulfilled:
            return self._loose_task is None or not self._loose_task.is_alive()
        else:
            return True

    def kill(self):
        """
        Kill the current step without fulfilling it
        """
        # removing the loose task
        if self._loose_task is not None:
            self.scenario.remove_task(self._loose_task)
        if self._to_do_task is not None:
            self.scenario.remove_task(self._to_do_task)
        if self._hint_task is not None:
            self.scenario.remove_task(self._hint_task)

    def end(self, win):
        """
        Ends the step and starts the next step.

        Args:
            win (bool): If :code:`True` or if the step is passive, the :code:`win_function` is called (if it exists).
                Otherwise, the :code:`loose_function` is called.
        """
        if win:
            Logger.print('\t-> task complete', color='green')
            if self._win_sound is not None:
                self.sound_player.play_sfx(self._win_sound)
        else:
            Logger.print('\t-> task lost', color='red')
            if self._loose_sound is not None:
                self.sound_player.play_sfx(self._loose_sound)
            if self._fulfill_if_lost:
                self.force_fulfill()

        # removing tasks
        if self._loose_task is not None:
            self.scenario.remove_task(self._loose_task)
        if self._to_do_task is not None:
            self.scenario.remove_task(self._to_do_task)
        if self._hint_task is not None:
            self.scenario.remove_task(self._hint_task)

        # starting the next step
        self.scenario.start_next_step()
