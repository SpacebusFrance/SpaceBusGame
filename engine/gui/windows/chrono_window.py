import datetime
import re

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from engine.gui.windows.window import Window


class ChronoWindow(Window):
    """
    A custom widget representing a chronometer
    """
    def __init__(self,
                 gui_engine,
                 life_time=None,
                 size_x=1.0,
                 size_y=0.8,
                 on_done=None,
                 alert_time=10.0,
                 title=None,
                 text=None,
                 **kwargs):
        super(ChronoWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title=title, text=text, **kwargs)

        widget_pad = 0.05
        text_scale = 0.2

        self._alert = alert_time
        self._on_done = on_done
        self._origin_time = life_time
        self._time = life_time
        self._chrono = OnscreenText(text='',
                                    align=TextNode.ACenter,
                                    pos=(0.0, - 0.5 * size_y + 2.0 * widget_pad),
                                    scale=text_scale,
                                    parent=self._widget)

        self._update()

    def _update(self, task=None):
        if self._time is None:
            self._chrono.setText('\1{color}\1{time}\2'.format(color='chrono', time='.. : ..'))
        else:
            if self._time < 0.0:
                if callable(self._on_done):
                    self._on_done()
            else:
                self._chrono.setText('\1{color}\1{time}\2'.
                                     format(color='chrono' if self._time >= self._alert else 'chrono-alert',
                                            time=re.search(r'\d*:(\d*:\d*)',
                                                           str(datetime.timedelta(seconds=self._time))).group(1)))
                self._time -= 1.0
                self.doMethodLater(1.0, self._update, 'chrono_update')

    def set_time(self, time):
        """
        Set the time for the counter

        Args:
            time (float): the time in seconds
        """
        self._time = time
        self._chrono.setText('\1{color}\1{time}\2'.
                             format(color='chrono' if self._time >= self._alert else 'chrono-alert',
                                    time=re.search(r'\d*:(\d*:\d*)',
                                                   str(datetime.timedelta(seconds=self._time))).group(1)))

    def start(self):
        """
        Starts the counter
        """
        self._update()

    def stop(self):
        """
        Stops the counter
        """
        self.removeTask('chrono_update')

    def reset(self, time=None):
        """
        Reset to its original state

        .. note:: this does not start the counter, you must call :func:`start` explicitly

        Args:
            time (:obj:`float`, optional): if specified, set the time
        """
        self.stop()
        if time is not None:
            self._origin_time = time
        self._time = self._origin_time
