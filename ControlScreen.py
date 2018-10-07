import random
import string
import sys

from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText, WindowProperties, TextNode, TransparencyAttrib
from direct.showbase import DirectObject
from panda3d.core import LVector3f, LVector4f, PNMImageHeader, Filename

from utils import read_ini_file, get_screen_resolutions


class Gauge:
    """
    Represents a dynamic gauge linked to a global variable of the shuttle.
    """
    def __init__(self, screen, name, x=0, low_value=-1, high_value=101, min=0, max=100):
        """
        Creates a new gauge
        @param screen: the controlScreen instance
        @param name: the name of the corresponding global variable (soft_state).
        @param x:
        @param low_value: below this limit,
        @param high_value:
        @param min: minimum value
        @param max: maximum value
        """
        self.taskMgr = screen.gameEngine.taskMgr
        self.update_func = screen.update
        self.screen = screen
        self.name = name
        self.low_value = low_value
        self.high_value = high_value
        self._hardware = screen.gameEngine.hardware
        self._sound = screen.gameEngine.sound_manager
        self.texture = OnscreenImage(image=screen.image_path + "indicateur.png",
                                     parent=screen.gui_render_node)
        self.texture.setTransparency(True)
        iH = PNMImageHeader()
        iH.readHeader(Filename(screen.image_path + "indicateur.png"))

        self.time_for_goto = None
        self.half_sec_step_for_goto = 1.0

        self.w = iH.get_x_size()
        self.h = iH.get_y_size()
        self._limits = [min, max]

        iH.readHeader(Filename(screen.image_path + "screen.png"))
        self._x0 = x
        self._x = [-1 + self.w / iH.get_x_size(), 2 / iH.get_x_size()]
        self._y = [1 - self.h / iH.get_y_size(), -2 / iH.get_y_size()]
        self._gauge_min_y = 44 - 0.5 * self.h
        self._gauge_max_y = 466 - 0.5 * self.h

        self.texture.set_scale(LVector3f(self.w / iH.get_x_size(),
                                         1,
                                         self.h / iH.get_y_size()))

        self._task_to_come = []
        self.value = self.screen.gameEngine.get_soft_state(self.name)
        self._is_destroyed = False

        self.set_value()
        self.hide()

    def set_time_for_goto(self, time):
        self.time_for_goto = time
        self.half_sec_step_for_goto = None

    def set_half_sec_step_for_goto(self, step):
        self.half_sec_step_for_goto = step
        self.time_for_goto = None

    def _set_gimp_pos(self, x, y):
        self.texture.set_pos((self._x[0] + x * self._x[1],
                              0.0,
                              self._y[0] + y * self._y[1]))

    def set_color(self, color):
        self.texture.set_color(color)

    def destroy(self):
        self.texture.destroy()
        self._is_destroyed = True
        for i in range(len(self._task_to_come)):
            self.taskMgr.remove(self._task_to_come.pop())

    def hide(self):
        self.texture.hide()

    def show(self):
        self.texture.show()

    def goto_value(self, new_value):
        # stop the previous tasks
        for i in range(len(self._task_to_come)):
            self.taskMgr.remove(self._task_to_come.pop())

        def func(v):
            self.set_value(v)
            self.update_func.__call__()

        def stop(t=None):
            self._hardware.set_led_off("l_" + self.name + "_down")
            self._hardware.set_led_off("l_" + self.name + "_up")
            if self.low_value >= self.value:
                self._sound.play(self.name + "_low")
            elif self.high_value <= self.value:
                self._sound.play(self.name + "_high")

        self._hardware.set_led_off("l_" + self.name + "_down")
        self._hardware.set_led_off("l_" + self.name + "_up")
        step_by_half_sec = self.half_sec_step_for_goto
        if self.half_sec_step_for_goto is None:
            dx = abs(self.value - new_value)
            step_by_half_sec = 0.5 * dx / self.time_for_goto

        if self.value >= new_value:
            self._hardware.set_led_on("l_" + self.name + "_down")
            step_by_half_sec = - step_by_half_sec
        else:
            self._hardware.set_led_on("l_" + self.name + "_up")

        n_steps = -int((self.value - new_value) / step_by_half_sec)
        old_value = self.value

        for i in range(n_steps):
            self._task_to_come.append(self.taskMgr.doMethodLater(0.5 * i, func, name="gauge_move",
                                                                 extraArgs=[old_value + (i + 1) * step_by_half_sec]))

        self._task_to_come.append(self.taskMgr.doMethodLater(0.5 * n_steps, stop, name="gauge_move_stop"))

    def set_value(self, value=None):
        if not self._is_destroyed:
            if self.value >= self._limits[1]:
                self.value = self._limits[1]
            elif self.value < self._limits[0]:
                self.value = self._limits[0]

            old_value = self.value
            if value is not None:
                if value >= self._limits[1]:
                    value = self._limits[1]
                elif value < self._limits[0]:
                    value = self._limits[0]
                self.value = value
            if old_value > self.low_value >= self.value:
                self._sound.play(self.name + "_low")
                self._hardware.set_led_on("l_" + self.name + "_low")
            elif old_value <= self.low_value < self.value:
                self._hardware.set_led_off("l_" + self.name + "_low")
            elif old_value < self.high_value <= self.value:
                self._sound.play(self.name + "_high")
                self._hardware.set_led_on("l_" + self.name + "_high")
            elif self.value < self.high_value <= old_value:
                self._hardware.set_led_off("l_" + self.name + "_high")

            self._set_gimp_pos(self._x0, self._gauge_max_y + (self.value - self._limits[0]) / (
                        self._limits[1] - self._limits[0]) * (self._gauge_min_y - self._gauge_max_y))


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

        elif message == "admin_screen":
            self.listen_to_keyboard()

            if self.current_screen is not None:
                self.current_screen.destroy()
            self.current_screen = AdminScreen(self)

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

    def set_single_window(self, screen_numbers=5, res_x=1920, res_y=1080):
        """
        If the game works in single window (much faster), enlarges the screen and allocates a fraction of it to the ControlScreen
        @param screen_numbers: the numbers of simulated screens (including the ControlScreen)
        @param res_x: the x resolution of each screen
        @param res_y: the y resolution of each screen
        """
        # setting the main window
        self.props.set_size((screen_numbers * res_x, res_y))
        self.props.set_origin((0, 0))
        self.props.setUndecorated(True)
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


