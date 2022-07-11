import datetime
import re

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from engine.gui.widgets.button import Button
from engine.gui.windows.window import Window


class ButtonWindow(Window):
    """
    A custom widget representing a chronometer
    """
    def __init__(self,
                 gui_engine,
                 size_x=1.0,
                 size_y=0.8,
                 title=None,
                 text=None,
                 **kwargs):
        super(ButtonWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title=title, text=text, **kwargs)

        widget_pad = 0.05
        text_scale = 0.2
        self._current_selected = 0
        self._buttons = list()
        self._widget.accept('arrow_down', self.select_next)
        self._widget.accept('arrow_up', self.select_previous)

    def select_button(self, num=0):
        """
        Select a button

        Args:
            num (int): the number of the button
        """
        num = min(len(self._buttons) - 1, max(0, num))
        self._buttons[self._current_selected].un_select()
        self._current_selected = num
        self._buttons[self._current_selected].select()

    def select_next(self):
        """
        Select next button
        """
        self._buttons[self._current_selected].un_select()
        self._current_selected += 1
        if self._current_selected >= len(self._buttons):
            self._current_selected = len(self._buttons) - 1
        self._buttons[self._current_selected].select()

    def select_previous(self):
        """
        Select previous button
        """
        self._buttons[self._current_selected].un_select()
        self._current_selected -= 1
        if self._current_selected < 0:
            self._current_selected = 0
        self._buttons[self._current_selected].select()

    def add_button(self, size_x, size_y, text, pos=None,on_select=None, extra_args=None, **kwargs):
        """
        """
        self._buttons.append(Button(self._gui_engine,
                                    text=self._gui_engine.process_text(text),
                                    size_x=size_x,
                                    size_y=size_y,
                                    on_click=on_select,
                                    extra_args=extra_args,
                                    **kwargs
                                    ))
        self._buttons[-1].reparent_to(self._widget)
        if pos is not None:
            self._buttons[-1].set_pos(pos)
