from direct.gui.DirectGuiGlobals import FLAT, WITHIN, WITHOUT, NORMAL
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from panda3d.core import LVector4f, MouseButton, PGButton, TextNode

from engine.gui.widgets.base_widget import BaseWidget


class ScrolledFrame(BaseWidget):
    """
    A custom frame that can be scrolled vertically only
    """
    def __init__(self, gui_engine,
                 size_x,
                 size_y,
                 **kwargs):
        super(ScrolledFrame, self).__init__(gui_engine, **kwargs)
        self._widget = DirectScrolledFrame(frameSize=LVector4f(0.0, size_x, 0.0, size_y),
                                           canvasSize=LVector4f(0.0, size_x - 0.05, 0.0, 0.0),
                                           frameColor=kwargs.get('color', LVector4f(0.0, 0.0, 0.0, 0.1)),
                                           scrollBarWidth=0.03,
                                           verticalScroll_relief=None,
                                           verticalScroll_frameColor=LVector4f(0.0, 0.0, 0.0, 0.2),
                                           verticalScroll_thumb_frameColor=LVector4f(0.5, 0.5, 0.5, 0.8),
                                           verticalScroll_thumb_relief=FLAT,
                                           verticalScroll_incButton_frameColor=LVector4f(1.0, 1.0, 1.0, 0.8),
                                           verticalScroll_incButton_relief=FLAT,
                                           verticalScroll_decButton_frameColor=LVector4f(1.0, 1.0, 1.0, 0.8),
                                           verticalScroll_decButton_relief=FLAT,
                                           horizontalScroll_frameColor=LVector4f(0.0, 0.0, 0.0, 0.2),
                                           horizontalScroll_thumb_frameColor=LVector4f(0.5, 0.5, 0.5, 0.8),
                                           horizontalScroll_thumb_relief=FLAT,
                                           horizontalScroll_incButton_frameColor=LVector4f(1.0, 1.0, 1.0, 0.8),
                                           horizontalScroll_incButton_relief=FLAT,
                                           horizontalScroll_decButton_frameColor=LVector4f(1.0, 1.0, 1.0, 0.8),
                                           horizontalScroll_decButton_relief=FLAT,
                                           state=NORMAL,
                                           **kwargs
                                           )
        self._widget.initialiseoptions(DirectScrolledFrame)

        self._size = (size_x, size_y)
        self._current_row = 0
        self._nb_items = 0

        self.bind(WITHIN, self._listen_scroll, [True])
        self.bind(WITHOUT, self._listen_scroll, [False])

        self._wheel_up_event = PGButton.getPressPrefix() + MouseButton.wheel_up().getName() + '-' + self.guiId
        self._wheel_down_event = PGButton.getPressPrefix() + MouseButton.wheel_down().getName() + '-' + self.guiId
        self.scroll_value = 10

    def _listen_scroll(self, allow, *args):
        """
        Allows the frame to listen to wheel events or not

        Args:
            allow (bool): if the listening should be on or not
        """
        if allow:
            self.accept(self._wheel_down_event,
                        self.vertical_scroll,
                        extraArgs=[self.scroll_value])
            self.accept(self._wheel_up_event,
                        self.vertical_scroll,
                        extraArgs=[-self.scroll_value])
        else:
            self.ignore(self._wheel_up_event)
            self.ignore(self._wheel_down_event)

    def vertical_scroll(self, v=0.0, *args):
        """
        Perform a vertical scroll if the page needs to

        Args:
            v (float): the value to scroll
        """
        if not self.verticalScroll.is_hidden():
            self.verticalScroll.scrollStep(v)

    def add_item(self, item, rescale=True):
        """
        Add an item to the frame and expand its height if necessary. All items are placed one next to another in
        vertical direction

        Args:
            item (NodePath): the node to add
            rescale (bool): if :code:`True`, the item is rescaled in order to fit widget's width.
        """
        # reparent it to the frame
        item.reparent_to(self.getCanvas())

        # child nodes also scroll !
        item.accept(self._wheel_up_event.replace(self.guiId, item.guiItem.getId()), self.vertical_scroll,
                    extraArgs=[-self.scroll_value])
        item.accept(self._wheel_down_event.replace(self.guiId, item.guiItem.getId()), self.vertical_scroll,
                    extraArgs=[self.scroll_value])

        # compute the scale if necessary
        scale = self._widget['canvasSize'][1] / (item.getWidth()) if rescale else item.get_scale().x
        item.set_scale(scale)
        # update canvas size
        # self._widget['canvasSize'][2] -= (item.getHeight() + 1) * scale
        self._widget['canvasSize'][2] -= (item.getHeight()) * scale
        # set the position of the item
        item.set_pos((0.0, 0, self._widget['canvasSize'][2]))

        self._widget.initialiseoptions(DirectScrolledFrame)

    def add_text(self, text, text_color='light', text_scale=0.07):
        """
        A shortcut to :func:`add_item` adding a text in the frame

        Args:
            text (str): the text to display
            text_color (:obj:`str`, :obj:`list-like`): the color of the text to display
            text_scale (float): the size of the text. Note that the text is automatically wrapped in order to fit
                widget's width.
        """
        self.add_item(DirectLabel(text=text,
                                  scale=text_scale,
                                  text_wordwrap=self._size[0] / text_scale * 0.9,
                                  text_align=TextNode.ALeft,
                                  text_bg=(1.0, 1.0, 1.0, 0.0),
                                  frameColor=(1.0, 1.0, 1.0, 0.0),
                                  text_fg=self.color(text_color)),
                      rescale=False)

    def reset_children(self):
        """
        Remove all widgets from the frame
        """
        for n in range(self.getCanvas().get_num_children()):
            self.getCanvas().get_child(n).remove_node()
        self._current_row = 0
        self._nb_items = 0
        self['canvasSize'][2] = 0
        self.initialiseoptions(ScrolledFrame)