class InfoOverScreen:
    """
    The popup window class
    """
    def __init__(self, MainScreen, text=""):
        self.main_screen = MainScreen
        self._image = OnscreenImage(image=self.main_screen.image_path + "comm.png",
                                    pos=(0, 0, 0),
                                    parent=self.main_screen.gui_render_node,
                                    )
        # image in front
        self._image.set_bin("fixed", 10)
        self._image.setTransparency(TransparencyAttrib.MAlpha)
        self._text = OnscreenText(text=text,
                                  align=TextNode.ALeft,
                                  mayChange=True,
                                  pos=self.main_screen.gimp_pos(210, 230),
                                  scale=(0.06, 0.08),
                                  fg=LVector4f(1, 1, 1, 1),
                                  parent=self._image,
                                  wordwrap=20,
                                  )
        self._show = False
        self._image.hide()
        self._text.hide()

    def is_on_screen(self):
        """
        @return: True if the popup is on screen. False otherwise
        """
        return self._show

    def show(self, t=None):
        """
        Shows the window
        @param t: a mute parameter allowing to call it in a doMethodLater
        """
        self._show = True
        self._image.show()
        self._text.show()
        self.main_screen.update()

    def hide(self, t=None):
        """
        Hides the window
        @param t: a mute parameter allowing to call it in a doMethodLater
        """
        self._show = False
        self._image.hide()
        self._text.hide()
        self.main_screen.update()

    def set_text(self, text, end="\n\n... (Entrée pour continuer) ..."):
        """
        Sets the text of the popup.
        @param text: the text
        @param end: the end text.
        """
        self._text["text"] = text + end
        if self._show:
            self.main_screen.update()


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


