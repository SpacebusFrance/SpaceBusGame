from direct.gui.DirectEntry import DirectEntry
from panda3d.core import TransparencyAttrib

from engine.gui.widgets.base_widget import BaseWidget


class Entry(BaseWidget):
    def __init__(self,
                 gui_engine,
                 size_x,
                 size_y,
                 hint='',
                 on_enter=None,
                 extra_args=None,
                 text_width=10):
        super(Entry, self).__init__(gui_engine)

        self._text_tooltip = hint
        self._widget = DirectEntry(initialText=self._text_tooltip,
                                   focusInCommand=self.gain_focus,
                                   width=text_width,
                                   focusOutCommand=self.loose_focus,
                                   command=on_enter if on_enter is not None
                                   else self.loose_focus,
                                   extraArgs=extra_args if extra_args is not None else [],
                                   frameColor=(0.3, 0.3, 0.3, 1.0),
                                   )
        self._widget.enterText('\1hint\1' + self._text_tooltip + '\2')

        self.setTransparency(TransparencyAttrib.MAlpha)
        self.initialiseoptions(Entry)

        # correct size
        sy = size_y / self._widget.getHeight()
        sx = sy * self._widget.getWidth()
        width = text_width * size_x / sx
        self._widget.set_scale(sy)
        self._widget['width'] = width
        self._widget.updateWidth()
        self.resetFrameSize()

    def get_text(self):
        return self._widget.get(plain=True)

    def gain_focus(self, reset=True):
        """
        Clear the text
        """
        self._widget['focus'] = 1
        if reset:
            self._widget.enterText('')
            self._widget.onscreenText.textNode.set_text_color(self._text_color)

    def loose_focus(self, _=None, reset=True):
        """
        Loose focus
        """
        if reset:
            self._widget.enterText('\1hint\1' + self._text_tooltip + '\2')
        self._widget['focus'] = 0

