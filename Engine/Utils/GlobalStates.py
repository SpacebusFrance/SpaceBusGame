from math import sqrt
from Engine.Utils.utils import read_ini_file


class PowerHandler:
    def __init__(self, gameEngine):
        self.game_engine = gameEngine
        self.power_consuming_actions = dict()

    def reset(self):
        self.power_consuming_actions = read_ini_file(self.game_engine.params("power_balance_file"))
        self.compute_power()

    def compute_power(self):
        power = 0
        for e in self.power_consuming_actions:
            if self.game_engine.get_soft_state(e):
                power += self.power_consuming_actions[e]

        self.game_engine.soft_states["sp_power"] = round(self.game_engine.get_soft_state("sp_max_power") / sqrt(
            1 + self.game_engine.get_soft_state("offset_ps_x") ** 2 + self.game_engine.get_soft_state(
                "offset_ps_y") ** 2), 3)

        self.game_engine.soft_states["main_power"] = self.game_engine.soft_states["sp_power"] + power

    def switch_off(self, key):
        if key in self.power_consuming_actions:
            power = self.game_engine.get_soft_state("main_power")
            self.game_engine.update_soft_state("main_power", power - self.power_consuming_actions[key])

    def switch_on(self, key, check=False):
        if key in self.power_consuming_actions:
            if check and self.can_be_switched_on(key) or not check:
                power = self.game_engine.get_soft_state("main_power")
                self.game_engine.update_soft_state("main_power", power + self.power_consuming_actions[key])

    def can_be_switched_on(self, action):
        power = self.game_engine.get_soft_state("main_power")
        if action in self.power_consuming_actions and self.power_consuming_actions[action] < 0:
            return power + self.power_consuming_actions[action] >= 0
        else:

            return True
