import os
import re

from direct.gui.DirectEntry import DirectEntry

from engine.gui.windows.window import Window


class TerminalWindow(Window):
    """
    A custom widget representing a gauge
    """
    def __init__(self,
                 gui_engine,
                 size_x=1.0,
                 size_y=0.8,
                 title=None,
                 focus=False,
                 **kwargs):
        super(TerminalWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title=title, text=None, **kwargs)
        self._line_arg = "[/root]:"

        self.num_lines = int((size_y - 5 * self._widget_pad - self._text_scale) / self._text_scale)
        self._entry = DirectEntry(
            width=(self._size[0] - 2 * self._widget_pad) / self._text_scale,
            numLines=self.num_lines,
            text_fg=self.color('light'),
            overflow=True,
            text_font=self._gui_engine.engine.loader.load_font(os.path.join(self._gui_engine.engine("font_path"),
                                                                            'UbuntuMono-B.ttf')),
            command=self.process,
            frameColor=self.color('terminal_bg'),
            pos=(- 0.5 * size_x + self._widget_pad, 0, 0.5 * size_y - 4 * self._widget_pad - self._text_scale),
            parent=self._widget,
            scale=self._text_scale,
            focus=False,
            focusInCommand=self._on_focus,
        )
        self._commands = {'test': 'checking power ... \1green\1OK\2\n'
                                  'check A1 ... \1green\1OK\2\n'
                                  'check A2 ... \1red\1ERROR\2'}

        self._entry.accept(self._entry.guiItem.getEraseEvent(), self._remove_char)
        self.set_focus(focus)

    def get_entry_text(self, plain=True):
        """
        Get the entry text

        Returns:
            a :obj:`str` containing the text if the entry exists
        """
        if self._entry is not None:
            return self._entry.get(plain=plain)

    def _get_current_line(self):
        """
        Get the last line displayed on the terminal

        Returns:
            a :obj:`str`
        """
        return self.get_entry_text().split('\n')[-1]

    def _on_focus(self):
        """
        Function called when focus is on
        """
        self.add_line(self._line_arg + ' ')

    def process(self, *args):
        """
        Function called when enter is pressed
        """
        if self._get_current_line().startswith(self._line_arg):
            line_args = re.findall(r"(\w+)", self._get_current_line().replace(self._line_arg, ''))
            command = line_args[0] if len(line_args) > 0 else None
            if command in self._commands.keys():
                self.add_text(self._commands[command], time_between_lines=0.5)
            elif command is not None:
                self.add_text('\1red\1unknown command "{}"\2'.format(command))
            else:
                self.add_text('\1red\1please enter a valid command\2')

    def set_focus(self, focus):
        """
        Set the focus on this window

        Args:
            focus (bool): the focus
        """
        self._entry['focus'] = focus
        self._entry.setFocus()

    def _remove_char(self, *args):
        """
        Function called when a char is removed
        """
        if self._get_current_line() == self._line_arg:
            self._entry.enterText(self.get_entry_text(False) + ' ')

    def add_line(self, line, dt=0.0):
        if dt > 0.0:
            self._entry.do_method_later(dt, lambda x: self.add_line(x, dt=0.0),
                                        name='delayed_add_line',
                                        extraArgs=[line])
        else:
            lines = self.get_entry_text(False).split('\n') + self._gui_engine.process_text(line).split('\n')
            # check length
            if len(lines) >= self._entry['numLines'] - 1:
                self.set_entry_text('\n'.join(lines[len(lines) - self._entry['numLines'] + 1:]))
            else:
                self.set_entry_text('\n'.join(lines))

    def add_text(self, text, give_focus=True, time_between_lines=0.0):
        """
        Display text on the terminal

        Args:
            text (str): the text to display
            give_focus (bool): if the focus should be given after text
            time_between_lines (float): the time to wait between each line is displayed (in seconds)
        """
        # remove focus
        self.set_focus(False)
        text = self._gui_engine.process_text(text)
        for count, line in enumerate(text.split('\n')):
            self.add_line(line=line, dt=(count + 1) * time_between_lines)
        if time_between_lines > 0.0:
            self._entry.do_method_later((len(text.split('\n')) + 1) * time_between_lines + 0.1,
                                        self.set_focus,
                                        'terminal focus',
                                        extraArgs=[give_focus])
        else:
            self.set_focus(give_focus)
