from direct.filter.CommonFilters import CommonFilters
from panda3d.core import CardMaker, NodePath, Shader, Point2, Vec3

SHADER = Shader.load(
    Shader.SL_GLSL,
    vertex='data/shaders/flare-vert.glsl',
    fragment='data/shaders/flare-frag.glsl'
)


class FakeScreen3D:
    def __init__(self, engine, screen_number, shuttle_angle=0, shift_x=0, shift_y=0.0):
        self._engine = engine
        self.screen = screen_number

        size_x = self._engine.get_option('screen_resolution')[0]
        size_y = self._engine.get_option('screen_resolution')[1]
        x0, x1 = 0.2 * screen_number, 0.2 * (screen_number + 1)
        self.cam_node = self._engine.make_camera(
            self._engine.win,
            displayRegion=(x0, x1, 0, 1),
            aspectRatio=size_x / size_y,
        )

        self.lens = self.cam_node.node().getLens()
        self.lens.setFov(self._engine.get_option("cam_fov"))
        self.lens.setNear(0.1)

        self.cam_node.reparent_to(self._engine.shuttle.frame)

        self.cam_node.set_hpr(-shuttle_angle, 0, 0)
        self.cam_node.set_x(shift_x)
        self.cam_node.set_y(shift_y)

        # bloom effect : glow on light colors
        if engine.get_option('use_bloom_effect'):
            filters = CommonFilters(engine.win, self.cam_node)
            filters.set_bloom(
                size="medium",
            )

        # sun shader
        if engine.get_option('use_sun_shader'):
            cm = CardMaker(f'card_{screen_number}')
            cm.setFrame(2 * x0 - 1, 2 * x1 - 1, - 1, 1)

            # Create a node path for the card
            card = NodePath(cm.generate())

            # Render the card in the 2D space
            card.setDepthWrite(False)
            card.setDepthTest(False)
            card.setBin("unsorted", 0)
            card.reparentTo(engine.render2d)
            card.set_transparency(True)

            card.set_shader(SHADER)
            card.set_shader_inputs(
                iResolution=(size_x, size_y),
                iShift=(x0 / (x1 - x0), 0),
                iPos=(10, 10)
            )

            def update(task):
                coord2d = Point2()
                self.lens.project(
                    engine.sun.node.get_pos(self.cam_node),
                    coord2d
                )
                facing = engine.render.getRelativeVector(self.cam_node, Vec3.forward()) \
                    .dot(engine.sun.node.get_pos() - self.cam_node.get_pos())
                if facing >= 0:
                    card.set_shader_input(
                        'iPos',
                        (
                            0.5 * coord2d[0],
                            0.5 * coord2d[-1]
                        )
                    )
                return task.cont

            engine.add_task(update, f'update_{screen_number}')

    def get_camera(self):
        return self.cam_node
