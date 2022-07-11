from panda3d.core import CullFaceAttrib, PointLight


class Flash(PointLight):
    def __init__(self, base, name, pos=None, color=None, show_model=True):
        PointLight.__init__(self, name)
        self.period = 1
        self.signal = 0.1
        self._engine = base
        self.show_model = show_model

        self._engine.taskMgr.add(self.flash, "Flash")
        self.node = self._engine.render.attachNewNode(self)
        self.node.hide()
        self.setAttenuation((1, 0, 0.2))

        self.set_pos(pos)
        if show_model:
            self.model = self._engine.loader.load_model("data/models/sphere.bam")
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
            self._engine.render.clearLight(self.node)
            return task.again
        elif task.time >= self.period - self.signal:
            self._engine.render.setLight(self.node)
            self.node.show()
        return task.cont
