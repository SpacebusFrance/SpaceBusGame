from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText

from engine import __version__ as version
from engine.utils.event_handler import EventObject


class MainScreen(EventObject):
    """
    Base class for main game screen
    """
    def __init__(self, gui_engine, image: str = 'back.png', background_color=None, show_version: bool = False):
        super().__init__()

        self.gui = gui_engine
        self.engine = gui_engine.engine

        self._formatters = {bool: lambda x: '\1green\1ON\2' if x else '\1red\1OFF\2',
                            float: lambda x: '\1golden\1{:.1f}\2'.format(x),
                            int: lambda x: '\1golden\1{}\2'.format(x),
                            str: lambda x: self.gui.process_text('\1light\1${}$\2'.format(x))}

        self._texts = dict()
        self._large_pad = 0.1
        self._small_pad = 0.01
        self._text_scale = 0.07
        self._icon_size = 0.05

        ar = self.engine.get_option('screen_resolution')[0] / self.engine.get_option('screen_resolution')[1]
        self._background = DirectFrame(
            image=(self.engine.get_option('image_path') + image) if image is not None else None,
            parent=self.engine.aspect2d,
            image_scale=(ar, 1, 1),
            frameColor=background_color if background_color is not None else (0, 0, 0, 0),
            frameSize=(-ar, ar, -1, 1)
        )
        if show_version:
            t = OnscreenText(text=f'version {version}', parent=self._background,
                             pos=(-0.8 * ar, -0.9), scale=0.07, fg=(0.8, 0.7, 0.6, 0.8))
            t.setBin('gui-popup', 1)

    def destroy(self):
        self._background.remove_node()

    def __getattr__(self, item):
        """
        Propagate all calls to the background image
        """
        return self._background.__getattribute__(item)

    def set_background_color(self, color):
        """
        Set the background color

        Args:
            color: the color to set
        """
        self._background.set_color(self.gui.colors[color] if isinstance(color, str) else color)

    def notify_update(self, key):
        """
        Notify that a soft or hard state was updated and update the GUI accordingly

        Args:
            key (str): the name of the state to update
        """
        if key in self._texts:
            if isinstance(self._texts[key], OnscreenText):
                # update the text
                self._texts[key].setText(text=self._format(key, True))
            else:
                # it is a gauge, set the value between 0 and 1
                self._texts[key].set_value(self._get_value(key) / 100)

    def _format(self, name, value=False):
        """
        Format states' name conveniently to display them on the screen

        Args:
            name (str): the name of the state to set
            value (bool): if True, the displayed value is not the name of the state but its value

        Returns:
            a formatted :obj:`str`
        """
        if value:
            name = self._get_value(name)
        return self._formatters[type(name)](name)

    def _get_value(self, key):
        """
        A shortcut to get a shuttle state value

        Args:
            key (str): the name of the state

        Returns:
            its value
        """
        return self.engine.state_manager.get_state(key).get_value() # get_soft_state(key)

    def make(self):
        """
        Build the screen
        """
        pass
