import inspect
from typing import List

from engine.utils.event_handler import send_event
from engine.utils.logger import Logger


class ScenarioStep:
    """
    Class representing one step in the scenario.
    """
    step_counter = 0

    def __init__(
            self,
            engine,
            id,
            end_conditions=None,
            action="",
            duration=None,
            delay=None,
            blocking=True,
            args_dict=None,
            win_sound=None,
            loose_sound=None,
            fulfill_if_lost=False,
            hint_sound=None,
            hint_time=None
    ):
        """
        Instantiate a :class:`Step`

        Args:
            engine (class:`GameEngine`): the main _engine
            end_conditions (:obj:`dict`, optional): define the conditions to fulfill to end this step. Keys of the
                dictionary should be *game states* (both *hard* or *soft*) and values can be
                    - a single value : in this case, the state must equal the value to fulfill the condition
                    - a tuple with two elements : in this case, the state value must lie in the range of these values
            action (str): the name of the event to call in :func:`Scenario.event`
            duration (:obj:`float`, optional): if not :code:`None`, specifies the time in seconds from the starting of
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
        self.engine = engine
        self.scenario = engine.scenario
        self.sound_player = engine.sound_manager
        self.name = action
        self.id = id

        self._next_step_started = False
        # self.counter = ScenarioStep.step_counter
        # ScenarioStep.step_counter += 1

        self._blocking = blocking
        self._hint_task = None
        self._hint_sound = hint_sound
        self._hint_time = hint_time
        self.duration = duration
        self._action_task = None
        self.delay = delay if delay is not None else 0.0

        self.constraints = end_conditions

        self._event_kwargs = args_dict if args_dict is not None else {}
        self._event_kwargs.update({'duration': self.duration})
        self._event_name = action
        self._end_task = None
        self._loose_sound = loose_sound
        self._win_sound = win_sound
        self._fulfill_if_lost = fulfill_if_lost

    def reset(self) -> None:
        """
        Reset this step. Remove incoming steps
        """
        self.kill()
        self._next_step_started = False

    def start(self) -> None:
        """
        Start this step
        """
        Logger.info('')
        Logger.info(f'starting step "{self.name}" (id "{self.id}", starts in {self.delay:.2f} seconds)')
        Logger.info(f'\t- blocking \t\t: {self._blocking}')
        Logger.info(f'\t- delay \t\t: {self.delay:.2f} seconds')
        Logger.info(f'\t- duration \t\t: {self.duration if self.duration is not None else "infinity"} seconds.')
        Logger.info(f'\t- conditions\t: {self.constraints}')
        Logger.info(f'\t- event name\t: {self._event_name}')
        Logger.info(f'\t- event args\t: {self._event_kwargs}')

        if self.constraints is None and self.duration is None and self._blocking:
            Logger.warning('this step has no end conditions nor max time')

        if self.duration is not None and self._blocking:
            # it is a blocking step with a duration
            # this duration can be either 0.0 or a positive number.
            # If we are here it means that either delay is set or
            # duration is > 0 and no end_conditions.
            # We stop this step in delay + durations seconds
            end_time = self.delay + self.duration
            self._end_task = self.scenario.event_manager.add_event(
                time=end_time,
                method=lambda *args: self.end(False)
            )

        if self._event_name is not None:
            # send the event in 'delay' seconds
            # possibly instantaneously if delay = 0
            if self.delay > 0:
                self._action_task = self.scenario.event_manager.add_event(
                    time=self.delay,
                    method=lambda *args: send_event(self._event_name, **self._event_kwargs)
                )
            else:
                send_event(self._event_name, **self._event_kwargs)

        if self._hint_sound is not None and self._hint_time is not None:
            # play some hint sfx in hint_time
            # if set
            self._hint_task = self.scenario.event_manager.add_event(
                time=self.delay + self._hint_time,
                method=lambda *args: self.engine.sound_manager.play_sfx(self._hint_sound)
            )

        if not self._blocking:
            # if we are here, it means that we are non-blocking.
            # We simply start the next step and avoid to start it
            # latter when some game-state is updated
            self._next_step_started = True
            self.scenario.start_next_step()

    def force_fulfill(self):
        """
        Fulfill this step. If there are wining conditions, these conditions will be forced
        """
        Logger.warning(f'fulfilling step {self.name}')

        if self.constraints is not None:
            for key, value in self.constraints.items():
                if self.engine.state_manager.get_state(key).get_value() != value:
                    Logger.warning(f'- forcing {key}={value}')
                    self.engine.state_manager.get_state(key).set_value(value, update_power=False)
        else:
            self.end(False)
        Logger.warning('- step forced')

    def can_end_step(self, wait_end_if_fulfilled=True):
        """
        Checks if the wining conditions of this step are fulfilled.

        Returns
            a :obj:`bool`
        """
        Logger.info(f'checking is step {self.name} can end')
        if self._next_step_started or not self._blocking:
            # This step has already been stopped
            # somewhere else (in start for example).
            # This call is likely to have been triggered
            # by `update_scenario`, triggered by some
            # game state update. Since we don't want to stop
            # current step, we simply return False
            Logger.info('-> Cannot end since already ended')
            return False
        if self.constraints is not None:
            for key in self.constraints:
                value = self.constraints[key]
                game_value = self.engine.state_manager.get_state(key).get_value()
                if value != game_value:
                    Logger.info('-> Cannot end since constrain not fulfilled')
                    return False
            return True
        if wait_end_if_fulfilled:
            res = self._end_task is None or not self.scenario.event_manager.is_event_alive(self._end_task)
            if res:
                Logger.info('-> Can end since task ended')
                return True
            else:
                Logger.info('-> Cannot end since task not ended')
                return False
        else:
            Logger.info('-> Can end task')
            return True

    @property
    def event_names(self) -> List:
        """
        get a list of all non-empty event names
        """
        names = [
            self._end_task,
            self._action_task,
            self._hint_task
        ]
        return [k for k in names if k is not None]

    def kill(self):
        """
        Kill the current step without fulfilling it. Remove all incoming events
        """
        # remove all tasks related to this step
        self.scenario.event_manager.remove_event(self._end_task)
        self.scenario.event_manager.remove_event(self._action_task)
        self.scenario.event_manager.remove_event(self._hint_task)

    def end(self, win, start_next_step: bool = True):
        """
        Ends the step and starts the next step.

        Args:
            win (bool): If :code:`True` or if the step is passive, the :code:`win_function` is called (if it exists).
                Otherwise, the :code:`loose_function` is called.
            start_next_step (bool): Start next step at the end
        """
        if win:
            Logger.info('\t-> task complete')
            self.sound_player.play_sfx(self._win_sound)
        else:
            Logger.info('\t-> task ended')
            self.sound_player.play_sfx(self._loose_sound)
            if self._fulfill_if_lost:
                self.force_fulfill()

        # removing tasks
        self.kill()

        # check that next step isn't started already
        if not self._next_step_started:
            Logger.info('-> There')
            self._next_step_started = True
            # tell the game that we stop current task
            send_event('current_step_end')

            if start_next_step:
                # starting the next step
                self.scenario.start_next_step()
