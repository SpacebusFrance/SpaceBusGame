from math import sqrt


class PowerHandler(object):
    def __init__(self, engine):
        self._engine = engine
        self.power_consuming_actions = dict()

    def reset(self):
        # self.power_consuming_actions = read_ini_file(self._engine("power_balance_file"))

        # build the initial state
        for c, l in self._engine.hardware_map.iterrows():
            value = l['power']
            if value != 0.0:
                self.power_consuming_actions[l['id']] = value
        self.compute_power()

    def compute_power(self):
        power = 0
        for e in self.power_consuming_actions:
            if self._engine.get_soft_state(e):
                power += self.power_consuming_actions[e]

        self._engine.soft_states["sp_power"] = round(self._engine.get_soft_state("sp_max_power")
                                                     / sqrt(1 + self._engine.get_soft_state("offset_ps_x") ** 2
                                                            + self._engine.get_soft_state("offset_ps_y") ** 2), 3)

        self._engine.soft_states["main_power"] = self._engine.soft_states["sp_power"] + power

    def switch_off(self, key):
        if key in self.power_consuming_actions:
            power = self._engine.get_soft_state("main_power")
            self._engine.update_soft_state("main_power", power - self.power_consuming_actions[key])

    def switch_on(self, key, check=False):
        if key in self.power_consuming_actions:
            if check and self.can_be_switched_on(key) or not check:
                power = self._engine.get_soft_state("main_power")
                self._engine.update_soft_state("main_power", power + self.power_consuming_actions[key])

    def can_be_switched_on(self, action):
        power = self._engine.get_soft_state("main_power")
        if action in self.power_consuming_actions and self.power_consuming_actions[action] < 0:
            return power + self.power_consuming_actions[action] >= 0
        else:
            return True
