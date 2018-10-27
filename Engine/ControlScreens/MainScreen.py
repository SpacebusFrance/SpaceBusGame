import string
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import WindowProperties, TransparencyAttrib
from direct.showbase import DirectObject
from panda3d.core import LVector4f, PNMImageHeader, Filename

from Engine.ControlScreens.AlertScreen import AlertScreen
from Engine.ControlScreens.ImageScreen import ImageScreen
from Engine.ControlScreens.InfoOverScreen import InfoOverScreen
from Engine.ControlScreens.LockScreen import LockScreen
from Engine.ControlScreens.DefaultScreen import MainScreen
from Engine.ControlScreens.TargetScreen import TargetScreen
from Engine.Utils.utils import read_ini_file, get_screen_resolutions


class ControlScreen(DirectObject.DirectObject):
    """
    Class that represents the main ControlScreen
    """

    def __init__(self, gameEngine):
        DirectObject.DirectObject.__init__(self)
        self.gameEngine = gameEngine
        self.elements = []
        self.font = gameEngine.loader.loadFont(
            self.gameEngine.params("font_path") + self.gameEngine.params("default_font"))

        iH = PNMImageHeader()
        self.image_path = self.gameEngine.params("control_screen_image_path")

        iH.readHeader(Filename(self.image_path + "screen.png"))
        self._x0 = 2 / iH.get_x_size()
        self._y0 = 2 / iH.get_y_size()

        # setting 16/9 screen
        self.props = WindowProperties()
        self.props.set_size((1024, 576))
        self.window = self.gameEngine.win
        self.window.requestProperties(self.props)

        self.gui_camera = self.gameEngine.cam2d
        # this could be simply removed
        self.gui_render_node = self.gui_camera

        self.lens = self.gui_camera.node().getLens()

        self.fg_color = LVector4f(0.3, 0.26, 0.227, 1.0)
        self.fg_color_red = LVector4f(0.709, 0.180, 0.090, 1.0)
        self.fg_color_green = LVector4f(0.501, 0.807, 0.337, 1.0)

        self.background_image = OnscreenImage(image=self.image_path + "default.png",
                                              pos=(0, 0, 0),
                                              sort=5,
                                              parent=self.gui_render_node)

        self._previous_screen = None
        self._keyboard_hardware_map = read_ini_file(self.gameEngine.params("hardware_keyboard_map_file"))
        self.current_screen = None
        self.on_screen_info = InfoOverScreen(self)
        self.enter_func = None

        self.limited_update = self.gameEngine.params("control_screen_limited_refresh")
        if not self.limited_update:
            self.window.setActive(True)
        else:
            self.update()

    def gimp_pos(self, xg, yg):
        """
        Returns the screen coordinates fro initial Gimp positions in the image
        @param xg: the x position on Gimp
        @param yg: the y position on Gimp
        @return:
        """
        return (-1 + xg * self._x0,
                1 - yg * self._y0)

    def set_background_image(self, name, extension='.png'):
        """
        Changes the background image
        @param name: the file name without extension
        @param extension: the file extension.
        """
        self.background_image.setImage(self.image_path + name + extension)

    def info_text(self, text, close_time=10):
        """
        Text popup screen. This screen can be closed by pressing 'enter' key
        @param text: The text to display
        @param close_time: the life time of the popup in seconds.
        """
        self.gameEngine.sound_manager.play("gui_open")
        self.on_screen_info.set_text(text)
        self.on_screen_info.show()
        self.gameEngine.update_soft_state("info_text", True)

        def _end(t=None):
            if self.on_screen_info.is_on_screen():
                self.gameEngine.sound_manager.play("gui_close")
                self.on_screen_info.hide()
                self.gameEngine.update_soft_state("info_text", False)
                if self.enter_func is not None:
                    self.accept("enter", self.enter_func)
                else:
                    self.ignore("enter")

        self.accept("enter", _end)
        self.request_focus()
        if close_time is not None:
            self.gameEngine.taskMgr.doMethodLater(close_time, _end, name="end_info")

    def event(self, message, **kwargs):
        """
        Send an event to the screen.
        @param message: the event name
        @param kwargs: the assocaited parameters.
        """
        if message == "crew_lock_screen":
            self._previous_screen = message
            self.listen_to_keyboard()
            self.gameEngine.update_soft_state("listen_to_hardware", False)

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = LockScreen(self, kwargs.get("num_player", None))

        elif message == "default_screen":
            self._previous_screen = message
            self.reject_keyboard()
            self.gameEngine.update_soft_state("listen_to_hardware", True)

            self.gameEngine.sound_manager.stop("alarm")
            self.gameEngine.sound_manager.play("screen_intro")

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = MainScreen(self)

        elif message == "alert_screen":
            self._previous_screen = message
            self.listen_to_keyboard()
            self.gameEngine.update_soft_state("listen_to_hardware", False)

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = AlertScreen(self)

        elif message == "target_screen":
            self._previous_screen = message
            self.gameEngine.update_soft_state("listen_to_hardware", False)
            self.listen_to_keyboard()

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = TargetScreen(self)

        # elif message == "admin_screen":
        #     self.listen_to_keyboard()
        #
        #     if self.current_screen is not None:
        #         self.current_screen.destroy()
        #     self.current_screen = AdminScreen(self)

        elif message == "image_screen":
            self._previous_screen = message
            self.reject_keyboard()

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = ImageScreen(self, kwargs.get("image_name", "default"))

        elif message == "image_screen_text":
            if isinstance(self.current_screen, ImageScreen):
                self.current_screen.show_text(kwargs.get("text", ""),
                                              size=kwargs.get("size", 1),
                                              pos_x=kwargs.get("pos_x", 0.0),
                                              pos_y=kwargs.get("pos_y", 0.0),
                                              color=kwargs.get("color", None),
                                              alpha_time=kwargs.get("alpha_time", 0.0))

        elif message == "set_gauge_goto_time" and isinstance(self.current_screen, MainScreen):
            gauge = self.current_screen.gauges.get(kwargs.get("gauge", None), None)
            time = kwargs.get("time", None)
            if gauge is not None and time is not None:
                gauge.set_time_for_goto(time)

        elif message == 'update_state' and isinstance(self.current_screen, MainScreen):
            key = kwargs.get("key", None)
            if key is not None:
                self.current_screen.set_element(key)
            else:
                self.current_screen.set_all_elements()

    def set_previous_screen(self):
        """
        Resets the previous screen
        """
        self.event(self._previous_screen)

    def request_focus(self):
        """
        Request the focus. Seems to be useless
        """
        self.props.setForeground(True)
        self.window.requestProperties(self.props)
        self.update()

    def set_single_window(self, screen_numbers=5, res_x=1920, res_y=1080, decorated=False, pos=None):
        """
        If the game works in single window (much faster), enlarges the screen and allocates a fraction of it to the ControlScreen
        @param screen_numbers: the numbers of simulated screens (including the ControlScreen)
        @param res_x: the x resolution of each screen
        @param res_y: the y resolution of each screen
        @param decorated: if the window should be decorated or not
        """
        # setting the main window
        self.props.set_size((screen_numbers * res_x, res_y))
        self.props.set_origin((0, 0) if pos is None else tuple(pos))
        self.props.setUndecorated(not decorated)
        self.window.requestProperties(self.props)

        # setting the dimensions of the gui display region
        for dr in self.window.get_display_regions():
            cam = dr.get_camera()
            if cam and "cam2d" in cam.name:
                dr.set_dimensions(0, 1/screen_numbers, 0, 1)

        self.update()

    def set_fullscreen(self):
        """
        Sets this screen in fullscreen mode.
        """
        res = get_screen_resolutions()[0]
        self.props.set_size(res)
        self.props.setFullscreen(True)
        self.lens.setAspectRatio(float(res[1] / res[0]))
        self.window.requestProperties(self.props)
        self.update()

    def listen_to_keyboard(self):
        """
        Allows to listen to the keyboard. Maps keys to the corresponding chars.
        """
        self.request_focus()
        self.reject_keyboard(False)

        if self.gameEngine.params("fulfill_current_step_key_with_F1"):
            self.accept('f1', self.gameEngine.scenario.fulfill_current_step)

        char_list = string.printable
        for char in char_list[:10]:
            self.accept(char, self.input_text, extraArgs=[char])
        for i, char in enumerate(char_list[10:36]):
            self.accept(char, self.input_text, extraArgs=[char])
            self.accept("shift-" + char, self.input_text, extraArgs=[char_list[i + 36]])
        # dot
        self.accept('.', self.input_text, extraArgs=['.'])
        self.accept("backspace", self.input_text, extraArgs=['back'])
        self.accept("enter", self.input_text, extraArgs=['enter'])

        self.enter_func = lambda: self.input_text("enter")

    def keyboard_as_shuttle_control(self):
        """
        Sets the keyboard as a shuttle controller.
        """
        self.request_focus()
        self.reject_keyboard(False)

        self.accept('arrow_up', self.gameEngine.shuttle.boost, extraArgs=['f'])
        self.accept('arrow_down', self.gameEngine.shuttle.boost, extraArgs=['b'])
        self.accept('arrow_right', self.gameEngine.shuttle.boost, extraArgs=['r'])
        self.accept('arrow_left', self.gameEngine.shuttle.boost, extraArgs=['l'])
        self.accept('+', self.gameEngine.shuttle.boost, extraArgs=['pp'])
        self.accept('-', self.gameEngine.shuttle.boost, extraArgs=['pm'])
        self.accept('space', self.gameEngine.shuttle.stop)
        self.accept('enter', lambda: print(self.gameEngine.shuttle.frame.get_pos()))
        self.accept('backspace', self.gameEngine.reset_game, extraArgs=[True])

        self.enter_func = lambda: print(self.gameEngine.shuttle.frame.get_pos())

        for key in ['x', 'y', 'z']:
            self.accept(key, self.gameEngine.shuttle.align_along, extraArgs=[key])

    def keyboard_as_hardware(self):
        """
        Sets the keyboard as a simulated hardware. The mapping is defined in the keyboard_hardware file.
        """
        self.request_focus()
        self.reject_keyboard(False)

        for key in self._keyboard_hardware_map:
            name = self._keyboard_hardware_map[key]
            if key == "enter":
                self.enter_func = lambda: self.gameEngine.update_hard_state[name]
            if name.startswith('j_'):
                self.accept(key, self.gameEngine.update_hard_state,
                            extraArgs=[name, 1])
                self.accept('shift-' + key, self.gameEngine.update_hard_state,
                            extraArgs=[name, -1])
                self.accept(key + '-up', self.gameEngine.update_hard_state,
                            extraArgs=[name, 0])
            elif name.startswith('b_'):
                self.accept(key, self.gameEngine.update_hard_state,
                            extraArgs=[name, True])
                self.accept(key + '-up', self.gameEngine.update_hard_state,
                            extraArgs=[name, False])
            else:
                self.accept(key, self._switch_state, extraArgs=[name])

    def reject_keyboard(self, connect_alternative=True):
        """
        Ignore all keyboard inputs.
        @param connect_alternative: if True, reads the params of the game and sets the keyboard on shuttle_control or hardware_control
        """
        self.ignore_all()

        if self.gameEngine.params("fulfill_current_step_key_with_F1"):
            self.accept('f1', self.gameEngine.scenario.fulfill_current_step)

        if connect_alternative:
            if self.gameEngine.params("keyboard_simulates_hardware"):
                self.keyboard_as_hardware()
            elif self.gameEngine.params("keyboard_controls_shuttle"):
                self.keyboard_as_shuttle_control()

    def _switch_state(self, key):
        if self.gameEngine.get_hard_state(key):
            self.gameEngine.update_hard_state(key, False)
        else:
            self.gameEngine.update_hard_state(key, True)

    def update(self):
        """
        Updates the window when this window is not active (for saving FPS).
        """
        if self.limited_update:
            self.window.setActive(True)
            self.gameEngine.graphicsEngine.render_frame()
            self.window.setActive(False)
        else:
            pass

    def input_text(self, textEntered):
        """
        Transmitting keyboard inputs.

        @param textEntered: string. Sent from the shuttle object.
        """
        self.current_screen.process_text(textEntered)



