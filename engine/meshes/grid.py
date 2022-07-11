from panda3d.core import GeomNode, LVector4f, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomLines, \
    NodePath


class Grid(GeomNode):
    def __init__(self, x_extend=None, y_extend=None, x_size=1, y_size=1, z=-0.01, thickness=1., name='Grid',
                 x_color=None, y_color=None):
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

        nb_lines_x = int((x_extend[1] - x_extend[0])/x_size)
        nb_lines_y = int((y_extend[1] - y_extend[0])/y_size)

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

        NodePath(self).setRenderModeThickness(thickness)
        NodePath(self).setLightOff()
        NodePath(self).setColorOff()
        NodePath(self).set_bin('fixed', 8)
