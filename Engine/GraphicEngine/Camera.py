import numpy as num
from direct.showbase import DirectObject
from panda3d.core import LVector3f

TO_RAD = 0.017453293
TO_DEG = 57.295779513


class FreeCameraControl(DirectObject.DirectObject):
    def __init__(self, base_object, cam_node=None):
        DirectObject.DirectObject.__init__(self)

        self.base_object = base_object
        base_object.disableMouse()

        if cam_node is None:
            self.camera = base_object.camera
        else:
            self.camera = cam_node

        self.camera.reparent_to(self.base_object.render)
        self.mwn = base_object.mouseWatcherNode

        self.target = LVector3f(0, 0, 0)

        self._phi = 0.
        self._theta = num.pi / 2
        self._r = 100.
        # u follows the line of sight
        self._u = LVector3f(0.0, 0.0, 0.0)
        # n is othogonal to the camera
        self._n = LVector3f(0.0, 0.0, 0.0)
        # k gives the direction of the camera in the X, Y plane
        self._k = LVector3f(0., 0., 0.)
        self.update_cam()

        self._mx, self._my = 0, 0

        self.can_spin_vertically = True

        self.keyboard = False
        self.spinning = False
        self.sliding = False
        self.velocity = 5
        self.slide_velocity = 30

        self.keyboard_velocity = 1.5
        self.keyboard_spin = 0.03

        self.panZoneSize = .15
        self.use_panning = False
        self._slide_x, self._slide_y = 0, 0

        self._config_mousse()
        self.base_object.taskMgr.add(self.cam_move_task, 'cam_move_task')

    def set_fov(self, fov):
        self.base_object.camLens.setFov(fov)

    def use_keyboard(self):
        self.keyboard = True
        self._config_keyboard()

    def use_mousse(self):
        self.keyboard = False
        self._config_mousse()

    def _config_keyboard(self):
        self.ignore_all()
        self.accept('space', self.space_key)
        self.accept('enter', self.enter_key)

    def _config_mousse(self):
        self.accept("mouse2", self.start_spin)
        self.accept("mouse2-up", self.stop_spin)

        self.accept("mouse3", self.start_sliding)
        self.accept("mouse3-up", self.stop_sliding)

        self.accept("wheel_up", lambda: self.set_r(0.9 * self._r))
        self.accept("wheel_down", lambda: self.set_r(1.1 * self._r))

    def reset_camera(self):
        self.target = LVector3f(0, 0, 0)

    def start_sliding(self):
        self.sliding = True
        if self.mwn.hasMouse():
            mpos = self.mwn.getMouse()
            self._slide_x = mpos.getX()
            self._slide_y = mpos.getY()

    def stop_sliding(self):
        self.sliding = False
        self._slide_x = 0.0
        self._slide_y = 0.0

    def start_spin(self):
        self.spinning = True

    def stop_spin(self):
        self.spinning = False

    def set_r(self, r):
        self._r = r
        self.look_to_target()

    def update_cam(self):
        self.update_euler_angles()
        self.look_to_target()

    def update_euler_angles(self):
        h = 90 + self._phi * 180. / num.pi
        p = - self._theta * 180 / num.pi
        self.camera.setHpr(h, p, 180)
        self.compute_unit_vectors()

    def compute_unit_vectors(self):
        self._u = LVector3f(-num.cos(self._phi) * num.cos(self._theta),
                            -num.sin(self._phi) * num.cos(self._theta),
                            -num.sin(self._theta))
        self._n = LVector3f(-num.sin(self._phi), num.cos(self._phi), 0.0)
        self._k = LVector3f(-num.cos(self._phi), -num.sin(self._phi), 0.0)

    def set_target(self, target):
        self.target = target
        self.look_to_target()

    def look_to_target(self):
        self.camera.setPos(self.target - self._u * self._r)

    def set_theta(self, theta):
        self._theta = theta
        self.update_euler_angles()

    def set_phi(self, phi):
        self._phi = phi
        self.update_euler_angles()

    def spin_around_target(self, d_phi=0.0, d_theta=0.0):
        self._phi += d_phi
        self._theta += d_theta
        self.update_cam()

    def move(self, dx=0.0, dy=0.0):
        dv = LVector3f(-dx * num.sin(self._phi) - dy * num.cos(self._phi),
                       dx * num.cos(self._phi) - dy * num.sin(self._phi),
                       0.0)
        self.camera.setPos(self.camera.getPos() + dv)
        self.target = LVector3f(self.target + dv)

    def space_key(self):
        self.reset_camera()

    def enter_key(self):
        selected_object = self.base_object.picker.get_selected_object()
        if selected_object is not None:
            self.set_target(selected_object.getPos())

    def cam_move_task(self, task):
        if not self.keyboard and self.mwn.hasMouse():
            mpos = self.mwn.getMouse()
            if self.spinning:
                if self.can_spin_vertically:
                    self.spin_around_target(d_phi=self._mx - mpos.getX(), d_theta=- self._my + mpos.getY())
                else:
                    self.spin_around_target(d_phi=self._mx - mpos.getX())
            elif self.sliding:
                self.move(dx=- self.slide_velocity * (mpos.getX() - self._slide_x),
                          dy=- self.slide_velocity * (mpos.getY() - self._slide_y))
                self._slide_x = mpos.getX()
                self._slide_y = mpos.getY()
            elif self.use_panning:
                dy = 0.
                dx = 0.
                if mpos.getY() > (1 - self.panZoneSize):
                    dy = mpos.getY() + self.panZoneSize - 1
                elif mpos.getY() < (-1 + self.panZoneSize):
                    dy = mpos.getY() + 1 - self.panZoneSize

                if mpos.getX() > (1 - self.panZoneSize):
                    dx = mpos.getX() + self.panZoneSize - 1
                elif mpos.getX() < (-1 + self.panZoneSize):
                    dx = mpos.getX() + 1 - self.panZoneSize

                if dx != 0.0 or dy != 0.0:
                    self.move(self.velocity * dx, self.velocity * dy)
            self._mx = mpos.getX()
            self._my = mpos.getY()
        elif self.keyboard:
            is_down = self.mwn.is_button_down
            if is_down('arrow_left') or is_down('q'):
                self.move(dx=- self.keyboard_velocity)
            if is_down('arrow_right') or is_down('d'):
                self.move(dx=self.keyboard_velocity)
            if is_down("arrow_up") or is_down('z'):
                self.move(dy=self.keyboard_velocity)
            if is_down('arrow_down') or is_down('s'):
                self.move(dy=-self.keyboard_velocity)
            if is_down('a'):
                self.spin_around_target(d_phi=self.keyboard_spin)
            if is_down('e'):
                self.spin_around_target(d_phi=-self.keyboard_spin)
            if is_down('page_up'):
                self.set_r(0.95 * self._r)
            if is_down('page_down'):
                self.set_r(1.05 * self._r)
        return task.cont