class Screen:
    """
    This class represents the actual behaviour of the ControlScreen. Each different behaviour is encoded as a child class of this general Screen class
    """
    def __init__(self, MainScreen, image_name=None, entry_gimp_pos=None, entry_size=1.0, max_char=7):
        """
        Creates the class.
        @param MainScreen: The ControlScreen class
        @param image_name: the name of the background image to display.
        @param entry_gimp_pos: the position of the entry if there is one. Positions are given in Gimp positions.
        @param entry_size: The size of the entry text.
        @param max_char: The max number of characters accepted in the entry.
        """
        self.main_screen = MainScreen
        self.name = ""
        self.max_char = max_char
        if image_name is not None:
            self.main_screen.set_background_image(image_name)
        scale_x = .1 + entry_size * 0.05
        scale_y = scale_x
        self.lock_text = OnscreenText(text="",
                                      pos=self.main_screen.gimp_pos(
                                          *entry_gimp_pos) if entry_gimp_pos is not None else (0, 0),
                                      scale=(scale_x, scale_y
                                             ),
                                      align=TextNode.ABoxedLeft,
                                      font=self.main_screen.font,
                                      fg=self.main_screen.fg_color,
                                      parent=self.main_screen.gui_render_node,
                                      )
        self._listen_to_input = True
        self.on_screen_texts = dict()

        self.info_screen = None

        self.passwords = dict()
        self.load_passwords()

    def load_passwords(self):
        """
        To be implemented in each child class.
        """
        pass

    def add_on_screen_text(self, xg, yg, text, size=1.0, name=None, may_change=False, color=None):
        """
        Adds text on the screen
        @param xg: the x Gimp position of the text
        @param yg: the y Gimp position of the text
        @param text: the text itself
        @param size: the size of the text
        @param name: the name of this text (if you want to change it later)
        @param may_change: True if the text may change. False otherwise
        @param color: the color of the text, can be "green", "red" or black by default.
        """
        name = text if name is None else name
        if name not in self.on_screen_texts:
            if color == 'red':
                fg = self.main_screen.fg_color_red
            elif color == "green":
                fg = self.main_screen.fg_color_green
            else:
                fg = self.main_screen.fg_color
            x_scale = 0.04 + 0.01 * size
            y_scale = x_scale * 16 / 9
            self.on_screen_texts[name] = OnscreenText(text=text,
                                                      align=TextNode.ALeft,
                                                      mayChange=may_change,
                                                      pos=self.main_screen.gimp_pos(xg, yg),
                                                      scale=(x_scale, y_scale),
                                                      font=self.main_screen.font,
                                                      fg=fg,
                                                      parent=self.main_screen.gui_render_node,
                                                      )

    def hide_on_screen_texts(self, names=None):
        """
        Hide some texts displayed on the screen
        @param names: the names of the texts to hide. Can be a string or a list of strings. If None, all texts are hidden.
        """
        if names is None:
            for ost in self.on_screen_texts:
                self.on_screen_texts[ost].hide()
        elif isinstance(names, list):
            for l in names:
                if l in self.on_screen_texts:
                    self.on_screen_texts[l].hide()
        elif names in self.on_screen_texts:
            self.on_screen_texts[names].hide()

    def show_on_screen_texts(self, names=None):
        """
        Shows some texts displayed on the screen
        @param names: the names of the texts to hide. Can be a string or a list of strings. If None, all texts are hidden.
        """
        if names is None:
            for ost in self.on_screen_texts:
                self.on_screen_texts[ost].show()
        elif isinstance(names, list):
            for l in names:
                if l in self.on_screen_texts:
                    self.on_screen_texts[l].show()
        elif names in self.on_screen_texts:
            self.on_screen_texts[names].show()

    def set_on_screen_text(self, name, new_text, update=True, color=None):
        """
        Updates a text displayed on the screen
        @param name: the name of the text to update
        @param new_text : the new text to diaplay
        @param update : if the main screen is not automatically updated, updates the screen
        @param color: to set the new color of the text.
        """
        if name in self.on_screen_texts:
            self.on_screen_texts[name]["text"] = new_text
            if color is not None:
                if color == "green":
                    self.on_screen_texts[name]["fg"] = self.main_screen.fg_color_green
                elif color == "red":
                    self.on_screen_texts[name]["fg"] = self.main_screen.fg_color_red
                else:
                    self.on_screen_texts[name]["fg"] = color
            if update:
                self._update()

    def listen_to_input(self, listen):
        """
        Specifies if keyboard input are considered or not.
        @param listen: a boolean
        """
        self._listen_to_input = listen

    def call_main_screen(self, message):
        """
        Sends a message (event) to the main ControlScreeen (e.g. changing the screen)
        @param message: the message (event)
        """
        self.main_screen.event(message)

    def _update(self):
        self.main_screen.update()

    def destroy(self):
        """
        Destroys the current screen
        """
        self.lock_text.destroy()
        for element in self.on_screen_texts.values():
            element.destroy()

    def check_input(self):
        """
        To be implemnetd in child class. Check if the input in the entry corresponds to the desired password or not
        """
        pass

    def check_password(self, key, text=None):
        """
        Checks if the text corresponds to te password named 'key'
        @param key: the key of the password
        @param text: the text to check. If None, the text is the one entered in the entry.
        @return: a boolean
        """
        text = text if text is not None else self.lock_text["text"]
        if len(text) > 0 and key in self.passwords:
            return text in self.passwords[key]
        return False

    def reset_text(self, sound=None, update=True):
        """
        Resets the entry text.
        @param sound: name of the sound to play
        @param update: update or not the screen
        """
        self.lock_text["text"] = ""
        if sound is not None:
            self.main_screen.gameEngine.sound_manager.play(sound)
        if update:
            self._update()

    def transition_screen(self, image, time):
        """
        Creates a transition screen. An image is popup while listening to input is set to False
        @param image: the image name
        @param time: the lifetime of the popup.
        """
        new_image = OnscreenImage(self.main_screen.image_path + image + ".png",
                                  parent=self.main_screen.gui_render_node,
                                  pos=(0, 0, 0),
                                  )
        new_image.set_bin("fixed", 10)
        new_image.show()
        self._update()

        # hidding on_screen_texts
        for o in self.on_screen_texts:
            self.on_screen_texts[o].hide()

        relisten = False
        if self._listen_to_input:
            self._listen_to_input = False
            relisten = True
            self.lock_text.hide()

        def to_call(relisten):
            if relisten:
                self._listen_to_input = True
                self.lock_text.show()

            new_image.destroy()
            # showing on_screen_texts
            for o in self.on_screen_texts:
                self.on_screen_texts[o].show()

            self._update()

        self.main_screen.gameEngine.taskMgr.doMethodLater(time, to_call, name="update", extraArgs=[relisten])

    def process_text(self, char):
        """
        Process the incoming text
        @param char: the sent string
        """
        if self._listen_to_input:
            if char == "enter":
                self.check_input()
            elif char == "back":
                if len(self.lock_text["text"]) > 0:
                    self.lock_text["text"] = self.lock_text["text"][0:-1]
                    self._update()
            elif len(self.lock_text["text"]) < self.max_char:
                self.lock_text["text"] += char
                self._update()


