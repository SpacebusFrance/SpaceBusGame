from panda3d.core import PointLight, CullFaceAttrib


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