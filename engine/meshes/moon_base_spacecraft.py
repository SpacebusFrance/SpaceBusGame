from random import random
from panda3d.core import NodePath, LVector3f, DirectionalLight
from engine.meshes.arrow import Arrow
from engine.utils.logger import Logger


class NewSpaceCraft:
    def __init__(self, base, quality=0, sun_angle=0):

        self.base = base
        folder = base("space_craft_folder")
        self.model = base.loader.load_model(folder + "core.egg")
        self.wheel = base.loader.load_model(folder + "wheel.egg")
        self.sp = base.loader.load_model(folder + "solar_panel.egg")

        self.model.reparentTo(base.render)
        self.wheel.reparentTo(self.model)

        self.rest_pos = NodePath("rest_pos")
        self.rest_pos.reparent_to(self.model)
        self.rest_pos.set_pos(LVector3f(0.0, -0.75, -0.24))

        # instanciating
        self.placeholders = []
        z1 = 0.4215
        z2 = 0.67935
        x1 = 1.136
        x2 = 2.6915
        for i, pos in enumerate(((x1, 0, z1),
                                 (x2, 0, z1),
                                 (-x1, 0, z1),
                                 (-x2, 0, z1),
                                 (x1, 0, z2),
                                 (x2, 0, z2),
                                 (-x1, 0, z2),
                                 (-x2, 0, z2))):
            self.placeholders.append(self.model.attachNewNode("p"+str(i)))
            self.placeholders[-1].set_pos(pos)
            self.sp.instanceTo(self.placeholders[-1])

        # wheel spinning task
        self.spin_velocity = 0.03
        if self.spin_velocity > 0.:
            self.spin_task = self.wheel.hprInterval(duration=1/self.spin_velocity, hpr=(360, 0, 0))
            self.spin_task.loop()

        # model light
        self.sun_light = DirectionalLight('SUN_LIGHT_ON_SPACE_CRAFT')
        self.sun_light.setColor((1., 1., 1., 1))
        self.sun_light_node = self.base.render.attachNewNode(self.sun_light)
        self.base.render.setLight(self.sun_light_node)

        if quality > 0:
            Logger.info(f'setting ShadowCaster quality to {quality *512}')
            self.sun_light.setShadowCaster(True, quality*512, quality*512)

        # self.sun_light.getLens().setFilmSize(60., 40.)
        self.sun_light.getLens().setFilmSize(6., 4.)
        self.sun_light.getLens().setNearFar(2., 6.)
        self.sun_light_node.lookAt(NodePath(self.base.sun))
        self.sun_light_node.set_pos(0, 3.5, 1)
        self.sun_light_node.set_h(self.sun_light_node.get_h() + 180)

        # self.model.set_r(180)
        self.model.set_p(-90 + sun_angle)
        # self.model.set_h(180)

        self.model.set_bin('fixed', 10)

        self.set_solar_panel_angle(70)

        # self.show_shuttle_rest_pos()
        # self.model.set_depth_write(0)
        # self.model.set_depth_test(0)

    def set_hpr(self, h, p, r):
        self.model.set_hpr(h, p, r)

    def get_shuttle_rest_pos(self):
        return self.rest_pos.get_pos()

    def get_shuttle_rest_hpr(self):
        return self.rest_pos.get_hpr()

    def get_connection_pos_and_hpr(self):
        node = NodePath('test')
        node.set_pos(0, 0, 0)
        node.set_hpr(0, 90, 0)
        node.reparent_to(self.rest_pos)
        node.wrtReparentTo(self.base.render)
        return node.get_pos(), node.get_hpr()

    def connect_to_shuttle(self, node):
        node.set_pos(0, 0, 0)
        node.set_hpr(0, 90, 0)
        node.reparent_to(self.rest_pos)
        node.wrtReparentTo(self.base.render)

    def show_shuttle_rest_pos(self):
        arrow = Arrow(self.base)
        arrow.set_color(0.5, 0.5, 0)
        arrow.reparent_to(self.rest_pos)
        arrow.look_at(LVector3f(0, 0, 1))
        # l = Lamp(self._engine, 'lamp', self.get_shuttle_rest_pos(), show_model=True)

    @staticmethod
    def get_shuttle_rest_direction():
        return LVector3f(1, 0, 0)

    def show_bounds(self):
        self.sun_light.showFrustum()
        for child in self.sun_light.getChildren():
            if child.name == "frustum":
                NodePath(child).setLightOff()
                NodePath(child).set_color(1, 1, 0, 1)
                NodePath(child).set_bin('fixed', 10)
        self.model.showTightBounds()

    def set_solar_panel_angle(self, angle):
        self.sp.set_p(angle)

    def solar_panel_increment(self, angle):
        self.sp.set_p(self.sp.get_p() + angle)

    def spin(self, angle, value):
        if angle == 'p':
            self.model.set_p(self.model.get_p() + value)
        elif angle == 'h':
            self.model.set_h(self.model.get_h() + value)
        elif angle == 'r':
            self.model.set_r(self.model.get_r() + value)

    def move_solar_panels(self, new_angle=None):
        if new_angle is None:
            new_angle = 180 * random()
        if 0 <= new_angle <= 180:
            angle = self.sp.get_h()
            time = (new_angle - angle)*0.1
            if time < 0:
                time = - time
            task = self.sp.hprInterval(duration=time, hpr=(0, new_angle, 0))
            task.start()

    def get_light(self):
        return self.sun_light_node

