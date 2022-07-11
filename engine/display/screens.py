from panda3d.core import WindowProperties, NodePath, LVector4f
from direct.gui.OnscreenText import OnscreenText, TextNode

from engine.utils.logger import Logger


class FakeScreen3D(object):
    def __init__(self, engine, screen_number, shuttle_angle=0, shift_x=0, shift_y=0.0):
        self._engine = engine
        self.screen = screen_number

        aspect_ratio = self._engine.params('screen_resolution')[0] / self._engine.params('screen_resolution')[1]

        self.cam_node = self._engine.make_camera(self._engine.win,
                                                 displayRegion=(0.2 * screen_number, 0.2 * (screen_number + 1), 0, 1),
                                                 aspectRatio=aspect_ratio,
                                                 )

        self.gui_cam_node = self._engine.make_camera2d(self._engine.win,
                                                       displayRegion=(0.2 * screen_number, 0.2 * (screen_number + 1), 0, 1),
                                                       cameraName=str(self.screen)
                                                       )

        self.lens = self.cam_node.node().getLens()
        self.lens.setFov(self._engine.params("cam_fov"))
        self.lens.setNear(0.1)

        self.cam_node.reparent_to(self._engine.shuttle.frame)

        self.cam_node.set_hpr(-shuttle_angle, 0, 0)
        self.cam_node.set_x(shift_x)
        self.cam_node.set_y(shift_y)

        self._text = None

        for dr in self._engine.win.get_display_regions():
            cam = dr.get_camera()
            if cam and "cam2d" in cam.name:
                dr.set_dimensions(0, 0.2, 0, 1)

    def display_text(self, text, pos_x=0.0, pos_y=0.0, scale=0.06):
        self._text = OnscreenText(text=text,
                                  align=TextNode.ACenter,
                                  mayChange=True,
                                  pos=(pos_x, pos_y),
                                  scale=(scale, 16/9 * scale),
                                  fg=LVector4f(1, 1, 1, 1),
                                  parent=self.gui_cam_node,
                                  )

    def set_angle(self, incr):
        self.cam_node.set_h(self.cam_node.get_h() + incr)
        Logger.info('new angle : {}'.format(self.cam_node.get_h()))

    def get_camera(self):
        return self.cam_node
#
#
# class Screen3D:
#     def __init__(self, engine, screen_number, shuttle_angle=0, shift_x=0, shift_y=0.0):
#         self._engine = engine
#
#         self.props = WindowProperties()
#         self.screen = screen_number
#         # hard-coded to avoid detection problems
#         self.res = [1920, 1080]
#
#         self.props.set_size(800, 600)
#         self.props.set_origin(100 + self.screen * self.res[0], 100)
#         self.props.set_undecorated(True)
#         self.props.set_foreground(False)
#
#         self.window = self._engine.openWindow(props=self.props, aspectRatio=float(800 / 600))
#
#         # getting the new camera
#         self.camera = self._engine.camList[-1].node()
#         self.cam_node = NodePath(self.camera)
#         self.cam_node.reparent_to(self._engine.shuttle.frame)
#         self.cam_node.set_x(shift_x)
#         self.cam_node.set_y(shift_y)
#         self.lens = self.camera.getLens()
#         self.lens.setFov(self._engine.params("cam_fov"))
#         self.lens.setNear(0.1)
#
#         # self.cam_node.set_hpr(0, shuttle_angle, 0)
#         self.cam_node.set_hpr(-shuttle_angle, 0, 0)
#         Logger.info('Opening new screen with h = {}'.format(-shuttle_angle))
#
#     def destroy(self):
#         self._engine.closeWindow(self.window)
#         self.camera.setActive(0)
#
#     def set_width(self, incr):
#         self.lens.setFilmSize(self.lens.getFilmSize() + incr)
#         Logger.info('new width : {}'.format(self.lens.getFilmSize()))
#
#     def set_fov(self, incr):
#         self.lens.setFov(self.lens.getFov() + incr)
#         Logger.info('new fov : {}'.format(self.lens.getFov()))
#
#     def set_angle(self, incr):
#         self.cam_node.set_h(self.cam_node.get_h() + incr)
#         Logger.info('new angle : {}'.format(self.cam_node.get_h()))
#
#     def get_camera(self):
#         return self.cam_node
#
#     def set_fullscreen(self, on=True):
#         if on:
#             self.props.set_size((self.res[0], self.res[1]))
#             self.props.setOrigin(self.screen * self.res[0], 0)
#             self.lens.setAspectRatio(float(self.res[0]/self.res[1]))
#         else:
#             self.props.set_size((800, 600))
#             self.props.setOrigin(self.screen * self.res[0] + 100, 100)
#             self.lens.setAspectRatio(4/3)
#         self.window.requestProperties(self.props)
#
#         d = {'resolution': self.res,
#              'pos': self.props.getOrigin(),
#              'size': self.props.getSize()}
#
#         Logger.info('Screen {0} infos : \n\t- {1}'.format(self.screen,
#                                                           '\n\t-'.join(['{0} : {1}'.format(k, d[k]) for k in d])))
#




