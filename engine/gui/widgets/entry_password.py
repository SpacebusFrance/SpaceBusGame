from direct.gui.DirectEntry import DirectEntry
from panda3d.core import TransparencyAttrib

from engine.gui.widgets.base_widget import BaseWidget


class EntryPassword(BaseWidget):
    def __init__(self,
                 gui_engine,
                 size_x,
                 size_y,
                 password,
                 hint='',
                 on_ok=None,
                 text_width=10,
                 **kwargs):
        super(EntryPassword, self).__init__(gui_engine)

        self._text_tooltip = hint
        self._password = password
        self._on_ok = on_ok
        self._widget = DirectEntry(initialText=self._text_tooltip,
                                   focusInCommand=self.gain_focus,
                                   width=text_width,
                                   focusOutCommand=self.loose_focus,
                                   command=self.check,
                                   **kwargs
                                   )
        self._widget.enterText('\1hint\1' + self._text_tooltip + '\2')
        self.setTransparency(TransparencyAttrib.MAlpha)

        # correct size
        sy = size_y / self._widget.getHeight()
        sx = sy * self._widget.getWidth()
        width = text_width * size_x / sx
        self._widget.set_scale(sy)
        self._widget['width'] = width
        self._widget.updateWidth()
        self.resetFrameSize()

    def check(self):
        """
        Check if the password is correct
        """
        if self.get_text() == self._password:
            self._gui_engine.sound_manager.play('ok')
            self._on_ok()
        else:
            self._gui_engine.sound_manager.play('wrong')
        self._widget.enterText('')

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
