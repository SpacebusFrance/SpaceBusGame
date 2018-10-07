from direct.gui.OnscreenText import OnscreenText, WindowProperties, NodePath, TextNode


class InfoScreen:
    def __init__(self, gameEngine, width=600, height=400):
        self.gameEngine = gameEngine
        self.elements = []
        self.font = gameEngine.loader.loadFont('data/fonts/Prototype.ttf')

        wp = WindowProperties()
        # x = 600
        # y = 400
        wp.setSize(width, height)
        wp.setOrigin(500, 500)
        self.window = self.gameEngine.openWindow(props=wp, aspectRatio=float(height / width))

        # self.window.setBackgroundColor(0, 0, 0)
        self.gameEngine.setBackgroundColor(0.15, 0.2, 0.15, 0, win=self.window)

        # disable the new camera
        self.gameEngine.camList[-1].node().setActive(0)

        # my render node
        self.gui_render_node = NodePath('gui_render')
        self.gui_render_node.setDepthWrite(0)
        self.gui_render_node.setDepthTest(0)
        self.gui_render_node.setMaterialOff(1)
        self.gui_render_node.setTwoSided(1)
        self.gui_camera = self.gameEngine.makeCamera2d(self.window)
        self.gui_camera.reparentTo(self.gui_render_node)

        scale = 0.08
        self.text_r = OnscreenText(text="", pos=(-1, 0.9), scale=scale, fg=(0.06, 0.73, 0.22, 1.0), bg=(0, 0, 0, 0),
                                   mayChange=False,
                                   align=TextNode.ABoxedLeft,
                                   font=self.font,
                                   parent=self.gui_render_node,
                                   wordwrap=int(0.95 / scale))
        self.update()

    def update(self):
        self.window.setActive(True)
        for i in range(4):
            self.gameEngine.graphicsEngine.render_frame()
        self.window.setActive(False)

    def right_text(self, text):
        print('setting text :', text)
        self.text_r["text"] = text
        self.update()

    def add_text(self, text, pos):
        textObject = OnscreenText(text=text, pos=pos, scale=0.1, fg=(0.06, 0.73, 0.22, 1.0), bg=(0, 0, 0, 0),
                                  mayChange=True,
                                  align=TextNode.ABoxedLeft,
                                  font=self.font,
                                  parent=self.gui_render_node,
                                  wordwrap=10)
        self.elements.append(textObject)
        return textObject