class ImageScreen(Screen):
    """
    A basic image screen. Displays an image and can set text over it.
    """
    def __init__(self, mainScreen, image_name):
        self._listen_to_input = False
        self.main_screen = mainScreen
        Screen.__init__(self, mainScreen,
                        image_name=image_name,
                        )
        self.texts = []
        self._update()

    def show_text(self, text, size=1, pos_x=0.0, pos_y=0.0, color=None, alpha_time=0.0):
        x_scale = 0.04 + 0.01 * size
        y_scale = x_scale * 16 / 9
        self.texts.append(OnscreenText(text=text,
                                       align=TextNode.ACenter,
                                       mayChange=False,
                                       pos=(pos_x, pos_y),
                                       scale=(x_scale, y_scale),
                                       font=self.main_screen.font,
                                       fg=color if color is not None else (1, 1, 1, 1),
                                       parent=self.main_screen.gui_render_node,
                                       ))

    def destroy(self):
        for t in self.texts:
            self.texts.pop().destroy()


class LockScreen(Screen):
    """
    The lock screen that must be unlocked by crew.
    """
    def __init__(self, mainScreen, num_player=None):
        self.current_lock = 0
        self._listen_to_input = True
        self.crew_list = list()
        self.main_screen = mainScreen
        self.max_lock = num_player if num_player is not None else self.main_screen.gameEngine.params(
            "default_num_player")

        # done after since it needs crew_list
        Screen.__init__(self, mainScreen,
                        image_name="crew_lock",
                        entry_gimp_pos=(375, 357),
                        entry_size=0,
                        max_char=6)

        self.name = "lock_screen"
        self.wait_logo = LoadIcon(self.main_screen)

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('crew_screen_unlocked', False)

        self.add_on_screen_text(97, 352,
                                text="test",
                                size=2,
                                name="crew",
                                may_change=True,
                                )

        self.set_screen()
        self._update()
        self._update()

    def set_screen(self):
        self.set_on_screen_text("crew",
                                self.crew_list[self.current_lock].strip(),
                                update=False)

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for c in passwords:
            if c.startswith('crew_'):
                name = c.replace('crew_', '')
                self.crew_list.append(name)
                self.passwords[name] = passwords[c]
        # select random names
        if self.max_lock < len(self.crew_list):
            new_list = []
            new_pass = dict()
            for i in range(self.max_lock):
                new_list.append(self.crew_list.pop(random.choice(range(len(self.crew_list)))))
                new_pass[new_list[-1]] = self.passwords[new_list[-1]]
            self.crew_list = new_list
            self.passwords = new_pass

    def check_input(self):
        if self.check_password(self.crew_list[self.current_lock]):
            self.current_lock += 1

            self.reset_text(sound="ok", update=False)

            if self.current_lock >= self.max_lock:
                self.main_screen.set_background_image("unlocked")
                self._listen_to_input = False
                self.hide_on_screen_texts()

                self.wait_logo.set_pos(0.2, -0.16)
                self.wait_logo.start()

                self.main_screen.gameEngine.sound_manager.play("voice_identify_ok")

                def unlock(t):
                    self.wait_logo.stop()
                    self.main_screen.gameEngine.update_soft_state('crew_screen_unlocked', True)
                    self.call_main_screen("default_screen")

                # tell the game that the screen is unlocked
                self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, name="unlock")
            else:
                # setting new screen
                self.set_screen()
                # self.set_screen(time=2)
                self.transition_screen("crew_ok", time=2)

            self._update()
        else:
            self.transition_screen("crew_wrong", time=2)
            self.reset_text(sound="wrong")


