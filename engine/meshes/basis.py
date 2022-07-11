from panda3d.core import GeomVertexData, GeomNode, GeomVertexFormat, Geom, GeomVertexWriter, GeomLines, NodePath


class CartesianBasis(GeomNode):
    def __init__(self, length=1., thickness=3.):
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

        NodePath(self).setRenderModeThickness(thickness)
        NodePath(self).setLightOff()
        NodePath(self).setColorOff()
        NodePath(self).set_bin('fixed', 9)
