from random import random

from panda3d.core import CullFaceAttrib, DirectionalLight, LVector3f, NodePath, GeomNode, GeomVertexData, \
    GeomVertexFormat, Geom, GeomVertexWriter, GeomLines, LVector4f, PointLight, PandaNode, \
    GeomTristrips


class Flash(PointLight):
    def __init__(self, base, name, pos=None, color=None, show_model=True):
        PointLight.__init__(self, name)
        self.period = 1
        self.signal = 0.1
        self.base = base
        self.show_model = show_model

        self.base.taskMgr.add(self.flash, "Flash")
        self.node = self.base.render.attachNewNode(self)
        self.node.hide()
        self.setAttenuation((1, 0, 0.2))

        self.set_pos(pos)
        if show_model:
            print('showing model')
            self.model = self.base.loader.load_model("data/models/sphere.bam")
            self.model.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
            self.model.set_scale(1)
            self.model.setLightOff()
            self.model.reparentTo(self.node)

        self.set_global_color(color)

    def set_pos(self, pos=None):
        pos = pos if pos is not None else (0, 0, 0)
        self.node.set_pos(pos)

    def set_global_color(self, color=None):
        color = color if color is not None else (1, 1, 1, 1)
        self.node.set_color(color)
        if self.show_model:
            self.model.set_color(color)

    def flash(self, task):
        if task.time >= self.period:
            self.node.hide()
            self.base.render.clearLight(self.node)
            return task.again
        elif task.time >= self.period - self.signal:
            self.base.render.setLight(self.node)
            self.node.show()
        return task.cont


class Arrow:
    def __init__(self, gameEngine):
        self.gameEngine = gameEngine
        self.model = self.gameEngine.loader.load_model("data/models/arrow.egg")
        self.model.set_bin("fixed", 10)
        self.model.setLightOff()
        self.model.reparentTo(self.gameEngine.render)

    def set_pos(self, x, y, z):
        self.model.set_pos(LVector3f(x, y, z))

    def set_hpr(self, h, p, r):
        self.model.set_hpr(h, p, r)

    def set_color(self, r, g, b):
        self.model.set_color(LVector4f(r, g, b, 1.0))

    def look_at(self, element):
        self.model.look_at(element)

    def set_size(self, size):
        self.model.set_scale(size)

    def reparent_to(self, node):
        self.model.reparentTo(node)


class Lamp(PointLight):
    def __init__(self, base, name, pos=None, color=None, show_model=False):
        PointLight.__init__(self, name)
        self.base = base
        self.node = self.base.render.attachNewNode(self)
        self.set_pos(pos)
        self.base.render.setLight(self.node)
        self.set_color(color if color is not None else (1, 1, 1, 1))
        self.set_max_distance(0.3)
        self.set_attenuation((1, 0, 0.2))

        self.show_model = show_model

        if show_model:
            self.model = self.base.loader.load_model("data/models/sphere.bam")
            self.model.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
            self.model.set_scale(0.05)
            self.model.set_color(color if color is not None else (1, 1, 1, 1))
            self.model.setLightOff()
            self.model.set_bin("fixed", 10)
            self.model.reparentTo(self.node)

    def set_pos(self, pos=None):
        pos = pos if pos is not None else (0, 0, 0)
        self.node.set_pos(pos)


