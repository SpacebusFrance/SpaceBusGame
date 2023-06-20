from panda3d.core import LVector3f


class Asteroid(object):
    def __init__(self, base, scale=0.5):
        self.game_engine = base
        self.model = self.game_engine.loader.load_model(self.game_engine.get_option("asteroid_model"))
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