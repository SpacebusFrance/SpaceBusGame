import os

from direct.gui.DirectButton import DirectButton
from direct.gui.DirectGuiGlobals import FLAT, NORMAL, ENTER, EXIT
from panda3d.core import TransparencyAttrib, LVector3f, TextNode, LVector2f

from engine.gui.widgets.base_widget import BaseWidget


class CheckBox(BaseWidget):
    def __init__(self,
                 gui_engine,
                 scale,
                 value=True,
                 **kwargs):
        super(CheckBox, self).__init__(gui_engine, shadow_scale=0.0)
        self._is_selected = False
        self._value = value
        self._im_on = os.path.join(self._gui_engine.engine('icon_path'), 'checkbox_on.png')
        self._im_off = os.path.join(self._gui_engine.engine('icon_path'), 'checkbox_off.png')

        self._widget = DirectButton(image=self._im_on if value else self._im_off,
                                    image_scale=scale,
                                    # color=(0, 0, 0, 1),
                                    frameColor=(0, 0, 0, 0),
                                    relief=FLAT,
                                    command=self.set_value,
                                    )

        self._widget['state'] = NORMAL
        self._widget.bind(ENTER, self.select)
        self._widget.bind(EXIT, self.un_select)

        self._widget.setTransparency(TransparencyAttrib.MAlpha)
        # self.set_size(size_x, size_y)

    def set_value(self, value=None):
        self._value = not self._value if value is None else value
        if self._value:
            self._widget.setImage(self._im_on)
        else:
            self._widget.setImage(self._im_off)

    def get(self, _=None):
        return self._value

    def select(self, *_):
        """
        Select the button and accept 'enter' as a click
        """
        if BaseWidget._selected_button != self and BaseWidget._selected_button is not None:
            BaseWidget._selected_button.un_select()
        BaseWidget._selected_button = self

        self._widget.set_color_scale(1.3)
        self._is_selected = True
        if callable(self._widget['command']):
            self._widget.accept('enter', self._widget['command'], extraArgs=self._widget['extraArgs'])

    def un_select(self, *_):
        """
        Unselect the button
        """
        BaseWidget._selected_button = None
        if not self._widget.is_empty():
            self._widget.set_color_scale(1.0)
            self._is_selected = False
            self._widget.ignore('enter')

    # def set_size(self, size_x, size_y):
    #     # now set the correct size for the frame
    #     self._widget['frameSize'] = (- 0.5 * size_x,
    #                                  0.5 * size_x,
    #                                  - 0.5 * size_y,
    #                                  0.5 * size_y)
    #     # self._widget['frameColor'] = color
    #     self.resetFrameSize()
    #     self.set_shadow()

    def set_on_click(self, func, extra_args=None):
        self._widget['command'] = func
        self._widget['extraArgs'] = [] if extra_args is None else extra_args