class AdminScreen(Screen):
    """
    The administrator screen. Mainly unused.
    """
    def __init__(self, mainScreen):
        self.unlocked = False
        self.menu_choice = 0
        self._listen_to_input = True

        # done after since it needs crew_list
        Screen.__init__(self, mainScreen,
                        image_name="admin_lock",
                        entry_gimp_pos=(375, 357),
                        entry_size=0,
                        max_char=10)

        self.name = "lock_screen"
        self.cursor = OnscreenImage(image=mainScreen.image_path + "admin_cursor.png",
                                    parent=mainScreen.gui_render_node,
                                    # sort=2
                                    )
        self.cursor.setTransparency(True)
        self.cursor.hide()
        iH = PNMImageHeader()
        iH.readHeader(Filename(mainScreen.image_path + "admin_cursor.png"))

        self.w = iH.get_x_size()
        self.h = iH.get_y_size()

        iH.readHeader(Filename(mainScreen.image_path + "screen.png"))
        self._x = [-1 + self.w / iH.get_x_size(), 2 / iH.get_x_size()]
        self._y = [1 - self.h / iH.get_y_size(), -2 / iH.get_y_size()]

        self.cursor.set_scale(LVector3f(self.w / iH.get_x_size(),
                                        1,
                                        self.h / iH.get_y_size()))

        self._update()
        self._update()

    def _set_gimp_pos(self, x, y):
        self.cursor.set_pos((self._x[0] + x * self._x[1],
                             0.0,
                             self._y[0] + y * self._y[1]))

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        self.passwords["password"] = passwords["admin_password"]

    def destroy(self):
        self.cursor.destroy()
        Screen.destroy(self)

    def set_menu(self):
        if self.menu_choice == 1:
            self._set_gimp_pos(281, 254)
        else:
            self._set_gimp_pos(281, 170)
        self._update()

    def change_menu(self):
        if self.menu_choice == 0:
            self.menu_choice = 1
        else:
            self.menu_choice = 0
        self.set_menu()

    def validate(self):
        if self.menu_choice == 0:
            self.destroy()
            self.main_screen.gameEngine.reset_game(True)
        else:
            sys.exit()

    def unlock(self):
        self.main_screen.set_background_image("admin_menu")
        self.cursor.show()
        self.set_menu()

        self._listen_to_input = False
        self.hide_on_screen_texts()

        self.main_screen.accept('arrow_up', self.change_menu)
        self.main_screen.accept('arrow_down', self.change_menu)
        self.main_screen.accept('enter', self.validate)

        self._update()

    def check_input(self):
        if self.check_password("password"):
            self.reset_text(sound="ok", update=False)
            self.unlocked = True

            self._listen_to_input = False
            self.hide_on_screen_texts()

            self.unlock()
        else:
            self.reset_text(sound="wrong")
            self.main_screen.set_previous_screen()


