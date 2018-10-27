from Engine.ControlScreens.Screen import Screen
from direct.gui.OnscreenText import OnscreenText, TextNode


class ImageScreen(Screen):
    """
    A basic image screen. Displays an image and can set text over it.
    """
    def __init__(self, mainScreen, image_name):
        self._listen_to_input = False
        self.main_screen = mainScreen
        Screen.__init__(self, mainScreen,
                        image_name=image_name,
                        )
        self.texts = []
        self._update()

    def show_text(self, text, size=1, pos_x=0.0, pos_y=0.0, color=None, alpha_time=0.0):
        x_scale = 0.04 + 0.01 * size
        y_scale = x_scale * 16 / 9
        self.texts.append(OnscreenText(text=text,
                                       align=TextNode.ACenter,
                                       mayChange=False,
                                       pos=(pos_x, pos_y),
                                       scale=(x_scale, y_scale),
                                       font=self.main_screen.font,
                                       fg=color if color is not None else (1, 1, 1, 1),
                                       parent=self.main_screen.gui_render_node,
                                       ))

    def destroy(self):
        for t in self.texts:
            self.texts.pop().destroy()