from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText, TextNode, TransparencyAttrib
from panda3d.core import LVector4f


class InfoOverScreen:
    """
    The popup window class
    """
    def __init__(self, MainScreen, text=""):
        self.main_screen = MainScreen
        self._image = OnscreenImage(image=self.main_screen.image_path + "comm.png",
                                    pos=(0, 0, 0),
                                    parent=self.main_screen.gui_render_node,
                                    )
        # image in front
        self._image.set_bin("fixed", 10)
        self._image.setTransparency(TransparencyAttrib.MAlpha)
        self._text = OnscreenText(text=text,
                                  align=TextNode.ALeft,
                                  mayChange=True,
                                  pos=self.main_screen.gimp_pos(210, 230),
                                  scale=(0.06, 0.08),
                                  fg=LVector4f(1, 1, 1, 1),
                                  parent=self._image,
                                  wordwrap=20,
                                  )
        self._show = False
        self._image.hide()
        self._text.hide()

    def is_on_screen(self):
        """
        @return: True if the popup is on screen. False otherwise
        """
        return self._show

    def show(self, t=None):
        """
        Shows the window
        @param t: a mute parameter allowing to call it in a doMethodLater
        """
        self._show = True
        self._image.show()
        self._text.show()
        self.main_screen.update()

    def hide(self, t=None):
        """
        Hides the window
        @param t: a mute parameter allowing to call it in a doMethodLater
        """
        self._show = False
        self._image.hide()
        self._text.hide()
        self.main_screen.update()

    def set_text(self, text, end="\n\n... (Entrée pour continuer) ..."):
        """
        Sets the text of the popup.
        @param text: the text
        @param end: the end text.
        """
        self._text["text"] = text + end
        if self._show:
            self.main_screen.update()