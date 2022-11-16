import subprocess

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties


def get_screen_resolutions():
    p = subprocess.Popen(['xrandr'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '*'], stdin=p.stdout, stdout=subprocess.PIPE)
    p.stdout.close()

    a, _ = p2.communicate()
    a = a.decode("utf-8")
    res = []
    for line in a.splitlines():
        r = line.strip().split(" ")[0].strip()
        res.append((int(r.split("x")[0].strip()), int(r.split("x")[1].strip())))
    return res


class MainScreen(ShowBase):
    def __init__(self, single_screen=False):
        ShowBase.__init__(self)

        self.props = WindowProperties()

        self.props.set_size(800, 600)
        self.props.set_origin(100, 100)
        self.win.requestProperties(self.props)
        self._monitor = 0

        # same resolutions
        self.res = get_screen_resolutions()[0]

        self.accept("u", self.set_undecorated)
        self.accept("p", print, extraArgs=[get_screen_resolutions()])
        self.accept("q", self.finalizeExit)
        self.accept("g", self.set_full_screen)
        self.accept("f", self.simulate_fullscreen)
        self.accept("arrow_up-repeat", self.shift_pos_y, extraArgs=[-5])
        self.accept("arrow_up", self.shift_pos_y, extraArgs=[-100])
        self.accept("arrow_down-repeat", self.shift_pos_y, extraArgs=[5])
        self.accept("arrow_down", self.shift_pos_y, extraArgs=[100])
        self.accept("arrow_right-repeat", self.shift_pos_x, extraArgs=[5])
        self.accept("arrow_right", self.shift_pos_x, extraArgs=[100])
        self.accept("arrow_left-repeat", self.shift_pos_x, extraArgs=[-5])
        self.accept("arrow_left", self.shift_pos_x, extraArgs=[-100])

        self.num_screen = 1
        self.screens = []
        if single_screen:
            for i in range(5):
                self.accept(str(i), self.set_on_screen, extraArgs=[i])
            self.set_on_screen()
        else:
            self.num_screen = len(get_screen_resolutions())
            for j in range(self.num_screen - 1):
                self.screens.append(TestScreen(self, j + 1))
        self.request_focus()

    def request_focus(self):
        self.props.set_foreground(True)
        self.win.requestProperties(self.props)

    def set_on_screen(self, screen=0):
        print("Setting on screen", screen)
        self.shift_pos_x((screen - self._monitor) * self.res[0])
        self._monitor = screen

    def get_pos(self):
        return self.props.get_origin().x, self.props.get_origin().y

    def shift_pos_x(self, x):
        print("\nold position : ", self.get_pos())
        pos_x, pos_y = self.get_pos()
        self.props.setOrigin(pos_x + x, pos_y)
        self.win.requestProperties(self.props)
        print("new position : ", self.get_pos())

    def shift_pos_y(self, y):
        print("\nold position : ", self.get_pos())
        pos_x, pos_y = self.get_pos()
        self.props.setOrigin(pos_x, pos_y + y)
        self.win.requestProperties(self.props)
        print("new position : ", self.get_pos())

    def set_undecorated(self):
        self.props.set_undecorated(not self.props.get_undecorated())
        self.props.set_foreground(True)
        self.win.requestProperties(self.props)

    def simulate_fullscreen(self, border=30):
        self.props.set_undecorated(True)
        self.props.set_size((self.res[0] - 2 * border, self.res[1] - 2 * border))
        print("fullscreen : ", border + self._monitor * self.res[0])
        self.props.set_origin((border + self._monitor * self.res[0], border))
        self.win.requestProperties(self.props)

    def set_full_screen(self):
        if self.props.get_fullscreen():
            self.props.set_size((800, 600))
        else:
            self.props.set_size(get_screen_resolutions()[0])
        self.props.setFullscreen(not self.props.get_fullscreen())
        if self.num_screen > 1:
            for s in self.screens:
                s.fullscreen()
        self.win.requestProperties(self.props)


class TestScreen:
    def __init__(self, main_screen, screen):
        self.main_screen = main_screen
        self.props = WindowProperties()

        self.props.set_size(800, 600)
        self.props.set_origin(100 + screen * self.main_screen.res[0], 100)
        self.props.set_undecorated(True)
        self.props.set_foreground(True)

        self._monitor = screen
        self.window = self.main_screen.openWindow(props=self.props)
        self.lens = self.main_screen.camList[-1].node().getLens()

    def fullscreen(self, border=0):
        if self.window.get_size()[0] == 800:
            self.props.set_size((self.main_screen.res[0] - 2 * border, self.main_screen.res[1] - 2 * border))
            self.props.setOrigin(self._monitor * self.main_screen.res[0] + border, border)
            self.lens.setAspectRatio(float(self.main_screen.res[0]/self.main_screen.res[1]))

        else:
            self.props.set_size(800, 600)
            self.props.setOrigin(100 + self._monitor * self.main_screen.res[0], 100)
            self.lens.setAspectRatio(4/3)

        self.window.requestProperties(self.props)


if __name__ == "__main__":
    game = MainScreen()
    game.run()

