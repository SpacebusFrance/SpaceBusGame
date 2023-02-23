from engine.utils.event_handler import send_event
from engine.utils.logger import Logger


class Event:
    """
    Class representing a single event that is played outside current steps
    """
    step_counter = 0

    def __init__(self, engine, id,
                 action="",
                 args_dict=None,
                 ):
        """
        Instantiate a :class:`Step`

        Args:
            engine (class:`GameEngine`): the main engine
            action (str): the name of the event to call in :func:`Scenario.event`
        """
        self.shuttle = engine.shuttle
        self.engine = engine
        self.scenario = engine.scenario
        self.sound_player = engine.sound_manager
        self.name = action
        assert id.startswith('event'), f'"event" names should start as "event...", not {id}'
        self.id = id

        self._event_kwargs = args_dict if args_dict is not None else dict()
        self._event_name = action

    def start(self, _=None):
        """
        Start this step
        """
        Logger.print('\n[{0}] starting event {1}'.format(self.engine.get_time(True), self.name),
                     color='green')

        if self._event_name is not None:
            send_event(self._event_name, **self._event_kwargs)
