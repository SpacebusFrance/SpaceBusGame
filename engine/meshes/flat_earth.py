from panda3d.core import PandaNode, GeomNode, GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomTristrips


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

        self.texture = base_object.loader.loadTexture(base_object.get_option("earth_texture"))
        self.node.set_texture(self.texture)

        self.node.setLightOff()
        self.node.setColorOff()
        self.node.setTransparency(True)

        self.node.set_bin('fixed', 3)
        self.node.set_depth_write(0)
        self.node.set_depth_test(0)
        # self.node.setBillboardPointEye()

    def move(self, dx):
        self.node.set_pos(self.node.get_pos() + dx)