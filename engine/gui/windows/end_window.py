import datetime
import re
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.interval.LerpInterval import LerpColorScaleInterval
from panda3d.core import TextNode, LVector3f
from engine.gui.windows.window import Window


class EndWindow(Window):
    """
    End window with player score
    """
    def __init__(self,
                 gui_engine,
                 player_position=None,
                 time_minutes=None,
                 time_seconds=None,
                 total_players=None,
                 size_x=1.7,
                 size_y=1.8,
                 text='$score_text$',
                 header='$score_header$',
                 **kwargs):

        super(EndWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title='', text=None, icon=None,
                                        color='black',
                                        **kwargs)

        self._text_scale = 0.1

        header = self._gui_engine.process_text(header)\
            .replace('MINUTES', str(time_minutes))\
            .replace('SECONDS', str(time_seconds))\
            .replace('POSITION', str(player_position))\
            .replace('TOTAL', str(total_players))

        OnscreenImage(image=self._gui_engine.engine('icon_path') + 'logo_sb.png',
                      pos=(1.25, 0, 0.75),
                      scale=(0.5, 1.0, 0.2),
                      color=self.color('golden'),
                      parent=self._widget)

        def appear(node, time):
            return LerpColorScaleInterval(node, time, colorScale=(1, 1, 1, 1), startColorScale=(1, 1, 1, 0))

        self._header = OnscreenText(text=header,
                                    fg=self.color('light'),
                                    wordwrap=size_x / self._text_scale * 0.9,
                                    align=TextNode.ACenter,
                                    pos=(0.0, 0.5 * size_y - self._widget_pad - self._text_scale),
                                    scale=self._text_scale,
                                    parent=self._widget
                                    )

        bl, tr = self._header.get_tight_bounds()
        self._header_size = tr.z - bl.z

        self._frame = DirectScrolledFrame(canvasSize=(- 0.5 * size_x + self._widget_pad,
                                                      0.5 * size_x - self._widget_pad,
                                                      - 1.0,
                                                      0.5 * size_y - 2 * self._widget_pad - self._header_size),
                                          frameSize=(- 0.5 * size_x + self._widget_pad,
                                                     0.5 * size_x - self._widget_pad,
                                                     - 1.0,
                                                     0.5 * size_y - 2 * self._widget_pad - self._header_size,
                                                     ),
                                          color=self.color('black'),
                                          autoHideScrollBars=True,
                                          scrollBarWidth=0.0,
                                          parent=self._widget
                                          )

        self._text = OnscreenText(text=self._gui_engine.process_text(text),
                                  fg=self.color('light'),
                                  wordwrap=size_x / self._text_scale * 0.9,
                                  align=TextNode.ACenter,
                                  pos=(0.0, - 1.0 - self._text_scale),
                                  scale=self._text_scale,
                                  parent=self._frame.getCanvas()
                                  )

        # fade-in time
        self._widget.set_color_scale((1, 1, 1, 0))
        appear(self._background, 5.0).start()
        self._gui_engine.do_method_later(5.0, lambda task: appear(self._widget, 5.0).start(), 'show_screen')
        self._gui_engine.do_method_later(10.0, self._scroll, 'end_screen_scrolling')

    def _scroll(self, _=None):
        bl, tr = self._text.get_tight_bounds()
        self._text.posInterval(35.0, LVector3f(0, 0, 1.0 + 1.2 * abs(tr.z - bl.z))).start()