class NewSpaceCraft:
    def __init__(self, base, quality=0, sun_angle=0):

        self.base = base
        folder = base.params("space_craft_folder")
        self.model = base.loader.load_model(folder + "core.egg")
        self.wheel = base.loader.load_model(folder + "wheel.egg")
        self.sp = base.loader.load_model(folder + "solar_panel.egg")

        self.model.reparentTo(base.render)
        self.wheel.reparentTo(self.model)

        self.rest_pos = NodePath("rest_pos")
        self.rest_pos.reparent_to(self.model)
        self.rest_pos.set_pos(LVector3f(0.0, -0.75, -0.24))

        # self.wheel_lights = base.loader.load_model(folder + "wheel_lights.egg")
        # self.wheel_lights.set_color(1, 1, 0)
        # self.wheel_lights.reparentTo(self.wheel)
        # self.wheel_lights.setLightOff()

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
            self.placeholders.append(self.model.attachNewNode("p" + str(i)))
            self.placeholders[-1].set_pos(pos)
            self.sp.instanceTo(self.placeholders[-1])

        # wheel spinning task
        self.spin_velocity = 0.01
        if self.spin_velocity > 0.:
            self.spin_task = self.wheel.hprInterval(duration=1 / self.spin_velocity, hpr=(360, 0, 0))
            self.spin_task.loop()

        # model light
        self.sun_light = DirectionalLight('SUN_LIGHT_ON_SPACE_CRAFT')
        self.sun_light.setColor((1., 1., 1., 1))
        self.sun_light_node = self.base.render.attachNewNode(self.sun_light)
        # self.sun_light_node.setHpr(-135, 0, 0)
        self.base.render.setLight(self.sun_light_node)

        if quality > 0:
            print(quality * 512)
            self.sun_light.setShadowCaster(True, quality * 512, quality * 512)

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
        # l = Lamp(self.base, 'lamp', self.get_shuttle_rest_pos(), show_model=True)

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
        print("sp :", self.sp.get_p())

    def spin(self, angle, value):
        if angle == 'p':
            self.model.set_p(self.model.get_p() + value)
        elif angle == 'h':
            self.model.set_h(self.model.get_h() + value)
        elif angle == 'r':
            self.model.set_r(self.model.get_r() + value)
        print(self.model.get_hpr())

    def move_solar_panels(self, new_angle=None):
        if new_angle is None:
            new_angle = 180 * random()
        if 0 <= new_angle <= 180:
            angle = self.sp.get_h()
            time = (new_angle - angle) * 0.1
            if time < 0:
                time = - time
            task = self.sp.hprInterval(duration=time, hpr=(0, new_angle, 0))
            task.start()

    def get_light(self):
        return self.sun_light_node


class AsteroidCloud:
    def __index__(self, base, nb_asteroids):
        self.game_engine = base
        self.asteroids = []

    def spawn(self, t=None):
        pass

    def unspawn(self, t=None):
        pass


class Asteroid:
    def __init__(self, base, scale=0.5):
        self.game_engine = base
        self.model = self.game_engine.loader.load_model(self.game_engine.params("asteroid_model"))
        self.model.reparentTo(self.game_engine.render)
        self.model.set_bin('fixed', 10)
        self.model.set_scale(scale)
        self.model.hide()
        self.rotate_task = None
        self.move_task = None

    def spawn(self, t=None, spin_time=2, init_pos=None, end_pos=None):
        self.rotate_task = self.model.hprInterval(duration=spin_time, hpr=(0, 360, 0))
        self.rotate_task.loop()
        self.move_task = self.model.posInterval(40,
                                                end_pos if end_pos is not None else LVector3f(-1500, -140, -2),
                                                startPos=init_pos if init_pos is not None else LVector3f(1500, 150, 2))
        self.move_task.start()
        self.model.show()
        self.game_engine.taskMgr.doMethodLater(40, self.unspawn, name="asteroid_end")

    def unspawn(self, t=None):
        self.model.hide()
        self.rotate_task.finish()
        self.move_task.finish()


