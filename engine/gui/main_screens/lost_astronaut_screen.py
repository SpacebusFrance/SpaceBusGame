from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from engine.gui.main_screens.main_screen import MainScreen
from engine.gui.windows.chrono_window import ChronoWindow
from engine.gui.windows.gauge_window import GaugeWindow
from engine.gui.windows.terminal_window import TerminalWindow
from engine.gui.windows.window import Window
from engine.utils.event_handler import event


class LostAstronautScreen(MainScreen):
    """
    Main screen for new scenario
    """
    def __init__(self, gui_engine, *args, **kwargs):
        super().__init__(gui_engine, *args, **kwargs)
        self._terminal = None
        self._chrono = None

    def make(self):
        """
        Build the screen
        """
        self._build_chrono()
        self._build_terminal()
        # # # self._build_gauge()

    @event('terminal-show')
    def on_terminal_show(self, text='$no_text$', focus=False, dt=0.0):
        self._terminal.add_text(text, give_focus=focus, time_between_lines=dt)

    @event('terminal-focus')
    def on_terminal_focus(self, focus=None):
        self._terminal.set_focus(focus)

    @event('start_chrono')
    def on_start_chrono(self, time=None):
        if time is not None:
            self._chrono.set_time(time)
        self._chrono.start()

    @event('stop-chrono')
    def on_stop_chrono(self):
        self._chrono.stop()

    @event('reset-chrono')
    def on_reset_chrono(self, time=None):
        self._chrono.reset(time=time)

    # def notify_event(self, event, **kwargs):
    #     """
    #     Notify an event
    #     """
    #     event = event.lower().strip()
    #     if event == 'terminal-show':
    #         self._terminal.add_text(kwargs.get('text', '$no_text$'),
    #                                 give_focus=kwargs.get('focus', False),
    #                                 time_between_lines=kwargs.get('dt', 0.0))
    #     elif event == 'terminal-focus':
    #         self._terminal.set_focus(kwargs.get('focus', None))
    #     elif event == 'start-chrono':
    #         if 'time' in kwargs:
    #             self._chrono.set_time(kwargs['time'])
    #         self._chrono.start()
    #     elif event == 'stop-chrono':
    #         self._chrono.stop()
    #     elif event == 'reset-chrono':
    #         self._chrono.reset(time=kwargs.get('time', None))

    def _build_terminal(self):
        self._terminal = TerminalWindow(self.gui,
                                        title='$terminal_title$',
                                        text_size=0.05,
                                        size_x=2.2,
                                        size_y=1.5,
                                        pos=(-0.6, 0.1))

    def _build_chrono(self, size_x=0.8, size_y=1.0):
        self._chrono = ChronoWindow(self.gui,
                                    title=self.gui.process_text('$chrono_title$'),
                                    text=self.gui.process_text('$chrono_text$'),
                                    size_y=size_y,
                                    size_x=size_x,
                                    icon_size=self._icon_size,
                                    icon='hourglass',
                                    pos=(1.3, 0.0)
                                    )