class MainScreen(Screen):
    """
    The main default screen with shuttle informations, gauges etc.
    """
    def __init__(self, mainScreen):
        Screen.__init__(self, mainScreen, "screen")
        self.name = "unlocked_screen"

        self.gauges = dict()
        self.gauges["main_O2"] = Gauge(self.main_screen, name="main_O2", x=775, low_value=70)
        self.gauges["main_CO2"] = Gauge(self.main_screen, name="main_CO2", x=844, low_value=30, high_value=70)
        self.gauges["main_power"] = Gauge(self.main_screen, name="main_power", x=912, low_value=0, min=-100, max=100)
        self.gauges["main_power"].half_sec_step_for_goto = 2.0

        for counter, g in enumerate(self.gauges):
            self.gauges[g].show()

        self.lock_text.hide()

        # list of software variables that appear in the defautl screen, in the state list
        self.global_variables = ['batterie1',
                                 'batterie2',
                                 'batterie3',
                                 'batterie4',
                                 'offset_ps_x',
                                 'offset_ps_y',
                                 'recyclage_O2',
                                 'recyclage_CO2',
                                 'recyclage_H2O',
                                 'tension_secteur1',
                                 'oxygene_secteur1',
                                 'thermique_secteur1',
                                 'tension_secteur2',
                                 'oxygene_secteur2',
                                 'thermique_secteur2',
                                 'tension_secteur3',
                                 'oxygene_secteur3',
                                 'thermique_secteur3',
                                 'target_name'
                                 ]
        for i, gb in enumerate(self.global_variables):
            self.add_on_screen_text(269, 109 + i * 24, size=0, text="", name=gb, may_change=True)

        # to be modified
        self.add_on_screen_text(427, 100, size=2, text="", name="freq_comm", may_change=True)
        self.add_on_screen_text(417, 243, size=3, text="ON", color='green', name="pilote_automatique", may_change=True)
        self.add_on_screen_text(440, 542, size=2, text="", name="sp_power", may_change=True)
        self.add_on_screen_text(518, 383, size=0, text="actif", name="moteur1", may_change=True, color="green")
        self.add_on_screen_text(518, 410, size=0, text="actif", name="moteur2", may_change=True, color="green")
        self.add_on_screen_text(518, 437, size=0, text="actif", name="moteur3", may_change=True, color="green")

        self.add_on_screen_text(617, 229, size=0, text="on", name="correction_roulis", may_change=True, color="green")
        self.add_on_screen_text(617, 249, size=0, text="on", name="correction_direction", may_change=True,
                                color="green")
        self.add_on_screen_text(617, 269, size=0, text="on", name="correction_stabilisation", may_change=True,
                                color="green")

        self.set_all_elements()

    def set_all_elements(self):
        for name in self.on_screen_texts:
            value = self.main_screen.gameEngine.get_soft_state(name)
            # particular cases
            if name == "pilote_automatique":
                if value:
                    self.set_on_screen_text(name, "ON", False, "green")
                else:
                    self.set_on_screen_text(name, "OFF", False, "red")
            elif name in ['moteur1', 'moteur2', 'moteur3']:
                if value:
                    self.set_on_screen_text(name, "actif", False, "green")
                else:
                    self.set_on_screen_text(name, "inactif", False, "red")
            elif name == 'freq_comm':
                self.set_on_screen_text("freq_comm", str(value) + " MHz", True)
            else:
                if isinstance(value, bool):
                    if value:
                        self.set_on_screen_text(name, "on", False, "green")
                    else:
                        self.set_on_screen_text(name, "off", False, "red")
                else:
                    self.set_on_screen_text(name, str(value), False)

        for g in self.gauges:
            self.gauges[g].goto_value(self.main_screen.gameEngine.get_soft_state(g))
        self._update()

    def destroy(self):
        for g in self.gauges:
            self.gauges[g].destroy()
        Screen.destroy(self)

    def set_element(self, name):
        # should be in software_values

        value = self.main_screen.gameEngine.get_soft_state(name)
        if value is not None and name in self.on_screen_texts:
            # particular cases
            if name == "pilote_automatique":
                if value:
                    self.set_on_screen_text(name, "ON", True, "green")
                else:
                    self.set_on_screen_text(name, "OFF", True, "red")
            elif name in ['moteur1', 'moteur2', 'moteur3']:
                if value:
                    self.set_on_screen_text(name, "actif", True, "green")
                else:
                    self.set_on_screen_text(name, "inactif", True, "red")
            elif name == 'freq_comm':
                self.set_on_screen_text("freq_comm", str(value) + " MHz", True)
            else:
                if isinstance(value, bool):
                    if value:
                        self.set_on_screen_text(name, "on", True, "green")
                    else:
                        self.set_on_screen_text(name, "off", True, "red")
                else:
                    self.set_on_screen_text(name, str(value), True)
        elif name in self.gauges:
            self.gauges[name].goto_value(value)


