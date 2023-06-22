import os

from direct.gui.DirectEntry import DirectEntry
from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TransparencyAttrib, TextNode, CardMaker, Vec3

from engine.gui.widgets.base_widget import BaseWidget


class Window(BaseWidget):
    """
    A custom widget representing a 2D window on the screen with an optional title and custom buttons. This window
    can be moved.
    """
    def __init__(self,
                 gui_engine,
                 color='dark-window',
                 life_time=-1.0,
                 size_x=1.0,
                 size_y=0.8,
                 title=None,
                 text=None,
                 pos=None,
                 on_enter=None,
                 text_color='light',
                 text_size=0.05,
                 text_align=TextNode.ALeft,
                 password=None,
                 on_password_find=None,
                 on_password_fail=None,
                 on_entry_add=None,
                 on_entry_delete=None,
                 entry_hint='',
                 entry_width=0.8,
                 icon=None,
                 icon_size=.05,
                 focus=1,
                 hide_password=False,
                 shadow=True,
                 background_color=(0.0, 0.0, 0.0, 0.7),
                 **kwargs):
        super(Window, self).__init__(gui_engine)

        self._background = None
        if background_color is not None:
            ar = self._gui_engine.engine.get_option('screen_resolution')[0] / self._gui_engine.engine.get_option('screen_resolution')[1]
            cm = CardMaker('back')
            cm.set_color(self.color(background_color) if isinstance(background_color, str) else background_color)
            cm.set_frame(-ar, ar, -1.0, 1.0)
            self._background = self._gui_engine.screen.attach_new_node(cm.generate())
            self._background.setTransparency(TransparencyAttrib.MAlpha)

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

        self._widget_pad = 0.03
        self._text_scale = text_size

        if title is not None:
            OnscreenText(text='\1title\1{}\2'.format(title.upper()),
                         align=TextNode.ALeft,
                         pos=(-0.5 * size_x + self._widget_pad, 0.5 * size_y - self._widget_pad - self._text_scale),
                         scale=self._text_scale,
                         parent=self._widget)

        self._text = None
        if text is not None:
            self._text = OnscreenText(text=text,
                                      fg=self.color(text_color),
                                      wordwrap=size_x / self._text_scale * 0.9,
                                      align=text_align,
                                      pos=(-0.5 * size_x + self._widget_pad if text_align == TextNode.ALeft else
                                           0.5 * size_x - self._widget_pad,
                                           0.5 * size_y - 2. * (self._widget_pad + self._text_scale) - self._widget_pad),
                                      scale=self._text_scale,
                                      parent=self._widget)

        self._text_tooltip = None
        self._entry = None
        self._on_password_find = on_password_find
        self._on_password_fail = on_password_fail
        self._password = password

        if password is not None:
            text_width = 10
            self._text_tooltip = entry_hint
            self._entry = DirectEntry(
                obscured=hide_password,
                command=self.check,
                focusInCommand=self._on_focus,
                width=text_width,
                focusOutCommand=self._off_focus,
                frameColor=self.color('darker'),
                text_fg=self.color(text_color),
                parent=self._widget,
                scale=self._text_scale,
                focus=focus,
                pos=(-0.5 * size_x + 0.5 * (1 - entry_width) * size_x, -1.0, - 0.5 * size_y + 2.0 * self._widget_pad + self._text_scale),
            )
            # correct size
            self._entry['width'] = text_width * entry_width / (self._entry.getWidth() * self._entry.getScale().x)
            self._entry.updateWidth()
            self._entry.resetFrameSize()

            self._entry.enterText('\1hint\1{}\2'.format(self._text_tooltip))
            self._entry.setTransparency(TransparencyAttrib.MAlpha)

            if on_entry_add is not None:
                self._entry.accept(self._entry.guiItem.getTypeEvent(),
                                   lambda *args: on_entry_add(self.get_entry_text()))
            if on_entry_delete is not None:
                self._entry.accept(self._entry.guiItem.getEraseEvent(),
                                   lambda *args: on_entry_delete(self.get_entry_text()))

            self._widget.ignore_all()
        elif callable(on_enter):
            if life_time is not None:
                # accept on_enter at most 0.05 secs after (to avoid event conflicts)
                self._widget.do_method_later(min(0.05, 0.95 * life_time),
                                             lambda task: self._widget.accept_once('enter', on_enter, extraArgs=[self]),
                                             'accepting')
            else:
                self._widget.accept_once('enter', on_enter, extraArgs=[self])
            OnscreenText(scale=0.05, parent=self._widget,
                         pos=(0, -0.5 * size_y - 2 * self._widget_pad),
                         text=self._gui_engine.process_text('$window_enter_to_close$'),
                         fg=(1.0, 0.8, 0.7, 0.6)
                         )
        if icon is not None:
            im = OnscreenImage(image=os.path.join(self._gui_engine.engine.get_option('icon_path'), '{}.png'.format(icon)),
                               scale=icon_size,
                               pos=(0.5 * self._size[0] - icon_size - self._widget_pad, 0.0,
                                    0.5 * self._size[1] - icon_size - self._widget_pad),
                               parent=self._widget)
            if icon == 'load_spinner':
                im.hprInterval(2.0, Vec3(0, 0, 360)).loop()

        if life_time is not None and life_time > 0.0:
            self._widget.doMethodLater(life_time, lambda *args: self.destroy(), 'remove_window')
        if shadow:
            self.set_shadow()

        self._gui_engine.engine.sound_manager.play_sfx('window_open')

    def get_node(self):
        return self._widget

    def destroy(self):
        if self._background is not None:
            self._background.remove_node()
        self._widget.ignore_all()
        self._widget.remove_all_tasks()
        super().destroy()

    def check(self, entry_text=None):
        """
        Check if the password is correct
        """
        if entry_text.lower() == self._password.lower():
            self._gui_engine.engine.sound_manager.play_sfx('ok')
            if callable(self._on_password_find):
                self._on_password_find(self)
            else:
                self.remove_node()
        else:
            self._gui_engine.engine.sound_manager.play_sfx('wrong')
            if callable(self._on_password_fail):
                self._on_password_fail()
            else:
                # try again
                self.gain_focus()

    def get_entry_text(self):
        """
        Get the entry text

        Returns:
            a :obj:`str` containing the text if the entry exists
        """
        if self._entry is not None:
            return self._entry.get(plain=True)

    def set_entry_text(self, text):
        """
        Set the entry text

        Args:
            text (str): the text to set
        """
        if self._entry is not None:
            self._entry.enterText(text)

    def _on_focus(self):
        """
        Called when focus is ON
        """
        self._entry.enterText('')
        self._entry.onscreenText.textNode.set_text_color(self.color('light'))

    def _off_focus(self):
        """
        Called when focus is OFF
        """
        self._entry.enterText('\1hint\1' + self._text_tooltip + '\2')

    def gain_focus(self):
        """
        Clear the text and gain focus
        """
        self._entry['focus'] = 1
        self._entry.setFocus()

    def loose_focus(self, _=None):
        """
        Loose focus
        """
        self._entry['focus'] = 0
        self._entry.setFocus()

    def update_text(self, new_text):
        """
        Update the text to display

        Args:
            new_text (str): the new text to set
        """
        if self._text is not None:
            self._text.setText(new_text)
