from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiGlobals import FLAT
from panda3d.core import TransparencyAttrib, LVector3f, TextNode, LVector2f

from direct.gui.DirectGuiGlobals import B1PRESS, B1RELEASE, NORMAL, ENTER, EXIT, DISABLED
from engine.gui.widgets.base_widget import BaseWidget


class Button(BaseWidget):

    def __init__(self,
                 gui_engine,
                 text,
                 size_x,
                 size_y,
                 color='button-color',
                 icon_left=True,
                 icon=None,
                 image_color=None,
                 on_click=None,
                 extra_args=None,
                 **kwargs):
        super().__init__(gui_engine, shadow_scale=0.07, **kwargs)
        txt_color = self.color(kwargs.pop('text_color', 'light'))
        self._is_selected = False

        self._widget = DirectButton(text=text,
                                    image=icon,
                                    image_scale=kwargs.pop('image_scale', 0.04),
                                    text_fg=txt_color,
                                    text_scale=kwargs.pop('text_scale', 0.07),
                                    text_align=TextNode.A_left if icon_left else TextNode.A_right,
                                    color=self.color(color),
                                    relief=FLAT,
                                    command=on_click,
                                    extraArgs=extra_args if extra_args is not None else [],
                                    )

        self.setTransparency(TransparencyAttrib.MAlpha)

        # set the position of the image
        if icon is not None:
            tb = self.component('text0').getTightBounds()
            cx, cy = self.getCenter()
            self._widget['text_pos'] = (0.1 - cx if icon_left else -0.1 - cx,
                                        - 0.5 * (tb[1][2] + tb[0][2]) - 0.5 * self.getHeight())
            self._widget['image_pos'] = self._widget['image_pos'] + LVector3f(-cx, 0, - cy - 0.5 * self.getHeight())
            if image_color is not None:
                self._widget['image_color'] = txt_color if image_color == 'text_color' else image_color
            self.resetFrameSize()

        self.set_size(size_x, size_y)

        self._widget['state'] = NORMAL
        self._widget.bind(ENTER, self.select)
        self._widget.bind(EXIT, self.un_select)
        self.initialiseoptions(Button)

    def select(self, *_):
        """
        Select the button and accept 'enter' as a click
        """
        self._widget.set_color_scale(2.0, 1.5, 1.8, 1.0)
        self._is_selected = True
        if BaseWidget._selected_button != self and BaseWidget._selected_button is not None:
            BaseWidget._selected_button.un_select()
        BaseWidget._selected_button = self
        if callable(self._widget['command']):
            self._widget.accept_once('enter', self._widget['command'], extraArgs=self._widget['extraArgs'])

    def un_select(self, *_):
        """
        Unselect the button
        """
        if not self._widget.is_empty():
            self._widget.clear_color_scale()
            self._is_selected = False
            self._widget.ignore('enter')
        BaseWidget._selected_button = None

    def set_size(self, size_x, size_y):
        # now set the correct size for the frame
        cx, cy = self.getCenter()
        self._widget['text_pos'] = LVector2f(self._widget['text_pos']) - LVector2f(cx, cy)
        # self._widget['image_pos'] = LVector3f(*self._widget['image_pos']) - LVector3f(cx, 0, cy)
        self._widget['frameSize'] = (- 0.5 * size_x,
                                     0.5 * size_x,
                                     - 0.5 * size_y,
                                     0.5 * size_y)
        # self._widget['frameColor'] = color
        # self.resetFrameSize()
        self.set_shadow()

    def set_on_click(self, func, extra_args=None):
        self._widget['command'] = func
        self._widget['extraArgs'] = [] if extra_args is None else extra_args