class LoadIcon:
    """
    A spinning icon.
    """
    def __init__(self, mainScreen, x=0.0, y=0.0):
        self.main_screen = mainScreen
        self._image = OnscreenImage(image=self.main_screen.image_path + "load_icon.png",
                                    pos=(x, 0, y),
                                    parent=self.main_screen.gameEngine.render2d,
                                    scale=(0.07, 1, 0.07)
                                    )
        self._image.setTransparency(TransparencyAttrib.MAlpha)
        self.spin_task = None
        self._image.hide()

    def set_pos(self, x, y):
        """
        Sets the position of the icon
        @param x: the relative x in the screen
        @param y: the relative y in the screen
        """
        self._image.set_r(0)
        self._image.set_pos(x, 0, y)

    def start(self):
        """
        Starts the spinning animation and shows it.
        """
        self._image.set_r(0)
        self._image.show()
        self.spin_task = self._image.hprInterval(duration=2, hpr=(0, 0, 360))
        self.spin_task.loop()

    def stop(self):
        """
        Stops the spinning animation and hides it.
        @return:
        """
        self.spin_task.finish()
        self._image.hide()


#
#
# class AdminScreen(Screen):
#     """
#     The administrator screen. Mainly unused.
#     """
#     def __init__(self, mainScreen):
#         self.unlocked = False
#         self.menu_choice = 0
#         self._listen_to_input = True
#
#         # done after since it needs crew_list
#         Screen.__init__(self, mainScreen,
#                         image_name="admin_lock",
#                         entry_gimp_pos=(375, 357),
#                         entry_size=0,
#                         max_char=10)
#
#         self.name = "lock_screen"
#         self.cursor = OnscreenImage(image=mainScreen.image_path + "admin_cursor.png",
#                                     parent=mainScreen.gui_render_node,
#                                     # sort=2
#                                     )
#         self.cursor.setTransparency(True)
#         self.cursor.hide()
#         iH = PNMImageHeader()
#         iH.readHeader(Filename(mainScreen.image_path + "admin_cursor.png"))
#
#         self.w = iH.get_x_size()
#         self.h = iH.get_y_size()
#
#         iH.readHeader(Filename(mainScreen.image_path + "screen.png"))
#         self._x = [-1 + self.w / iH.get_x_size(), 2 / iH.get_x_size()]
#         self._y = [1 - self.h / iH.get_y_size(), -2 / iH.get_y_size()]
#
#         self.cursor.set_scale(LVector3f(self.w / iH.get_x_size(),
#                                         1,
#                                         self.h / iH.get_y_size()))
#
#         self._update()
#         self._update()
#
#     def _set_gimp_pos(self, x, y):
#         self.cursor.set_pos((self._x[0] + x * self._x[1],
#                              0.0,
#                              self._y[0] + y * self._y[1]))
#
#     def load_passwords(self):
#         passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
#         self.passwords["password"] = passwords["admin_password"]
#
#     def destroy(self):
#         self.cursor.destroy()
#         Screen.destroy(self)
#
#     def set_menu(self):
#         if self.menu_choice == 1:
#             self._set_gimp_pos(281, 254)
#         else:
#             self._set_gimp_pos(281, 170)
#         self._update()
#
#     def change_menu(self):
#         if self.menu_choice == 0:
#             self.menu_choice = 1
#         else:
#             self.menu_choice = 0
#         self.set_menu()
#
#     def validate(self):
#         if self.menu_choice == 0:
#             self.destroy()
#             self.main_screen.gameEngine.reset_game(True)
#         else:
#             sys.exit()
#
#     def unlock(self):
#         self.main_screen.set_background_image("admin_menu")
#         self.cursor.show()
#         self.set_menu()
#
#         self._listen_to_input = False
#         self.hide_on_screen_texts()
#
#         self.main_screen.accept('arrow_up', self.change_menu)
#         self.main_screen.accept('arrow_down', self.change_menu)
#         self.main_screen.accept('enter', self.validate)
#
#         self._update()
#
#     def check_input(self):
#         if self.check_password("password"):
#             self.reset_text(sound="ok", update=False)
#             self.unlocked = True
#
#             self._listen_to_input = False
#             self.hide_on_screen_texts()
#
#             self.unlock()
#         else:
#             self.reset_text(sound="wrong")
#             self.main_screen.set_previous_screen()


