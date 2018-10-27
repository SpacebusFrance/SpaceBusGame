from Engine.ControlScreens.Gauge import Gauge
from Engine.ControlScreens.Screen import Screen


class MainScreen(Screen):
    """
    The main default screen with shuttle informations, gauges etc.
    """
    def __init__(self, mainScreen):
        Screen.__init__(self, mainScreen, "screen")
        self.name = "unlocked_screen"

        self.gauges = dict()
        self.gauges["main_O2"] = Gauge(self.main_screen, name="main_O2", x=775, low_value=70)
        self.gauges["main_CO2"] = Gauge(self.main_screen, name="main_CO2", x=844, low_value=30, high_value=70)
        self.gauges["main_power"] = Gauge(self.main_screen, name="main_power", x=912, low_value=0, min=-100, max=100)
        self.gauges["main_power"].half_sec_step_for_goto = 2.0

        for counter, g in enumerate(self.gauges):
            self.gauges[g].show()

        self.lock_text.hide()

        # list of software variables that appear in the defautl screen, in the state list
        self.global_variables = ['batterie1',
                                 'batterie2',
                                 'batterie3',
                                 'batterie4',
                                 'offset_ps_x',
                                 'offset_ps_y',
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
                                 'target_name'
                                 ]
        for i, gb in enumerate(self.global_variables):
            self.add_on_screen_text(269, 109 + i * 24, size=0, text="", name=gb, may_change=True)

        # to be modified
        self.add_on_screen_text(427, 100, size=2, text="", name="freq_comm", may_change=True)
        self.add_on_screen_text(417, 243, size=3, text="ON", color='green', name="pilote_automatique", may_change=True)
        self.add_on_screen_text(440, 542, size=2, text="", name="sp_power", may_change=True)
        self.add_on_screen_text(518, 383, size=0, text="actif", name="moteur1", may_change=True, color="green")
        self.add_on_screen_text(518, 410, size=0, text="actif", name="moteur2", may_change=True, color="green")
        self.add_on_screen_text(518, 437, size=0, text="actif", name="moteur3", may_change=True, color="green")

        self.add_on_screen_text(617, 229, size=0, text="on", name="correction_roulis", may_change=True, color="green")
        self.add_on_screen_text(617, 249, size=0, text="on", name="correction_direction", may_change=True,
                                color="green")
        self.add_on_screen_text(617, 269, size=0, text="on", name="correction_stabilisation", may_change=True,
                                color="green")

        self.set_all_elements()

    def set_all_elements(self):
        for name in self.on_screen_texts:
            value = self.main_screen.gameEngine.get_soft_state(name)
            # particular cases
            if name == "pilote_automatique":
                if value:
                    self.set_on_screen_text(name, "ON", False, "green")
                else:
                    self.set_on_screen_text(name, "OFF", False, "red")
            elif name in ['moteur1', 'moteur2', 'moteur3']:
                if value:
                    self.set_on_screen_text(name, "actif", False, "green")
                else:
                    self.set_on_screen_text(name, "inactif", False, "red")
            elif name == 'freq_comm':
                self.set_on_screen_text("freq_comm", str(value) + " MHz", True)
            else:
                if isinstance(value, bool):
                    if value:
                        self.set_on_screen_text(name, "on", False, "green")
                    else:
                        self.set_on_screen_text(name, "off", False, "red")
                else:
                    self.set_on_screen_text(name, str(value), False)

        for g in self.gauges:
            self.gauges[g].goto_value(self.main_screen.gameEngine.get_soft_state(g))
        self._update()

    def destroy(self):
        for g in self.gauges:
            self.gauges[g].destroy()
        Screen.destroy(self)

    def set_element(self, name):
        # should be in software_values

        value = self.main_screen.gameEngine.get_soft_state(name)
        if value is not None and name in self.on_screen_texts:
            # particular cases
            if name == "pilote_automatique":
                if value:
                    self.set_on_screen_text(name, "ON", True, "green")
                else:
                    self.set_on_screen_text(name, "OFF", True, "red")
            elif name in ['moteur1', 'moteur2', 'moteur3']:
                if value:
                    self.set_on_screen_text(name, "actif", True, "green")
                else:
                    self.set_on_screen_text(name, "inactif", True, "red")
            elif name == 'freq_comm':
                self.set_on_screen_text("freq_comm", str(value) + " MHz", True)
            else:
                if isinstance(value, bool):
                    if value:
                        self.set_on_screen_text(name, "on", True, "green")
                    else:
                        self.set_on_screen_text(name, "off", True, "red")
                else:
                    self.set_on_screen_text(name, str(value), True)
        elif name in self.gauges:
            self.gauges[name].goto_value(value)
