from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from engine.gui.main_screens.main_screen import MainScreen
from engine.gui.windows.chrono_window import ChronoWindow
from engine.gui.windows.gauge_window import GaugeWindow
from engine.gui.windows.terminal_window import TerminalWindow
from engine.gui.windows.window import Window


class Screen2(MainScreen):
    """
    Main screen for new scenario
    """
    def __init__(self, gui_engine, *args, **kwargs):
        super(Screen2, self).__init__(gui_engine, *args, **kwargs)
        self._terminal = None
        self._chrono = None

    def make(self):
        """
        Build the screen
        """
        self._build_chrono()
        self._build_terminal()
        # # # self._build_gauge()

    def notify_event(self, event, **kwargs):
        """
        Notify an event
        """
        event = event.lower().strip()
        if event == 'terminal-show':
            print(kwargs)
            self._terminal.add_text(kwargs.get('text', '$no_text$'),
                                    give_focus=kwargs.get('focus', False),
                                    time_between_lines=kwargs.get('dt', 0.0))
        elif event == 'terminal-focus':
            self._terminal.set_focus(kwargs.get('focus', None))
        elif event == 'start-chrono':
            if 'time' in kwargs:
                self._chrono.set_time(kwargs['time'])
            self._chrono.start()
        elif event == 'stop-chrono':
            self._chrono.stop()
        elif event == 'reset-chrono':
            self._chrono.reset(time=kwargs.get('time', None))

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