class AlertScreen(Screen):
    """
    The alert screen that popups after the collision
    """
    def __init__(self, mainScreen):
        self.current_task = 0
        self.task_list = list()

        Screen.__init__(self, mainScreen, "alert",
                        entry_gimp_pos=(508, 430),
                        entry_size=0.3)
        self.name = "alert_screen"
        self._listen_to_input = False

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('alert_screen_unlocked', False)

        self.add_on_screen_text(319, 440, name="task", may_change=True, size=0, text="")
        self.hide_on_screen_texts()

        self.main_screen.gameEngine.sound_manager.play("alarm", loop=True,
                                                       volume=self.main_screen.gameEngine.params("alarm_volume"))

        self.wait_logo = LoadIcon(mainScreen, x=0.3, y=-0.38)
        self.wait_logo.start()
        self._update()

        # showing the unlock screen in a few secs.
        def task(t):
            self._listen_to_input = True
            self.wait_logo.stop()
            self.main_screen.set_background_image("alert_lock")
            self.set_screen()
            self.main_screen.gameEngine.sound_manager.play("voice_mdp")
            self.main_screen.info_text("Entrer le mot de passe inscrit sur la valve O2-5 qui se trouve dans la navette")
            self._update()

        self.main_screen.gameEngine.taskMgr.doMethodLater(2, self.main_screen.gameEngine.sound_manager.play, "as1",
                                                          extraArgs=['voice_alert'])
        self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, task, "as2")

    def set_screen(self):
        self.set_on_screen_text("task", self.task_list[self.current_task], False)
        self.show_on_screen_texts()

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for task in passwords:
            if task.startswith('alert_'):
                name = task.replace('alert_', '')
                self.task_list.append(name)
                self.passwords[name] = passwords[task]

    def check_input(self):
        if self.check_password(self.task_list[self.current_task]):
            self.reset_text(sound="ok", update=False)
            self.current_task += 1
            if self.current_task >= len(self.task_list):
                self._listen_to_input = False
                self.main_screen.set_background_image("alert_ok")
                self.hide_on_screen_texts()
                self.wait_logo.set_pos(0, -0.5)
                self.wait_logo.start()

                self.main_screen.gameEngine.sound_manager.stop("alarm")

                def unlock(t):
                    self.wait_logo.stop()
                    self.main_screen.gameEngine.update_soft_state('alert_screen_unlocked', True)
                    self.call_main_screen("default_screen")

                self.main_screen.gameEngine.taskMgr.doMethodLater(1, self.main_screen.gameEngine.sound_manager.play,
                                                                  "unlock0", extraArgs=["voice_alert_done"])
                self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, "unlock")
            else:
                self.set_screen()
            self._update()
        else:
            self.reset_text("wrong")