# class SpaceCraft:
#     def __init__(self, base, quality=0, pos=None):
#         self.frame = NodePath("spacecraft_frame")
#         self.frame.reparent_to(base.render)
#
#         # align to axis
#         # self.frame.set_r(-90)
#
#         self.base = base
#         # self.model = base.loader.load_model("model/space_odyssey/space_odyssey_new.bam")
#         # self.model = base.loader.load_model("model/new_spaceship/new_spaceship.bam")
#         self.model = base.loader.load_model("model/nasa_warp/model.bam")
#
#         self.model.reparentTo(self.frame)
#         # # model scale
#         # self.model.set_scale(0.005)
#         # self.model.set_scale(0.1)
#         # # model offset
#         self.model.set_pos(0, 0, -102)
#         # model rotation
#         self.model.set_r(180)
#
#         self.spin_velocity = 0.1
#
#         # model light
#         self.sun_light = DirectionalLight('SUN_LIGHT_ON_SPACE_CRAFT')
#         self.sun_light.setColor((1., 1., 1., 1))
#         self.sun_light_node = self.base.render.attachNewNode(self.sun_light)
#         self.sun_light_node.setHpr(-135, 0, 0)
#         self.base.render.setLight(self.sun_light_node)
#
#         if quality > 0:
#             print(quality*512)
#             self.sun_light.setShadowCaster(True, quality*512, quality*512)
#
#         self.sun_light.getLens().setFilmSize(60., 40.)
#         self.sun_light.getLens().setNearFar(1., 60.)
#
#         self.sun_light.show_frustum()
#
#         # self.base.taskMgr.add(self.spin_task, "SpaceCraftSpin")
#
#         self.set_pos((0, 0, 0))
#
#         self.model.set_bin('fixed', 10)
#         # self.model.set_depth_write(0)
#         # self.model.set_depth_test(0)
#
#     def get_light(self):
#         return self.sun_light_node
#
#     def spin_task(self, task):
#         self.model.set_h(self.model.get_h() + self.spin_velocity)
#         return task.cont
#
#     def set_pos(self, pos):
#         self.frame.set_pos(LVector3f(pos))
#         self.sun_light_node.set_pos(LVector3f(pos) - LVector3f(20, -20, 0))


