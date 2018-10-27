from panda3d.core import WindowProperties, NodePath


class FakeScreen3D:
    def __init__(self, gameEngine, screen_number, shuttle_angle=0, shift_x=0, shift_y=0.0):
        self.gameEngine = gameEngine
        self.screen = screen_number

        self.cam_node = self.gameEngine.make_camera(self.gameEngine.win,
                                                    displayRegion=(
                                                    0.2 * screen_number, 0.2 * (screen_number + 1), 0, 1),
                                                    aspectRatio=16 / 9,
                                                    )

        self.lens = self.cam_node.node().getLens()
        self.lens.setFov(self.gameEngine.params("cam_fov"))
        self.lens.setNear(0.1)

        self.cam_node.reparent_to(self.gameEngine.shuttle.frame)

        self.cam_node.set_hpr(-shuttle_angle, 0, 0)
        self.cam_node.set_x(shift_x)
        self.cam_node.set_y(shift_y)

    def set_angle(self, incr):
        self.cam_node.set_h(self.cam_node.get_h() + incr)
        print("new angle :", self.cam_node.get_h())

    def get_camera(self):
        return self.cam_node


class Screen3D:
    def __init__(self, gameEngine, screen_number, shuttle_angle=0, shift_x=0, shift_y=0.0):
        self.gameEngine = gameEngine

        self.props = WindowProperties()
        self.screen = screen_number
        # hard-coded to avoid detection problems
        self.res = [1920, 1080]

        self.props.set_size(800, 600)
        self.props.set_origin(100 + self.screen * self.res[0], 100)
        self.props.set_undecorated(True)
        self.props.set_foreground(False)

        self.window = self.gameEngine.openWindow(props=self.props, aspectRatio=float(800 / 600))

        # getting the new camera
        self.camera = self.gameEngine.camList[-1].node()
        self.cam_node = NodePath(self.camera)
        self.cam_node.reparent_to(self.gameEngine.shuttle.frame)
        self.cam_node.set_x(shift_x)
        self.cam_node.set_y(shift_y)
        self.lens = self.camera.getLens()
        self.lens.setFov(self.gameEngine.params("cam_fov"))
        self.lens.setNear(0.1)

        # self.cam_node.set_hpr(0, shuttle_angle, 0)
        self.cam_node.set_hpr(-shuttle_angle, 0, 0)
        print("Opening new screen with h=", -shuttle_angle)

    def destroy(self):
        self.gameEngine.closeWindow(self.window)
        self.camera.setActive(0)

    def set_width(self, incr):
        self.lens.setFilmSize(self.lens.getFilmSize() + incr)
        print("new width", self.lens.getFilmSize())

    def set_fov(self, incr):
        self.lens.setFov(self.lens.getFov() + incr)
        print("new fov", self.lens.getFov())

    def set_angle(self, incr):
        self.cam_node.set_h(self.cam_node.get_h() + incr)
        print("new angle :", self.cam_node.get_h())

    def get_camera(self):
        return self.cam_node

    def set_fullscreen(self, on=True):
        if on:
            self.props.set_size((self.res[0], self.res[1]))
            self.props.setOrigin(self.screen * self.res[0], 0)
            self.lens.setAspectRatio(float(self.res[0] / self.res[1]))
        else:
            self.props.set_size((800, 600))
            self.props.setOrigin(self.screen * self.res[0] + 100, 100)
            self.lens.setAspectRatio(4 / 3)
        self.window.requestProperties(self.props)
        print("SCREEN", self.screen, "\n\t res", self.res, "\n\t pos", self.props.getOrigin(), "\n\t size",
              self.props.getSize())
