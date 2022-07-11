from panda3d.core import LVector3f, LVector4f


class Arrow(object):
    def __init__(self, gameEngine):
        self.gameEngine = gameEngine
        self.model = self.gameEngine.loader.load_model("../../data/models/arrow.egg")
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