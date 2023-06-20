

class SkyDome(object):
    def __init__(self, base_object):
        self.model = base_object.loader.load_model(base_object.get_option("sky_dome_model"))

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