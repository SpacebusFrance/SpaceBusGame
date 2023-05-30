from panda3d.core import CardMaker

from engine.gui.windows.window import Window


class VideoWindow(Window):
    """
    A custom widget playing a video
    """
    def __init__(self,
                 gui_engine,
                 video_path,
                 size_x=1.0,
                 size_y=0.8,
                 start=True,
                 title=None,
                 text=None,
                 file_format='avi',                                     
                 **kwargs):
        super(VideoWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title=title, text=text, **kwargs)

        widget_pad = 0.05
        text_scale = 0.2

        self._movie = self._gui_engine.engine.loader.loadTexture("data/movie/{}.{fmt}".format(video_path,
                                                                                              fmt=file_format))

        cm = CardMaker('video')
        ar = self._movie.get_video_height() / self._movie.get_video_width()
        cm.set_frame(-0.5 * size_x + widget_pad,
                     0.5 * size_x - widget_pad,
                     -0.5 * size_y + widget_pad,
                     ar * (size_x - 2.0 * widget_pad) - 0.5 * size_y + widget_pad)
        cm.setUvRange(self._movie)
        node = self._widget.attachNewNode(cm.generate())
        node.setTexture(self._movie)

        self._sound = self._gui_engine.engine.loader.loadSfx("data/movie/{}.{fmt}".format(video_path,
                                                                                          fmt=file_format))
        self._movie.synchronizeTo(self._sound)
        # node.set_pos(0, 1, 0)
        if start:
            self._sound.play()

    def __getattr__(self, item):
        try:
            if self._widget is not None:
                return self._widget.__getattribute__(item)
        except AttributeError:
            return self._sound.__getattribute__(item)
