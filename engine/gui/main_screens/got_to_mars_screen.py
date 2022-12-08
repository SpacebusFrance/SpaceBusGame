from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from engine.gui.main_screens.main_screen import MainScreen
from engine.gui.windows.chrono_window import ChronoWindow
from engine.gui.windows.gauge_window import GaugeWindow
from engine.gui.windows.window import Window
from engine.utils.event_handler import event


class GoToMarsScreen(MainScreen):
    """
    Main screen for Mars Scenario (default game)
    """
    def __init__(self, gui_engine, *args, **kwargs):
        super(GoToMarsScreen, self).__init__(gui_engine, *args, **kwargs)

        self._left_panel = ['batterie1',
                            'batterie2',
                            'batterie3',
                            'batterie4',
                            'recyclage_O2',
                            'recyclage_CO2',
                            'recyclage_H2O',
                            'tension_secteur1',
                            'oxygene_secteur1',
                            'thermique_secteur1',
                            'tension_secteur2',
                            'oxygene_secteur2',
                            'thermique_secteur2',
                            'tension_secteur3',
                            'oxygene_secteur3',
                            'thermique_secteur3',
                            ]

        self._engine_panel = ['moteur1', 'moteur2', 'moteur3']
        self._solar_panel = ['offset_ps_x', 'offset_ps_y', 'sp_power']

    @event('start_chrono')
    def on_start_chrono(self, time=None):
        if time is not None:
            self._chrono.set_time(time)
        self._chrono.start()

    @event('stop-chrono')
    def on_stop_chrono(self):
        self._chrono.stop()

    @event('reset-chrono')
    def on_reset_chrono(self, time=None):
        self._chrono.reset(time=time)
    #
    #
    # def notify_event(self, event, **kwargs):
    #     """
    #     Notify an event
    #     """
    #     event = event.lower().strip()
    #
    #     if event == 'start-chrono':
    #         if 'time' in kwargs:
    #             self._chrono.set_time(kwargs['time'])
    #         self._chrono.start()
    #     elif event == 'stop-chrono':
    #         self._chrono.stop()
    #     elif event == 'reset-chrono':
    #         self._chrono.reset(time=kwargs.get('time', None))

    def make(self):
        """
        Build the screen
        """
        self._build_com_panel()
        self._build_engine_panel()
        self._build_gauge()
        self._build_shuttle_frame()
        self._build_solar_panel()
        self._build_chrono()

    def _build_shuttle_frame(self, size_x=0.9, size_y=1.8):
        w = Window(self.gui,
                   title=self.gui.process_text('$shuttle_title$'),
                   text='',
                   size_y=size_y,
                   size_x=size_x,
                   icon_size=self._icon_size,
                   icon=None,
                   pos=(-1.2, 0.0))

        for i, e in enumerate(self._left_panel):
            # text, should not move
            OnscreenText(text=self._format(e),
                         align=TextNode.ALeft,
                         pos=(-0.5 * size_x + self._large_pad,
                              - 0.5 * size_y + self._large_pad + i * (self._text_scale + self._small_pad)),
                         scale=self._text_scale,
                         parent=w.get_node())
            # values
            self._texts[e] = OnscreenText(text=self._format(e, True),
                                          align=TextNode.ARight,
                                          pos=(0.5 * size_x - self._large_pad,
                                               - 0.5 * size_y + self._large_pad + i * (
                                                       self._text_scale + self._small_pad)),
                                          scale=self._text_scale,
                                          parent=w.get_node())

    def _build_com_panel(self, size_y=0.5, size_x=0.8, pos_x=-0.2):
        # BUILD COM PANEL
        com = Window(self.gui,
                     title=self.gui.process_text('$com_title$'),
                     text=self.gui.process_text('$com_text$'),
                     size_y=size_y,
                     size_x=size_x,
                     icon_size=self._icon_size,
                     icon=None,
                     pos=(pos_x, 0.65))
        self._texts['freq_comm'] = OnscreenText(
            text=f'\1title\1{self._format("freq_comm", True)}\2  \1light\1[MHZ]\2',
            align=TextNode.ACenter,
            pos=(0.0, - 0.5 * size_y + self._large_pad),
            scale=self._text_scale,
            parent=com.get_node())

    def _build_engine_panel(self, size_x=0.8, size_y=0.5, pos_x=-0.2):
        # ENGINE USE
        engine = Window(self.gui,
                        title=self.gui.process_text('$engine_title$'),
                        size_y=size_y,
                        size_x=size_x,
                        icon_size=self._icon_size,
                        icon=None,
                        pos=(pos_x, 0.05))
        for i, e in enumerate(self._engine_panel):
            # text, should not move
            OnscreenText(text=self._format(e),
                         align=TextNode.ALeft,
                         pos=(-0.5 * size_x + self._large_pad,
                              - 0.5 * size_y + self._large_pad + i * (self._text_scale + self._small_pad)),
                         scale=self._text_scale,
                         parent=engine.get_node())
            # values
            self._texts[e] = OnscreenText(text=self._format(e, True),
                                          align=TextNode.ARight,
                                          pos=(0.5 * size_x - self._large_pad,
                                               - 0.5 * size_y + self._large_pad + i * (
                                                       self._text_scale + self._small_pad)),
                                          scale=self._text_scale,
                                          parent=engine.get_node())

    def _build_solar_panel(self, size_y=0.5, size_x=0.8, pos_x=-0.2):
        # Solar Panels
        solar = Window(self.gui,
                       title=self._format('solar_title'),
                       size_y=size_y,
                       size_x=size_x,
                       icon_size=self._icon_size,
                       icon=None,
                       pos=(pos_x, -0.54))
        for i, e in enumerate(self._solar_panel):
            # text, should not move
            OnscreenText(text=self._format(e),
                         align=TextNode.ALeft,
                         pos=(-0.5 * size_x + self._large_pad,
                              - 0.5 * size_y + self._large_pad + i * (self._text_scale + self._small_pad)),
                         scale=self._text_scale,
                         parent=solar.get_node())
            # values
            self._texts[e] = OnscreenText(text=self._format(e, True),
                                          align=TextNode.ARight,
                                          pos=(0.5 * size_x - self._large_pad,
                                               - 0.5 * size_y + self._large_pad + i * (
                                                           self._text_scale + self._small_pad)),
                                          scale=self._text_scale,
                                          parent=solar.get_node())

    def _build_gauge(self, size_x=.45, size_y=1.2, bar_number=20):
        # BUILD GAUGES
        colors = {'main_CO2': 'rgr', 'main_O2': 'rbg', 'main_power': 'rg'}
        for i, value in enumerate(['main_CO2', 'main_O2', 'main_power']):
            self._texts[value] = GaugeWindow(self.gui,
                                             size_x=size_x,
                                             size_y=size_y,
                                             gauge_color=colors[value],
                                             bar_number=bar_number,
                                             value=self._get_value(value) / 100,
                                             title=self._format(value),
                                             )
            self._texts[value].set_pos(0.6 + i * size_x * 0.9, 0.0, 0.3)

    def _build_chrono(self, size_x=1.25, size_y=0.5):
        self._chrono = ChronoWindow(self.gui,
                                    title=self.gui.process_text('$chrono_title$'),
                                    text=self.gui.process_text(''),
                                    size_y=size_y,
                                    size_x=size_x,
                                    icon_size=self._icon_size,
                                    pos=(1., -0.65)
                                    )