class Grid(GeomNode):
    def __init__(self, x_extend=None, y_extend=None, x_size=1, y_size=1, z=-0.01, tickness=1., name='Grid',
                 x_color=None,
                 y_color=None):
        GeomNode.__init__(self, name)
        if x_color is None:
            x_color = LVector4f(1.0, 1.0, 1.0, 1.0)

        if y_color is None:
            y_color = LVector4f(1.0, 1.0, 1.0, 1.0)

        if x_extend is None:
            x_extend = [0, 10]
        if y_extend is None:
            y_extend = [0, 10]

        self.vertexData = GeomVertexData("Chunk", GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.color = GeomVertexWriter(self.vertexData, 'color')

        self.mesh = Geom(self.vertexData)
        self.lines = GeomLines(Geom.UHStatic)

        nb_lines_x = int((x_extend[1] - x_extend[0]) / x_size)
        nb_lines_y = int((y_extend[1] - y_extend[0]) / y_size)

        vertex_nb = 0
        for ix in range(nb_lines_x):
            for iy in range(nb_lines_y):
                x = x_extend[0] + ix * x_size
                y = y_extend[0] + iy * y_size

                self.vertex.addData3f(x, y, z)
                self.color.addData4f(x_color)

                self.vertex.addData3f(x + x_size, y, z)
                self.color.addData4f(x_color)

                self.vertex.addData3f(x, y, z)
                self.color.addData4f(y_color)

                self.vertex.addData3f(x, y + y_size, z)
                self.color.addData4f(y_color)

                self.lines.add_vertices(vertex_nb, vertex_nb + 1, vertex_nb + 2, vertex_nb + 3)
                vertex_nb += 4

        self.lines.closePrimitive()
        self.mesh.addPrimitive(self.lines)
        self.addGeom(self.mesh)

        NodePath(self).setRenderModeThickness(tickness)
        NodePath(self).setLightOff()
        NodePath(self).setColorOff()
        NodePath(self).set_bin('fixed', 8)


class CartesianBasis(GeomNode):
    def __init__(self, length=1., tickness=3.):
        GeomNode.__init__(self, "Basis")
        self.vertexData = GeomVertexData("Basis", GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.color = GeomVertexWriter(self.vertexData, 'color')
        self.mesh = Geom(self.vertexData)
        self.lines = GeomLines(Geom.UHStatic)

        self.vertex.addData3f(0.0, 0.0, 0.0)
        self.color.addData4f(1.0, 0.0, 0.0, 1.0)
        self.vertex.addData3f(length, 0.0, 0.0)
        self.color.addData4f(1.0, 0.0, 0.0, 1.0)
        self.lines.add_vertices(0, 1)

        self.vertex.addData3f(0.0, 0.0, 0.0)
        self.color.addData4f(0.0, 1.0, 0.0, 1.0)
        self.vertex.addData3f(0.0, length, 0.0)
        self.color.addData4f(0.0, 1.0, 0.0, 1.0)
        self.lines.add_vertices(2, 3)

        self.vertex.addData3f(0.0, 0.0, 0.0)
        self.color.addData4f(0.0, 0.0, 1.0, 1.0)
        self.vertex.addData3f(0.0, 0.0, length)
        self.color.addData4f(0.0, 0.0, 1.0, 1.0)
        self.lines.add_vertices(4, 5)

        self.lines.closePrimitive()
        self.mesh.addPrimitive(self.lines)
        self.addGeom(self.mesh)

        NodePath(self).setRenderModeThickness(tickness)
        NodePath(self).setLightOff()
        NodePath(self).setColorOff()
        NodePath(self).set_bin('fixed', 9)


class SkyDome:
    def __init__(self, base_object):
        self.model = base_object.loader.load_model(base_object.params("sky_dome_model"))

        self.model.reparentTo(base_object.render)
        # self.skysphere.set_color(0.5, 0.5, 0.5)
        self.model.set_pos(0, 0, 0)
        self.model.set_scale(10000)

        self.model.set_bin('fixed', 0)
        self.model.set_depth_write(0)
        self.model.set_depth_test(0)

    def set_color(self, color):
        self.model.set_color(color)

    def set_color_scale(self, color):
        self.model.set_color_scale(color)

    def set_luminosity(self, l):
        self.model.set_color_scale((l, l, l, 1.0))


class Moon3D:
    def __init__(self, base_object):
        self.model = base_object.loader.load_model(base_object.params("moon_3D"))

        self.model.reparentTo(base_object.render)
        # self.skysphere.set_color(0.5, 0.5, 0.5)
        self.model.set_pos(0, -100, 0)
        self.model.set_scale(200)
        # #
        # self.model.set_bin('fixed', 0)
        # self.model.set_depth_write(0)
        # self.model.set_depth_test(0)

    def set_color(self, color):
        self.model.set_color(color)

    def set_color_scale(self, color):
        self.model.set_color_scale(color)

    def set_luminosity(self, l):
        self.model.set_color_scale((l, l, l, 1.0))


class Earth(PandaNode):
    def __init__(self, base_object):
        PandaNode.__init__(self, "Earth")

        self.geom = GeomNode("earth")
        self.vertexData = GeomVertexData("Basis", GeomVertexFormat.getV3cpt2(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.tex_coord = GeomVertexWriter(self.vertexData, 'texcoord')
        self.mesh = Geom(self.vertexData)
        self.tris = GeomTristrips(Geom.UHStatic)

        size = 200
        z = -1000
        dx = 0
        dy = -200

        self.vertex.addData3f(z, size + dx, -size + dy)
        self.tex_coord.addData2f(1.0, 0.0)

        self.vertex.addData3f(z, -size + dx, -size + dy)
        self.tex_coord.addData2f(1.0, 1.0)

        self.vertex.addData3f(z, size + dx, size + dy)
        self.tex_coord.addData2f(0.0, 0.0)

        self.vertex.addData3f(z, -size + dx, size + dy)
        self.tex_coord.addData2f(0.0, 1.0)

        self.tris.add_vertices(1, 0, 3, 2)

        self.tris.closePrimitive()
        self.mesh.addPrimitive(self.tris)
        self.geom.addGeom(self.mesh)

        self.node = base_object.render.attachNewNode(self.geom)
        self.node.set_p(90)
        # self.node.set_h(90)

        self.texture = base_object.loader.loadTexture(base_object.params("earth_texture"))
        self.node.set_texture(self.texture)

        self.node.setLightOff()
        self.node.setColorOff()
        self.node.setTransparency(True)

        # self.node.set_bin('fixed', 3)
        # self.node.set_depth_write(0)
        # self.node.set_depth_test(0)
        # self.node.setBillboardPointEye()

    def move(self, dx):
        self.node.set_pos(self.node.get_pos() + dx)


class Moon(PandaNode):
    def __init__(self, base_object):
        PandaNode.__init__(self, "Moon")

        self.geom = GeomNode("Moon")
        self.vertexData = GeomVertexData("Basis", GeomVertexFormat.getV3cpt2(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.tex_coord = GeomVertexWriter(self.vertexData, 'texcoord')
        self.mesh = Geom(self.vertexData)
        self.tris = GeomTristrips(Geom.UHStatic)

        size = 700
        z = 1000
        dx = 0
        dy = 500

        self.vertex.addData3f(z, size + dx, -size + dy)
        self.tex_coord.addData2f(1.0, 0.0)

        self.vertex.addData3f(z, -size + dx, -size + dy)
        self.tex_coord.addData2f(1.0, 1.0)

        self.vertex.addData3f(z, size + dx, size + dy)
        self.tex_coord.addData2f(0.0, 0.0)

        self.vertex.addData3f(z, -size + dx, size + dy)
        self.tex_coord.addData2f(0.0, 1.0)

        self.tris.add_vertices(0, 1, 2, 3)

        self.tris.closePrimitive()
        self.mesh.addPrimitive(self.tris)
        self.geom.addGeom(self.mesh)

        self.node = base_object.render.attachNewNode(self.geom)
        self.node.set_p(90)
        # self.node.set_r(-90)
        # self.node.set_h(90)

        # self.node.set_p(90)
        # self.node.set_scale(500)

        # self.node.set_pos(1.7 * self.node.get_scale()[0],
        #                   0,
        #                   self.node.get_scale()[0] * 0.5)

        self.texture = base_object.loader.loadTexture(base_object.params("moon_texture"))
        self.node.set_texture(self.texture)

        self.node.setLightOff()
        self.node.setColorOff()
        self.node.setTransparency(True)

        self.node.set_bin('fixed', 2)
        self.node.set_depth_write(0)
        self.node.set_depth_test(0)
        # self.node.lookAt(0, 0, 0)

    def move(self, dx):
        self.node.set_pos(self.node.get_pos() + dx)


class Sun(PandaNode):
    def __init__(self, base_object):
        PandaNode.__init__(self, "Sun")

        self.geom = GeomNode("Sun")
        self.vertexData = GeomVertexData("Basis", GeomVertexFormat.getV3cpt2(), Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.tex_coord = GeomVertexWriter(self.vertexData, 'texcoord')
        self.mesh = Geom(self.vertexData)
        self.tris = GeomTristrips(Geom.UHStatic)

        self.vertex.addData3f(0.0, 0.0, 0.0)
        self.tex_coord.addData2f(1.0, 0.0)

        self.vertex.addData3f(1.0, 0.0, 0.0)
        self.tex_coord.addData2f(1.0, 1.0)

        self.vertex.addData3f(0.0, 1.0, 0.0)
        self.tex_coord.addData2f(0.0, 0.0)

        self.vertex.addData3f(1.0, 1.0, 0.0)
        self.tex_coord.addData2f(0.0, 1.0)

        self.tris.add_vertices(0, 1, 2, 3)

        self.tris.closePrimitive()
        self.mesh.addPrimitive(self.tris)
        self.geom.addGeom(self.mesh)

        self.node = base_object.render.attachNewNode(self.geom)
        self.node.set_r(-90)
        self.node.set_h(90)
        self.node.set_scale(40)

        self.node.set_pos(0, 500, 0)

        self.texture = base_object.loader.loadTexture(base_object.params("sun_texture"))
        self.node.set_texture(self.texture)

        self.node.setLightOff()
        self.node.setColorOff()
        self.node.setTransparency(True)

        self.node.set_bin('fixed', 1)
        self.node.set_depth_write(0)
        self.node.set_depth_test(0)

        self.node.setBillboardPointEye()

    def move(self, dx):
        self.node.set_pos(self.node.get_pos() + dx)