class TargetScreen(Screen):
    """
    The target screen to be unlocked
    """
    def __init__(self, mainScreen):
        Screen.__init__(self, mainScreen, "coordinates_lock",
                        entry_gimp_pos=(275, 305),
                        entry_size=0.5,
                        max_char=12)
        self.name = "target_screen"

        self._listen_to_input = True
        self._current_target = None

        self.wait_logo = LoadIcon(self.main_screen)

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('target_screen_unlocked', False)

        self.add_on_screen_text(250, 250,
                                text="Longitude (N) de la base 2012A2",
                                size=1,
                                may_change=True,
                                name="text"
                                )

        self.add_on_screen_text(450, 310,
                                text="",
                                size=2,
                                name="target")

        self.hide_on_screen_texts("target")

        # do it twice to secure
        self._update()

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for key in passwords:
            if key.startswith('target_'):
                self.passwords[key.replace('target_', "")] = passwords[key]

    def _update(self):
        # take correction into account
        self.lock_text["text"] = self.lock_text["text"].replace(" ", "")
        text = ""
        for i, a in enumerate(self.lock_text["text"]):
            text += a
            if i in [1, 3]:
                text += "   "
        self.lock_text["text"] = text
        Screen._update(self)

    def process_text(self, char):
        if self._listen_to_input:
            if char == "enter":
                self.check_input()
            elif char == "back":
                if len(self.lock_text["text"]) > 0:
                    self.lock_text["text"] = self.lock_text["text"].replace(" ", "")
                    self.lock_text["text"] = self.lock_text["text"][0:-1]
                    self._update()
            elif len(self.lock_text["text"]) < self.max_char:
                self.lock_text["text"] += char
                self._update()

    def check_input(self):
        if self._current_target is None:
            # check if the passwords corresponds to one target
            for p in self.passwords:
                if str(self.passwords[p][0]) == self.lock_text["text"].replace(" ", ""):
                    self.reset_text("ok", update=False)
                    self.set_on_screen_text("text",
                                            "Latitude (E) de la base 2012A2",
                                            update=False)
                    self._current_target = p
                    self._update()
                    break

            if self._current_target is None:
                self.reset_text("wrong")

        elif str(self.passwords[self._current_target][1]) == self.lock_text["text"].replace(" ", ""):
            self.reset_text("ok", update=False)
            self.main_screen.set_background_image("coordinates_ok")
            self.wait_logo.set_pos(0.3, -0.3)
            self.wait_logo.start()

            self._listen_to_input = False

            self.main_screen.gameEngine.update_soft_state("target_name", self._current_target)
            self.hide_on_screen_texts("text")
            self.set_on_screen_text("target", self._current_target)
            self.show_on_screen_texts("target")

            self.main_screen.gameEngine.sound_manager.play("voice_target_ok")

            def unlock(t):
                self.wait_logo.stop()
                self.main_screen.gameEngine.update_soft_state('target_screen_unlocked', True)
                self.call_main_screen("default_screen")

            self.main_screen.gameEngine.taskMgr.doMethodLater(7.0,
                                                              self.main_screen.gameEngine.sound_manager.play,
                                                              "sound_ts",
                                                              extraArgs=["voice_target_on"])
            self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, "unlock")
            self._update()
        else:
            self.reset_text("wrong")
