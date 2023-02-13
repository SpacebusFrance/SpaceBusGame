import os

from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib, NodePath


class BaseWidget:
    shadows_path = 'data/gui/shadow'
    _selected_button = None

    def __init__(self,
                 gui_engine,
                 shadow_scale=0.05):
        self._gui_engine = gui_engine
        self._widget = None
        self._shadow_scale = shadow_scale

    def play_sound(self, sound_name: str) -> None:
        """
        Plays a sound file
        """
        self._gui_engine.engine.sound_manager.play_sfx(sound_name, avoid_playing_twice=False)

    def color(self, color_name):
        """
        Get the globally defined color

        Args:
            color_name (str): the name of the color
        """
        return self._gui_engine.colors[color_name]

    def __getattr__(self, item):
        if self._widget is not None:
            return self._widget.__getattribute__(item)

    @staticmethod
    def hex_to_rgb(str_hex, alpha=1.0):
        to_list = [int(str_hex.replace('#', "").strip()[i:i + 2], 16) for i in (0, 2, 4)]
        return to_list[0] / 255, to_list[1] / 255, to_list[2] / 255, alpha

    def set_shadow(self, y_shift=1E-3):
        """
        Add a smooth shadow under the widget
        """
        self.get_bounds()
        x1, x2, y1, y2 = self._widget.getBounds()
        node = NodePath(self._widget.getName() + '_shadow')
        node.reparent_to(self._widget)
        scale = self._shadow_scale

        def place_shadow_im(name, x, y, sx=scale, sy=scale):
            loc_im = OnscreenImage(os.path.join(self.shadows_path, 'light{}.png'.format(name)),
                                   parent=node,
                                   scale=(sx, 1, sy))
            loc_im.set_pos((x, 0, y))
            loc_im.setTransparency(TransparencyAttrib.MAlpha)

        place_shadow_im('_dl', x1 + scale, y1 - scale + y_shift)
        place_shadow_im('_corner', x2 + scale, y1 - scale + y_shift)
        place_shadow_im('_d', 0.5 * (x1 + x2) + scale, y1 - scale + y_shift, 0.5 * (x2 - x1) - scale)
        place_shadow_im('_r', x2 + scale, 0.5 * (y1 + y2) - scale, scale, 0.5 * (y2 - y1) - scale)
        place_shadow_im('_ur', x2 + scale, y2 - scale)
        node.flatten_strong()

    def destroy(self):
        if self._widget is not None:
            self._widget.destroy()
