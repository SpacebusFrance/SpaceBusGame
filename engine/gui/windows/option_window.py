import os

from direct.gui.DirectCheckButton import DirectCheckButton
from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectGuiGlobals import FLAT
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TransparencyAttrib, TextNode

from engine.gui.widgets.base_widget import BaseWidget
from engine.gui.widgets.checkbox import CheckBox
from engine.gui.widgets.scrolled_frame import ScrolledFrame
from engine.utils.ini_parser import ParamUtils
from engine.utils.logger import Logger


class OptionWindow(BaseWidget):
    """
    A custom widget representing a 2D window on the screen with an optional title and custom buttons. This window
    can be moved.
    """
    def __init__(self,
                 gui_engine,
                 color=None,
                 life_time=-1.0,
                 size_x=1.5,
                 size_y=0.8,
                 title=None,
                 pos=None,
                 icon=None,
                 icon_size=.07,
                 size_button=0.15,
                 focus=1,
                 **kwargs):
        super(OptionWindow, self).__init__(gui_engine)

        # now create the node
        self._widget = DirectFrame(
            frameColor=self.color(color) if isinstance(color, str) else self.color('dark') if color is None else color,
            frameSize=(-.5 * size_x, .5 * size_x, -0.5 * size_y, 0.5 * size_y),
            parent=gui_engine.screen
        )

        if pos is not None:
            self.set_pos(pos[0], 0.0, pos[-1])

        self._size = (size_x, size_y)

        self.setTransparency(TransparencyAttrib.MAlpha)
        self._widget.initialiseoptions(DirectFrame)

        self._widget_pad = 0.05
        self._text_scale = 0.07

        self._scrolled = ScrolledFrame(self._gui_engine, size_x=size_x - 2 * self._widget_pad,
                                       size_y=size_y - 4 * self._widget_pad - self._text_scale - size_button)
        self._scrolled.reparent_to(self._widget)
        self._scrolled.set_pos(-0.5 * size_x + self._widget_pad, 0.0,
                               -0.5 * size_y + self._widget_pad + size_button)

        if title is not None:
            OnscreenText(text='\1title\1{}\2'.format(title.upper()),
                         align=TextNode.ALeft,
                         pos=(-0.5 * size_x + self._widget_pad, 0.5 * size_y - self._widget_pad - self._text_scale),
                         scale=self._text_scale,
                         parent=self._widget)

        if icon is not None:
            OnscreenImage(image=os.path.join(self._gui_engine.engine('icon_path'), '{}.png'.format(icon)),
                          scale=icon_size,
                          pos=(0.5 * self._size[0] - icon_size - self._widget_pad, 0.0,
                               0.5 * self._size[1] - icon_size - self._widget_pad),
                          parent=self._widget)

        if life_time > 0.0:
            self._gui_engine.doMethodLater(life_time,
                                           lambda *args: self.destroy(),
                                           name="window_lifetime")

        self._options = dict()
        self.set_shadow()

    def get_node(self):
        return self._widget

    def destroy(self):
        self._widget.ignore_all()
        self._widget.destroy()

    def add_option(self, name, value):
        self._text_scale = 0.06
        df = DirectFrame(
            frameColor=(0.0, 0.0, 0.0, 0.0),
            frameSize=(-.5 * self._size[0],
                       .5 * self._size[0],
                       - self._widget_pad,
                       self._widget_pad + self._text_scale)
        )
        OnscreenText(text=self._gui_engine.process_text('\1title\1 {}\2'.format(name)),
                     align=TextNode.ALeft,
                     scale=self._text_scale,
                     parent=df)
        if isinstance(value, bool):
            self._options[name] = CheckBox(self._gui_engine,
                                           scale=self._text_scale,
                                           value=value)
            self._options[name].reparent_to(df)
            self._options[name].set_pos(self._size[0] - self._widget_pad - 0.5 * self._text_scale * 8, 0,
                                        0.5 * self._widget_pad)
        else:
            self._options[name] = DirectEntry(
                initialText='{}'.format(value),
                width=8,
                text_fg=self.color('light'),
                overflow=True,
                # focusOutCommand=self._off_focus,
                frameColor=self.color('darker'),
                # text_fg=self.color(text_color),
                pos=(self._size[0] - self._widget_pad - self._text_scale * 8, 0, 0.0),
                parent=df,
                scale=self._text_scale
            )
        self._scrolled.add_item(df, rescale=True)

    def set_option(self, name, value):
        if name in self._options:
            if isinstance(self._options[name], DirectEntry):
                self._options[name].set('{}'.format(value))
            else:
                self._options[name].set_value(value)
        else:
            Logger.error('option {} does not exists !'.format(name))

    def get_option(self, name=None):
        """
        Get the casted value of the desired option

        Args:
            name (str): the name of the options to get. If set to ``None``, all values are returned in a dictionnary

        Returns:
            a single value if ``name`` is provided, else a ``dictionary``
        """
        if name is not None and name in self._options:
            return ParamUtils.smart_cast(self._options[name].get(True))
        elif name is None:
            return {key: ParamUtils.smart_cast(self._options[key].get(True)) for key in self._options}
        else:
            Logger.error('option {} does not exists !'.format(name))
