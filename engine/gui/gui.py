import math
import os
import re
import pandas as pd
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
    colors = {'green': (0.2, 0.8, 0.1, 1.0),
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
        self._text_file = pd.read_csv(self.engine('text_file'), sep=',', index_col='key').fillna('NaN')
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
        self.set_current_window(win=EndWindow,
                                player_position=player_position,
                                time_minutes=time_minutes,
                                time_seconds=time_seconds,
                                total_players=total_players,
                                background_color=self.colors['black'],
                                )

        self.accept_once('enter', self.reset)
        # buy default, reset menu after a certain delay
        self.do_method_later(self.engine('end_game_reset_delay'), self.reset, name='menu_reset_task')

    def hide_cursor(self):
        # hide cursor
        Logger.error('HIDING cursor')
        props = WindowProperties()
        props.setCursorHidden(True)
        self.engine.win.requestProperties(props)

    def show_cursor(self):
        # show cursor
        Logger.error('SHOWING cursor')
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
            kwargs['background_color'] = (0.0, 0.0, 0.0, 0.5)
        self._current_window = win(self, **kwargs)

    def close_window_and_go(self, *args):
        """
        Close the current window and run the next step

        Args:
            *args: ignored arguments
        """
        if self._current_window is not None and not self._current_window.is_empty():
            self._current_window.destroy()
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

    @event('end_screen')
    def on_end_screen(self):
        self.end_screen()

    @event('info')
    def on_info(self, icon='chat', title='$info_title$', text='', close_time=-1, close_on_enter=True,
                color='dark-window', **kwargs):
        self.set_current_window(
            icon=icon,
            title=self.process_text(title),
            text=self.process_text(text),
            life_time=close_time,
            on_enter=self.close_window_and_go if close_on_enter else None,
            color=color,
            **kwargs
        )

    @event('password')
    def on_password(self, icon='caution', title='$password_title$', text='', close_time=-1, password='', format=None,
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
            life_time=close_time,
            password=password,
            on_password_find=self.close_window_and_go if on_password_find is None else on_password_find,
            color=color,
            **kwargs
        )

    @event('video')
    def on_video(self, name, size_x=1.0, size_y=0.8, close_time=-1, start=True, color='dark-window',
                 title='$video_title$', text='$video_text$', **kwargs):
        self.set_current_window(
            VideoWindow,
            color=color,
            video_path=name,
            size_x=size_x,
            size_y=size_y,
            life_time=close_time,
            start=start,
            title=self.process_text(title),
            text=self.process_text(text),
            file_format='avi',
            **kwargs
        )

    @event('warning')
    def on_warning(self, icon='caution', close_time=-1, color='dark-window', title='$warning_title$', text='',
                   close_on_enter=True, **kwargs):
        self.set_current_window(
            color=color,
            icon=icon,
            title=self.process_text(title),
            text=self.process_text(text),
            life_time=close_time,
            on_enter=self.close_window_and_go if close_on_enter else None,
            **kwargs
        )

    @event('menu')
    def on_menu(self):
        self.show_menu()

    @event('update_state')
    def on_update_state(self, key=None):
        self.screen.notify_update(key)

    @event('close_window')
    def on_close_window(self):
        self.close_window_and_go()

# else:
# # finally, pass event to the screen itself
# self.screen.notify_event(message, **kwargs)

    # def event(self, message, **kwargs) -> None:
    #     """
    #     Process an event that wasn't used in scenario handler
    #
    #     Args:
    #         message (str): event name
    #         **kwargs: optional args
    #     """
        # if message == 'set_screen':
        #     scenario_name = kwargs["name"].lower()
        #
        #     if scenario_name in ['go_to_mars', 'gotomars']:
        #         self.set_screen(GoToMarsScreen)
        #     elif scenario_name in ['lost_astronaut', 'lostastronaut']:
        #         self.set_screen(LostAstronautScreen)
        #     else:
        #         self.set_screen(None)
        #
        # elif message == 'end_screen':
        #     self.end_screen()
        #
        # elif message == 'info':
        #     self.set_current_window(
        #         icon=kwargs.pop('icon', 'chat'),
        #         title=self.process_text(kwargs.pop('title', '$info_title$')),
        #         text=self.process_text(kwargs.pop('text', '')),
        #         life_time=kwargs.pop('close_time', -1),
        #         on_enter=self.close_window_and_go if kwargs.pop('close_on_enter', True) else None,
        #         color=kwargs.pop('color', 'dark-window'),
        #         **kwargs
        #     )
        #
        # elif message == 'password':
        #     def format_target(x):
        #         x = x.replace('-', '')[:6]
        #         self._current_window.set_entry_text('-'.join([x[2 * i:2 * (i + 1)] for i in range(math.ceil(len(x) / 2))]))
        #
        #     if 'format' in kwargs:
        #         if kwargs['format'] == 'target':
        #             kwargs['on_entry_add'] = format_target
        #             kwargs['on_entry_delete'] = format_target
        #         else:
        #             Logger.error('unknown text format {}'.format(kwargs['format']))
        #
        #     self.set_current_window(
        #         icon=kwargs.pop('icon', 'caution'),
        #         title=self.process_text(kwargs.pop('title', '$password_title$')),
        #         text=self.process_text(kwargs.pop('text', '')),
        #         life_time=kwargs.pop('close_time', -1),
        #         password=kwargs.pop('password'),
        #         on_password_find=kwargs.pop('on_password_find', self.close_window_and_go),
        #         color=kwargs.pop('color', 'dark-window'),
        #         **kwargs
        #     )
        #
        # elif message == 'video':
        #     self.set_current_window(
        #         VideoWindow,
        #         color=kwargs.pop('color', 'dark-window'),
        #         video_path=kwargs['name'],
        #         size_x=kwargs.pop('size_x', 1.0),
        #         size_y=kwargs.pop('size_y', 0.8),
        #         life_time=kwargs.pop('close_time', -1),
        #         start=kwargs.pop('start', True),
        #         title=self.process_text(kwargs.pop('title', '$video_title$')),
        #         text=self.process_text(kwargs.pop('text', '$video_text$')),
        #         file_format='avi',
        #         **kwargs
        #     )
        #
        # elif message == 'warning':
        #     self.set_current_window(
        #         color=kwargs.pop('color', 'dark-window'),
        #         icon=kwargs.pop('icon', 'caution'),
        #         title=self.process_text(kwargs.pop('title', '$warning_title$')),
        #         text=self.process_text(kwargs.pop('text', '')),
        #         life_time=kwargs.pop('close_time', -1),
        #         on_enter=self.close_window_and_go if kwargs.pop('close_on_enter', True) else None,
        #         **kwargs
        #     )
        #
        # elif message == 'menu':
        #     self.show_menu()
        #
        # elif message == 'update_state':
        #     self.screen.notify_update(kwargs.get('key', None))
        #
        # elif message == 'close_window':
        #     self.close_window_and_go()
        #
        # else:
        #     # finally, pass event to the screen itself
        #     self.screen.notify_event(message, **kwargs)

    def show_menu(self):
        """
        Display the main menu
        """
        # reset the screen, displays a black empty image
        self.set_screen()

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

        # aspectRatio = self.engine.getAspectRatio()
        # self.myAspect2d = self.engine.render2d.attachNewNode(PGTop('myAspect2d'))
        # self.myAspect2d.setScale(y/x, 1.0, 1.0)
        # self.myAspect2d.node().setMouseWatcher(self.engine.mouseWatcherNode)

        # this causes GUI to render wrongly
        # self.engine.cam2d.node().getLens().setAspectRatio(x / y)
            # # setting the dimensions of the gui display region
            # for dr in self.engine.win.get_display_regions():
            #     print('->', dr)
            #     cam = dr.get_camera()
            #     e = 1 / screen_number
            #     if cam and "cam2d" in cam.name:
            #         print('cam2d region:', dr)
            #         dr.set_dimensions(0, e, 0, 1)
            #         cam.node().getLens().setAspectRatio(x / (screen_number * y))

    # def set_fullsd_ccreen(self):
    #     #     props = WindowProperties()
    #     #     res = getscreen_resolutions()[0]
    #     #     props.set_size(res)
    #     #     props.setFullscreen(True)
    #     #     self.engine.cam2d.node().getLens().setAspectRatio(float(res[1]/res[0]))
    #     #     self.engine.win.requestProperties(props)
    #     #
    #     #     self.set_backgrounolor()

    # def listen_to_keyboard(self):
    #     self.currentscreen.gain_focus()
    #
    # def keyboard_as_shuttle_control(self):
    #     self.request_focus()
    #     self.reject_keyboard(False)
    #
    #     self.accept('arrow_up', self.engine.shuttle.boost, extraArgs=['f'])
    #     self.accept('arrow_down', self.engine.shuttle.boost, extraArgs=['b'])
    #     self.accept('arrow_right', self.engine.shuttle.boost, extraArgs=['r'])
    #     self.accept('arrow_left', self.engine.shuttle.boost, extraArgs=['l'])
    #     self.accept('+', self.engine.shuttle.boost, extraArgs=['pp'])
    #     self.accept('-', self.engine.shuttle.boost, extraArgs=['pm'])
    #     self.accept('space', self.engine.shuttle.stop)
    #     self.accept('enter', lambda: print(self.engine.shuttle.frame.get_pos()))
    #     self.accept('backspace', self.engine.reset_game, extraArgs=[True])
    #
    #     self.enter_func = lambda: print(self.engine.shuttle.frame.get_pos())
    #
    #     for key in ['x', 'y', 'z']:
    #         self.accept(key, self.engine.shuttle.align_along, extraArgs=[key])
    #
    # def keyboard_as_hardware(self):
    #     self.request_focus()
    #     self.reject_keyboard(False)
    #
    #     for key in self._keyboard_hardware_map:
    #         name = self._keyboard_hardware_map[key]
    #         if key == "enter":
    #             self.enter_func = lambda: self.engine.update_hard_state[name]
    #         if name.startswith('j_'):
    #             self.accept(key, self.engine.update_hard_state,
    #                         extraArgs=[name, 1])
    #             self.accept('shift-' + key, self.engine.update_hard_state,
    #                         extraArgs=[name, -1])
    #             self.accept(key + '-up', self.engine.update_hard_state,
    #                         extraArgs=[name, 0])
    #         elif name.startswith('b_'):
    #             self.accept(key, self.engine.update_hard_state,
    #                         extraArgs=[name, True])
    #             self.accept(key + '-up', self.engine.update_hard_state,
    #                         extraArgs=[name, False])
    #         else:
    #             self.accept(key, self._switch_state, extraArgs=[name])

    def reject_keyboard(self, connect_alternative=True):
        pass
        # if self.currentscreen is not None:
        #     self.currentscreen.loose_focus()
        #
        # if self.engine("fulfill_current_step_key_with_F1"):
        #     self.accept('f1', self.engine.scenario.fulfill_current_step)
        #
        # if connect_alternative:
        #     if self.engine("keyboard_simulates_hardware"):
        #         self.keyboard_as_hardware()
        #     elif self.engine("keyboard_controls_shuttle"):
        #         self.keyboard_as_shuttle_control()

    def _switch_state(self, key):
        if self.engine.get_hard_state(key):
            self.engine.update_hard_state(key, False)
        else:
            self.engine.update_hard_state(key, True)
