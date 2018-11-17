from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib


class LoadIcon:
    """
    A spinning icon.
    """
    def __init__(self, mainScreen, x=0.0, y=0.0):
        self.main_screen = mainScreen
        self._image = OnscreenImage(image=self.main_screen.image_path + "load_icon.png",
                                    pos=(x, 0, y),
                                    parent=self.main_screen.gameEngine.render2d,
                                    scale=(0.07, 1, 0.07)
                                    )
        self._image.setTransparency(TransparencyAttrib.MAlpha)
        self.spin_task = None
        self._image.hide()

    def set_pos(self, x, y):
        """
        Sets the position of the icon
        @param x: the relative x in the screen
        @param y: the relative y in the screen
        """
        self._image.set_r(0)
        self._image.set_pos(x, 0, y)

    def start(self):
        """
        Starts the spinning animation and shows it.
        """
        self._image.set_r(0)
        self._image.show()
        self.spin_task = self._image.hprInterval(duration=2, hpr=(0, 0, 360))
        self.spin_task.loop()

    def stop(self):
        """
        Stops the spinning animation and hides it.
        @return:
        """
        self.spin_task.finish()
        self._image.hide()