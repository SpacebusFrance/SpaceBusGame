import math
import os
import re
import pandas as pd
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import WindowProperties
from panda3d.core import PGTop

from engine.gui.main_screens.main_screen import MainScreen
from engine.gui.main_screens.got_to_mars_screen import GoToMarsScreen
from engine.gui.main_screens.lost_astronaut_screen import LostAstronautScreen
from engine.gui.utils import build_text_properties
from engine.gui.widgets.button import Button
from engine.gui.windows.button_window import ButtonWindow
from engine.gui.windows.end_window import EndWindow
from engine.gui.windows.option_window import OptionWindow
from engine.gui.windows.video_window import VideoWindow
from engine.gui.windows.window import Window
from engine.utils.event_handler import EventObject, event, send_event
from engine.utils.logger import Logger


class Gui(EventObject):
    """
    Class that represents the [old]ControlScreen that must be unlocked.
    Displayed on the control screen
    """
    colors = {
        'green': (0.2, 0.8, 0.1, 1.0),
        'red': (0.8, 0.2, 0.1, 1.0),
        'blue': (0.2, 0.2, 0.6, 1.0),
        'light': (0.9, 0.9, 0.9, 1.0),
        'golden': (0.9, 0.9, 0.43, 1.0),
        'black': (0.0, 0.0, 0.0, 1.0),
        'dark': (0.2, 0.2, 0.2, 1.0),
        'dark-blue': (0.1, 0.1, 0.2, 1.0),
        'dark-sp': (0.2, 0.2, 0.2, 0.7),
        'darker': (0.1, 0.1, 0.1, 1.0),
        'dark-window': (0.12, 0.12, 0.12, 1.0),
        'button-color': (0.15, 0.15, 0.15, 1.0),
        'background': (0.08, 0.08, 0.08, 1.0),
        'terminal_bg': (0.174, 0.036, 0.11, 1.0),
    }

    def __init__(self, engine):
        super().__init__()

        self.engine = engine
        self._current_window = None

        # build text properties
        build_text_properties(engine)

        self.image_path = self.engine("control_screen_image_path")

        # read text correspondence
        self._text_file = pd.read_csv(self.engine('text_file'), sep=';', index_col='key').fillna('NaN')
        self.screen = None

    def admin_screen(self):
        """
        Displays an admin screen, if password is correct, leads back to menu
        """
        self.engine.scenario.pause()

        def reset_game() -> None:
            # close admin window
            self._current_window.destroy()
            # resume game
            self.engine.scenario.resume()

        send_event('password',
                   title='Admin window',
                   text='Administrator password',
                   close_time=20,
                   password=self.engine('admin_password'),
                   hide_password=True,
                   on_password_fail=reset_game,
                   on_password_find=lambda *args: self.engine.reset_game(None, False),
                   )

    def end_screen(self, player_position=None, total_players=None, time_minutes=None, time_seconds=None):
        """
        Displays an end screen

        Args:
            player_position (int):
            player_time (float):
            total_players (int):
        """
        self.set_current_window(
            win=EndWindow,
            player_position=player_position,
            time_minutes=time_minutes,
            time_seconds=time_seconds,
            total_players=total_players,
            background_color=self.colors['black'],
        )

        self.accept_once('enter', self.reset)
        # buy default, reset menu after a certain game_time
        self.do_method_later(self.engine('end_game_reset_delay'), self.reset, name='menu_reset_task')

    def hide_cursor(self):
        # hide cursor
        props = WindowProperties()
        props.setCursorHidden(True)
        self.engine.win.requestProperties(props)

    def show_cursor(self):
        # show cursor
        props = WindowProperties()
        props.setCursorFilename(os.path.join(self.engine('image_path'), self.engine('cursor_file')))
        props.setCursorHidden(False)
        self.engine.win.requestProperties(props)

    def reset(self, show_menu=True):
        """
        Reset the gui and optionally display the main menu

        Args:
            show_menu (bool): specifies if the main menu should be displayed or not
        """
        Logger.title('GUI reset')
        self.ignore_all()
        self.remove_all_tasks()
        if self._current_window is not None and not self._current_window.is_empty():
            self._current_window.destroy()
        if show_menu:
            send_event('menu')

    def process_text(self, text, key='$'):
        """
        Process text for language support. Looks for every string matching **key**...**key**, e.g. `$...$` and replace
        it with the corresponding value

        Args:
            text (str): the text to process
            key (str): the string that defines words to replace

        Returns:
            a :obj:`str` with process text
        """
        for value in re.findall(r'[{key}](\S*)[{key}]'.format(key=key), text):
            try:
                new_value = self._text_file.loc[value, self.engine('lang')]
            except KeyError:
                new_value = 'NaN'
            if new_value == 'NaN':
                # can be either missing key or language
                Logger.error(f'missing text "{value}" for lang "{self.engine("lang")}"')
                new_value = f'!{value}!'
            text = text.replace('{key}{value}{key}'.format(key=key, value=value), new_value)
        return text.replace('\\1', '\1').replace('\\2', '\2').replace('\\n', "\n").replace('\\t', '\t')

    def set_current_window(self, win=Window, **kwargs):
        """
        Instantiate the current window

        Args:
            win (class): the class of the window,
            **kwargs: parameters to instantiate the window
        """
        if self._current_window is not None and not self._current_window.is_empty():
            self._current_window.destroy()
        if 'background_color' not in kwargs:
            kwargs['background_color'] = (0.0, 0.0, 0.0, 0.8)
        self._current_window = win(self, **kwargs)

    def close_window_and_go(self, *args):
        """
        Close the current window and run the next step

        Args:
            *args: ignored arguments
        """
        if self._current_window is not None and not self._current_window.is_empty():
            self._current_window.destroy()
            self._current_window = None
            # if the task is fulfilled, just kill it, no need to wait until its end
            self.engine.scenario.update_scenario(wait_end_if_fulfilled=False)

    def set_screen(self, cls=None):
        if self.screen is not None:
            self.screen.destroy()
        if cls is None:
            self.screen = MainScreen(self)
        else:
            self.screen = cls(self)
        self.screen.make()

    @event('set_screen')
    def on_set_screen(self, name=""):
        scenario_name = name.lower()

        if scenario_name in ['go_to_mars', 'gotomars']:
            self.set_screen(GoToMarsScreen)
        elif scenario_name in ['lost_astronaut', 'lostastronaut']:
            self.set_screen(LostAstronautScreen)
        else:
            self.set_screen(None)

    @event('current_step_end')
    def on_current_step_end(self):
        if self._current_window is not None and not self._current_window.is_empty():
            self._current_window.destroy()
            self._current_window = None

    @event('end_screen')
    def on_end_screen(self):
        self.end_screen()

    @event('info')
    def on_info(self, icon='chat', title='$info_title$', text='', duration=-1, close_on_enter=True, text_size=0.05,
                color='dark-window', **kwargs):
        self.set_current_window(
            icon=icon,
            size_x=1.2,
            size_y=0.9,
            title=self.process_text(title),
            text=self.process_text(text),
            life_time=duration,
            on_enter=self.close_window_and_go if close_on_enter else None,
            color=color,
            text_size=text_size,
            **kwargs
        )

    @event('password')
    def on_password(self, icon='caution', title='$password_title$', text='', text_size=0.05, duration=-1, password='', format=None,
                    on_password_find=None, color='dark-window', **kwargs):
        def format_target(x):
            x = x.replace('-', '')[:6]
            self._current_window.set_entry_text('-'.join([x[2 * i:2 * (i + 1)] for i in range(math.ceil(len(x) / 2))]))

        if format is not None:
            if format == 'target':
                kwargs['on_entry_add'] = format_target
                kwargs['on_entry_delete'] = format_target
            else:
                Logger.error('unknown text format {}'.format(format))

        self.set_current_window(
            icon=icon,
            title=self.process_text(title),
            text=self.process_text(text),
            life_time=duration,
            password=password,
            on_password_find=self.close_window_and_go if on_password_find is None else on_password_find,
            color=color,
            text_size=text_size,
            **kwargs
        )

    @event('video')
    def on_video(self, name, size_x=1.0, size_y=0.8, duration=-1, start=True, color='dark-window',
                 title='$video_title$', text='$video_text$', **kwargs):
        self.set_current_window(
            VideoWindow,
            color=color,
            video_path=name,
            size_x=size_x,
            size_y=size_y,
            life_time=duration,
            start=start,
            title=self.process_text(title),
            text=self.process_text(text),
            file_format='avi',
            **kwargs
        )

    @event('warning')
    def on_warning(self, icon='caution', duration=-1, color='dark-window', title='$warning_title$', text='',
                   close_on_enter=True, **kwargs):
        self.set_current_window(
            color=color,
            icon=icon,
            title=self.process_text(title),
            text=self.process_text(text),
            life_time=duration,
            on_enter=self.close_window_and_go if close_on_enter else None,
            **kwargs
        )

    @event('menu')
    def on_menu(self):
        self.show_menu()

    @event('update_state')
    def on_update_state(self, key=None):
        if self.screen is not None:
            self.screen.notify_update(key)

    @event('close_window')
    def on_close_window(self):
        self.close_window_and_go()

    def show_menu(self):
        """
        Display the main menu
        """
        # reset the screen, displays a black empty image
        self.set_screen()

        # play nice music
        self.engine.sound_manager.play_music('menu1')

        # show cursor
        self.show_cursor()

        def choose_game(*args):
            """
            function called when hitting "play" button
            """
            self.set_current_window(
                win=ButtonWindow,
                title=self.process_text('$game_title$'),
                text=self.process_text('$game_text$'),
                size_x=1.0,
                size_y=1.8,
            )
            files = [k for k in os.listdir(self.engine('scenario_path')) if k.endswith('.xml')]
            for i, game in enumerate(files):
                self._current_window.add_button(size_x=0.5,
                                                size_y=0.15,
                                                text='\1golden\1{}\2'.format(
                                                    game.replace('.xml', '').replace('_', ' ')),
                                                on_select=lambda x: self.engine.reset_game(scenario=x, start=True),
                                                extra_args=[game.replace('.xml', '')],
                                                pos=(0.0, 0.0, 0.4 - i * 0.18))

            self._current_window.add_button(size_x=0.5,
                                            size_y=0.15,
                                            text='\1golden\1back\2',
                                            color='blue',
                                            on_select=self.show_menu,
                                            pos=(0., 0.0, -0.7))

            self._current_window.select_button()

        def options(*args):
            """
            Function called when hitting "option" button
            """
            self.set_current_window(
                win=OptionWindow,
                title=self.process_text('$options_title$'),
                size_x=1.5,
                size_y=1.8,
            )
            for param in self.engine.params:
                if not isinstance(self.engine(param), str) or '/' not in self.engine(param):
                    self._current_window.add_option(param.replace('_', ' '), self.engine(param))
            # add buttons

            def save_options():
                # get all options
                for key, value in self._current_window.get_option().items():
                    self.engine.set_option(key.replace(' ', '_'), value)

            b = Button(self,
                       text=self.process_text('$apply_menu_button$'),
                       color='red',
                       size_x=0.3,
                       size_y=0.15,
                       on_click=save_options,
                       )
            b.reparent_to(self._current_window._widget)
            b.set_pos(0.5, 0, -0.5 * 1.8 + 0.1)

            def reset_options():
                # get all options
                for key in self._current_window.get_option().keys():
                    self._current_window.set_option(key, self.engine(key.replace(' ', '_'), default=True))

            b = Button(self,
                       text=self.process_text('$reset_menu_button$'),
                       color='blue',
                       size_x=0.3,
                       size_y=0.15,
                       on_click=reset_options,
                       )
            b.reparent_to(self._current_window._widget)
            b.set_pos(0., 0, -0.5 * 1.8 + 0.1)

            def back():
                # back to previous window
                self.show_menu()

            b = Button(self,
                       text=self.process_text('$back_menu_button$'),
                       size_x=0.3,
                       size_y=0.15,
                       on_click=back,
                       )
            b.reparent_to(self._current_window._widget)
            b.set_pos(-0.5, 0, -0.5 * 1.8 + 0.1)

        # current window is a ButtonWindow with several buttons
        self.set_current_window(
            win=ButtonWindow,
            title=self.process_text('$menu_title$'),
            text=self.process_text('$menu_text$'),
            size_x=1.0,
            size_y=1.0,
        )
        self._current_window.add_button(size_x=0.5,
                                        size_y=0.15,
                                        text='\1golden\1$button_play$\2',
                                        pos=(0.0, 0.0, 0.1),
                                        on_select=choose_game)
        self._current_window.add_button(size_x=0.5,
                                        size_y=0.15,
                                        text='\1golden\1$button_options$\2',
                                        pos=(0.0, 0.0, -0.1),
                                        on_select=options)
        self._current_window.add_button(size_x=0.5,
                                        size_y=0.15,
                                        text='\1golden\1$button_quit$\2',
                                        pos=(0.0, 0.0, -0.3),
                                        on_select=self.engine.quit)
        self._current_window.select_button()

    def set_single_window(self, with_3d_screens, screen_number):
        # setting the main window properties
        props = WindowProperties()
        # screen resolutions
        x, y = self.engine('screen_resolution')
        if with_3d_screens:
            # set window size
            props.set_size((screen_number * x, y))
        else:
            props.set_size((x, y))
        if self.engine('screen_position') is not None:
            props.set_origin(self.engine('screen_position'))

        props.set_undecorated(not self.engine('decorated_window'))
        self.engine.win.request_properties(props)
