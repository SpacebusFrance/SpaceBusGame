from panda3d.core import CardMaker, LVector4f

from engine.gui.windows.window import Window


class GaugeWindow(Window):
    """
    A custom widget representing a gauge
    """
    def __init__(self,
                 gui_engine,
                 size_x=1.0,
                 size_y=0.8,
                 title=None,
                 text=None,
                 bar_number=15,
                 value=0.5,
                 gauge_color='br',
                 evolution_per_seconds=0.01,
                 **kwargs):
        super(GaugeWindow, self).__init__(gui_engine, size_x=size_x, size_y=size_y, title=title, text=text, **kwargs)

        self._bars = bar_number
        self._gauge_value = value
        self._gauge_color = gauge_color
        self._gauge = self._widget.attach_new_node('gauge')
        self._target_value = value
        self._evolution_per_seconds = evolution_per_seconds
        self._build_gauge()

    def _color(self, i):
        cols = {'r': self.color('red'),
                'g': self.color('green'),
                'b': self.color('blue')}
        x = (i + 1) / self._bars
        if len(self._gauge_color) == 2:
            res = LVector4f(cols[self._gauge_color[0]]) * (1 - x) + LVector4f(cols[self._gauge_color[1]]) * x
        else:
            res = LVector4f(cols[self._gauge_color[0]]) * (1 - x) ** 2 \
                  + LVector4f(cols[self._gauge_color[1]]) * 2 * x * (1 - x) \
                  + LVector4f(cols[self._gauge_color[2]]) * x ** 2.0
        if i > self._gauge_value * self._bars:
            res.w = 0.2
        else:
            res.w = 1.0
        return res

    def _build_gauge(self):
        widget_pad = 0.05
        alpha = 0.3
        # total_h = self._size[1] - widget_pad
        total_h = self._size[1]
        total_w = self._size[0] - 3.0 * widget_pad
        h = total_h / (self._bars * (alpha + 1) - alpha)
        bar_pad = alpha * h
        # h = (total_h - (self._gauge_range - 1) * bar_pad) / self._gauge_range
        for i in range(self._bars):
            cm = CardMaker('gauge_{}'.format(i))
            cm.set_frame(-0.5 * total_w, 0.5 * total_w,
                         - 0.5 * self._size[1] + 2.0 * widget_pad + i * h,
                         - 0.5 * self._size[1] + 2.0 * widget_pad + i * h + h - bar_pad)
            self._gauge.attachNewNode(cm.generate())
        self.set_value(self._gauge_value)

    def set_value(self, value, dynamic=True):
        """
        Set the gauge value

        Args:
            value (float): the value to set
            dynamic (bool): if the value should evolve slowly or not
        """
        self._target_value = max(0.0, min(value, 1.0))
        if dynamic:
            self._gauge_value = self._target_value
        else:
            self._widget.remove_all_tasks()
            self._widget.add_task(self._evolution, name='gauge_evolution')
        self._update()

    def _update(self):
        for i in range(self._bars):
            self._gauge.get_child(i).set_color(self._color(i))

    def _evolution(self, task):
        if self._gauge_value == self._target_value:
            return task.done
        else:
            dv = min(self._evolution_per_seconds * self._gui_engine.engine.clock.get_dt(),
                     abs(self._target_value - self._gauge_value))
            if self._gauge_value > self._target_value:
                self._gauge_value -= dv
            else:
                self._gauge_value += dv
            self._update()
            return task.cont
