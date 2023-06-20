from panda3d.core import Geom, GeomTristrips, GeomVertexWriter, GeomVertexFormat, GeomVertexData, GeomNode, PandaNode


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

        self.texture = base_object.loader.loadTexture(base_object.get_option("sun_texture"))
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