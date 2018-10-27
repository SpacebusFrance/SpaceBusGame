from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import LVector3f, PNMImageHeader, Filename


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