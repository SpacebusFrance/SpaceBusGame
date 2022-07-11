import datetime
import pandas as pd
import numpy as num
from math import sqrt

from direct.showbase.ShowBase import ShowBase, ClockObject
from panda3d.core import AntialiasAttrib, LVector3f

from engine.display.camera import FreeCameraControl
from engine.gui.gui import Gui
from engine.hardware.hardware_handler import HardwareHandler
from engine.scenario.scenario_handler import Scenario
from engine.shuttle.power_handler import PowerHandler
from engine.display.screens import FakeScreen3D
from engine.shuttle.shuttle_frame import ShuttleFrame
from engine.sound.sound_manager import SoundManager
from engine.meshes.asteroids import Asteroid
from engine.meshes.basis import CartesianBasis
from engine.meshes.flat_earth import Earth
from engine.meshes.flat_moon import Moon
from engine.meshes.flat_sun import Sun
from engine.meshes.grid import Grid
from engine.meshes.moon_base_spacecraft import NewSpaceCraft
from engine.meshes.sky_dome import SkyDome
from engine.utils.ini_parser import ParamUtils
from engine.utils.logger import Logger
from utils import smart_cast


# TODO : écran de fin
# TODO : fichier de sauvegarde
# TODO : désactiver touches rémanentes => voir les options de Ubuntu !
# TODO : puissance et oxygène à setter ailleurs que dans les jauges ?

class Game(ShowBase):
    def __init__(self, param_file, default_param_file):
        ShowBase.__init__(self)

        self.hard_states = dict()
        self.soft_states = dict()

        # self.params = Param()
        self.params = ParamUtils.read_ini_file(param_file)
        # add the path to the parameter file
        self.params['param_file'] = param_file

        # set default parameters
        self.default_params = ParamUtils.read_ini_file(default_param_file)
        self.default_params['param_file'] = param_file

        self.hardware_map = None
        self.load_config()

        # self.generate_files()

        self._admin_task = None
        self.clock = ClockObject()

        if self("test_3D"):
            self.earth = Earth(self)
            self.moon = Moon(self)
            self.sun = Sun(self)
            self.space_craft = NewSpaceCraft(self, quality=self("quality"))

            self.sound_manager = SoundManager(self)
            self.sound_manager.play_ambient_sound()

            cam = FreeCameraControl(self)
            cam.look_to_target()

            cb = CartesianBasis()
            self.render.attachNewNode(cb)
            grid = Grid(x_extend=[-10, 10], y_extend=[-10, 10], x_color=(1, 1, 1, 0.1), y_color=(1, 1, 1, 0.1))
            self.render.attach_new_node(grid)
            self.sky_sphere = SkyDome(self)
            self.sky_sphere.set_color_scale(LVector3f(0.4, 0.4, 0.4))

            self.render.setShaderAuto()
            self.setFrameRateMeter(True)
            self.render.setAntialias(AntialiasAttrib.MAuto)
            self.space_craft.show_bounds()

            self.space_craft.set_hpr(5, -122, 18)
            self.space_craft.set_solar_panel_angle(125.)

            # simple linking
            self.accept('a', self.space_craft.spin, extraArgs=['r', 1])
            self.accept('z', self.space_craft.spin, extraArgs=['r', -1])
            self.accept('e', self.space_craft.spin, extraArgs=['p', 1])
            self.accept('r', self.space_craft.spin, extraArgs=['p', -1])
            self.accept('t', self.space_craft.spin, extraArgs=['h', 1])
            self.accept('y', self.space_craft.spin, extraArgs=['h', -1])
            self.accept('q', self.space_craft.solar_panel_increment, extraArgs=[1])
            self.accept('s', self.space_craft.solar_panel_increment, extraArgs=[-1])
            self.accept('enter', self.sound_manager.play, extraArgs=['engine_fails'])
            self.accept('space', self.sound_manager.play, extraArgs=['engine_starts'])
        else:
            # hardware
            self.hardware = HardwareHandler(self)

            # power
            self.power = PowerHandler(self)
            self.power.compute_power()

            # scenario
            self.scenario = Scenario(self)

            # sound manager
            # todo : if we set sounds, this fails ... why ?
            self.sound_manager = SoundManager(self, load=False)

            # control screen
            self.gui = Gui(self) if self('use_new_gui') else ControlScreen(self)

            # environment
            self.earth = Earth(self)
            self.moon = Moon(self)
            self.sun = Sun(self)
            self.space_craft = NewSpaceCraft(self, quality=self("quality"))

            self.asteroid = Asteroid(self)

            # initial position and angle
            self.space_craft.set_hpr(5, -122, 18)
            self.space_craft.set_solar_panel_angle(125.)

            # shuttle frame
            self.shuttle = ShuttleFrame(self)

            self.screens = []

            if self("enable_free_camera"):
                self.screens.append(FakeScreen3D(self, 1, shuttle_angle=0))

                cam = FreeCameraControl(self, self.screens[0].get_camera())
                cam.look_to_target()

                self.shuttle.show_shuttle()
            else:
                # disable the standard mouse behavior
                self.disableMouse()

                # disabling the normal camera
                self.cam.node().set_active(0)

                # creating screens
                self.generate_spacebus_screens()

            # other options
            if self("show_basis"):
                cb = CartesianBasis()
                self.render.attachNewNode(cb)
            if self("show_grid"):
                grid = Grid(x_extend=[-10, 10], y_extend=[-10, 10], x_color=(1, 1, 1, 0.1), y_color=(1, 1, 1, 0.1))
                self.render.attach_new_node(grid)
            if self("show_ship_bounds"):
                self.space_craft.show_bounds()
            if self("show_sky_dome"):
                self.sky_sphere = SkyDome(self)
            else:
                self.setBackgroundColor(0, 0, 0)

            # automatic shader
            self.render.setShaderAuto()
            self.sky_sphere.set_luminosity(self("background_luminosity"))

            if self("show_frame_rate"):
                self.setFrameRateMeter(True)
            if self("anti_aliasing"):
                self.render.setAntialias(AntialiasAttrib.MAuto)
            # if self("play_scenario"):
            #     self.load_scenario(self('scenario'))

            self.reset_game()

    def __call__(self, key, default=False):
        """
        Get the option named `key`

        Args:
            key (str): the name of the option
            default (:obj:`bool`, optional): if set to ``True``, returns the *default* option value

        Returns:
            the value if founded, else `None`
        """
        if key in self.params:
            return self.params[key] if not default else self.default_params[key]
        else:
            Logger.error('option {} does not exists'.format(key))
            return None

    def set_option(self, name, value):
        """
        Update a value of options. This writes on the 'param_file' file

        Args:
            name (str): the name of the option to override
            value (object): its new value
        """
        if name not in self.params:
            Logger.error('option {} does not exists !'.format(name))
        else:
            old_value = self.params[name]
            self.params[name] = value
            # update file
            with open(self.params['param_file'], 'r') as f:
                content = f.read()
            with open(self.params['param_file'], 'w') as f:
                f.write(content.replace('{key}={value}'.format(key=name, value=old_value),
                                        '{key}={value}'.format(key=name, value=value)))

    def generate_spacebus_screens(self):
        """
        Generate screens for the game. Either with or without 3D screens
        """
        self.gui.set_single_window(self('show_3d_windows'))

        if self("show_3d_windows"):
            # and setting the other display regions
            self.screens.clear()
            self.screens.append(FakeScreen3D(self, 1, shuttle_angle=-90, shift_y=-4.0))
            self.screens.append(FakeScreen3D(self, 2, shuttle_angle=-self("front_screen_angle")))
            self.screens.append(FakeScreen3D(self, 3, shuttle_angle=self("front_screen_angle")))
            self.screens.append(FakeScreen3D(self, 4, shuttle_angle=90, shift_y=-4.0))

    def get_time(self, string_format=False, round_result=True):
        """
        Get the current game time

        Args:
            string_format (bool): specifies if it should be returned as a string
            round_result (bool): specifies if the result should be rounded at second level

        Returns:
            a :obj:`float` or a :obj:`str`
        """
        if string_format:
            return str(datetime.timedelta(seconds=round(self.clock.get_real_time(), 1)))
        else:
            return round(self.clock.get_real_time(), 1) if round_result else self.clock.get_real_time()

    def reset_game(self, scenario=None, start=False):
        """
        Resets the game in its original state

        Args:
            scenario (:obj:`str`, optional): if specified, loads the given scenario
            start (:obj:`bool`, optional): if :code:`True`, starts the scenario
        """
        self.clock.reset()
        self.sound_manager.reset()

        # self.hard_states = ParamUtils.read_ini_file(self("hardware_states_file"))
        # self.soft_states = ParamUtils.read_ini_file(self("software_states_file"))
        self.load_config()

        self.power.reset()
        self.hardware.all_leds_off()

        if scenario is not None:
            self.scenario.reset()
            self.scenario.load_scenario(scenario)

        self.shuttle.reset()
        self.gui.reset()

        if start:
            self.start_game()

    def quit(self):
        """
        Close current game
        """
        Logger.warning('quitting game')
        self.userExit()

    def start_game(self):
        """
        Starts the current scenario
        """
        self.sound_manager.play_ambient_sound()
        self.scenario.start_game()

    def get_soft_state(self, state_key):
        """
        Get the desired *soft state*

        Args:
            state_key (str): the name of the state

        Returns:
            a :obj:`bool` or a :obj:`float`
        """
        return self.soft_states.get(state_key, None)

    def get_hard_state(self, state_key):
        """
        Get the desired *hard state*

        Args:
            state_key (str): the name of the state

        Returns:
            a :obj:`bool` or a :obj:`float`
        """
        return self.hard_states.get(state_key, None)

    def load_config(self):
        """
        Load and reads the *main_hardware_file*
        """
        self.hardware_map = pd.read_csv(self('main_hardware_file'), sep=',') \
            .replace({'defines_a_state': {num.nan: False},
                      'power': {num.nan: 0.0}}) \
            .replace(num.nan, '')

        # build the initial state
        for c, l in self.hardware_map.iterrows():
            value = smart_cast(l['initial_value'])
            if l['id'].startswith(('j_', 'b_', 'l_', 's_')):
                self.hard_states[l['id']] = value
                if l['defines_a_state']:
                    self.soft_states[l['id'][2:]] = value
            elif l['type'] == 'SOFT':
                self.soft_states[l['id']] = value

    def update_soft_state(self, state_key, value, force_power=False, silent=False):
        """
        Update one state of the shuttle and tells the game that the shuttle is updated.

        Args:
            state_key (str): the name of the state
            value (:obj:`bool`, obj:`float`): the new value to set
            force_power (bool): specifies if the power should be taken into account or not
            silent (bool): specifies if any sound should be played
        """
        if state_key in self.soft_states:
            if (not self("use_power") or force_power or not value
                or (value and self("use_power") and self.power.can_be_switched_on(state_key))) \
                    and self.soft_states[state_key] != value:

                # first, there may be some conditions
                if state_key in ["correction_roulis", "correction_direction", "correction_stabilisation"] and value and not self.soft_states["pilote_automatique"]:
                    return True
                if state_key.startswith("batterie") and not state_key.endswith('s') and not self.soft_states["batteries"]:
                    self.sound_manager.play("batterie_wrong")
                    return True
                if state_key.startswith("moteur") and value and self.get_soft_state("collision_occurred"):
                    self.sound_manager.play("engine_fails")
                    return True

                # now we switch it on
                Logger.print("(soft state update) : {0} -> {1}".format(state_key, value), color='bold')
                old_value = self.soft_states[state_key]
                self.soft_states[state_key] = value

                # check if it is associated to one led
                self.hardware.check_constrained_led(state_key, value)

                # maybe it changes the energy and maybe it plays an automatic sound
                if not value:
                    if not silent:
                        self.sound_manager.play(state_key + "_off")
                    self.power.switch_off(state_key)
                else:
                    if not silent:
                        self.sound_manager.play(state_key + "_on")
                    self.power.switch_on(state_key)

                # check for gui:
                self.gui.event("update_state", key=state_key)

                # particular actions ?
                if state_key == "offset_ps_x" or state_key == "offset_ps_y":
                    self.update_soft_state("sp_power",
                                           round(self.get_soft_state("sp_max_power") / sqrt(
                                               1 + self.get_soft_state("offset_ps_x") ** 2 + self.get_soft_state(
                                                   "offset_ps_y") ** 2), 3))
                    if self.get_soft_state("offset_ps_x") == self.get_soft_state("offset_ps_y") == 0:
                        self.sound_manager.play("sp_nominal")
                        self.hardware.set_led_on("l_ps_nominal")
                    else:
                        self.hardware.set_led_off("l_ps_nominal")
                elif state_key == "sp_power":
                    power = self.get_soft_state("main_power")
                    self.update_soft_state("main_power", power + value - old_value)
                elif state_key == "pilote_automatique" and not value:
                    self.soft_states["full_pilote_automatique"] = False

                    # switch corrections off
                    for c in ["correction_roulis", "correction_direction", "correction_stabilisation"]:
                        self.update_soft_state(c, False)
                elif state_key in ["correction_roulis", "correction_direction", "correction_stabilisation"]:
                    on = True
                    for c in ["correction_roulis", "correction_direction", "correction_stabilisation"]:
                        if not self.get_soft_state(c):
                            on = False
                            break
                    self.soft_states["full_pilote_automatique"] = on
                elif state_key.startswith("moteur") and value:
                    self.sound_manager.play("engine_starts")

                elif state_key == "pilote_automatique_failed" and value:
                    # removing it in a few frames
                    self.taskMgr.doMethodLater(0.1, self.update_soft_state, name="paf_end",
                                               extraArgs=["pilote_automatique_failed", False])

                # and tell the game that there have been a update
                self.scenario.update_scenario()

                # this may append if the task is automatically fulfilled with f1.
                if state_key == "pilote_automatique_failed" and value:
                    self.soft_states["pilote_automatique_failed"] = False
                    Logger.print("(soft state update) : {0} -> {1}".format(state_key, False), color='bold')
            else:
                if state_key.startswith('moteur') and value:
                    self.sound_manager.play("engine_fails")
                elif value and not self.power.can_be_switched_on(state_key):
                    if state_key == "pilote_automatique":
                        # sets the failed to True and immediately after to False.
                        self.soft_states["pilote_automatique_failed"] = True
                        Logger.print("(soft state update) : {0} -> {1}".format(state_key, True), color='bold')
                        self.scenario.update_scenario()
                        self.soft_states["pilote_automatique_failed"] = False
                        Logger.print("(soft state update) : {0} -> {1}".format(state_key, False), color='bold')
            return True
        return False

    def update_hard_state(self, state_key, value, silent=False):
        """
        Update a hardware state of the shuttle and tells the game that the shuttle is updated.

        Args:
           state_key (str): the name of the state
           value (:obj:`bool`, obj:`float`): the new value to set
           silent (bool): specifies if any sound should be played
        """
        if state_key == "b_admin":
            self.hard_states[state_key] = value
            # always listen to it
            self.scenario.update_scenario()

        # only do it if the key exists and if we listen to hardware and if the value is different from the previous one
        # (to avoid spam of joysticks_axis = 0.0)
        elif state_key in self.hard_states and self.get_soft_state("listen_to_hardware") and value != self.hard_states[state_key]:
            Logger.print("(hard state update) : {0} -> {1}".format(state_key, value), color='bold')
            self.hard_states[state_key] = value

            # check if it is associated to one led
            self.hardware.check_constrained_led(state_key, value)

            # maybe it plays an automatic sound
            if not silent:
                if value:
                    self.sound_manager.play(state_key + "_on")
                else:
                    self.sound_manager.play(state_key + "_off")

            self.scenario.update_scenario()

            # particular cases:
            if state_key == "b_freq_moins" and value:
                self.update_soft_state("freq_comm", self.get_soft_state("freq_comm") - self("freq_comm_increment"), silent=silent)
            elif state_key == "b_freq_plus" and value:
                self.update_soft_state("freq_comm", self.get_soft_state("freq_comm") + self("freq_comm_increment"), silent=silent)
            elif state_key == "b_stop_shuttle" and value:
                self.shuttle.stop()
            elif state_key == "j_sp_orientation_h":
                if value > 0 and self.get_soft_state("offset_ps_x") < 10:
                    self.update_soft_state("offset_ps_x", self.get_soft_state("offset_ps_x") + 1, silent=silent)
                elif value < 0 and self.get_soft_state("offset_ps_x") > -10:
                    self.update_soft_state("offset_ps_x", self.get_soft_state("offset_ps_x") - 1, silent=silent)
            elif state_key == "j_sp_orientation_v":
                if value > 0 and self.get_soft_state("offset_ps_y") < 10:
                    self.update_soft_state("offset_ps_y", self.get_soft_state("offset_ps_y") + 1, silent=silent)
                elif value < 0 and self.get_soft_state("offset_ps_y") > -10:
                    self.update_soft_state("offset_ps_y", self.get_soft_state("offset_ps_y") - 1, silent=silent)
            elif state_key[:-1] == 's_pilote_automatique':
                other = 's_pilote_automatique1' if state_key[-1] == '2' else 's_pilote_automatique2'
                if value and self.get_hard_state(other):
                    self.update_soft_state("pilote_automatique", True, silent=silent)
                elif not value and not self.get_hard_state(other):
                    self.update_soft_state("pilote_automatique", False, silent=silent)

            # now check if it controls a software value
            self.update_soft_state(state_key.split('_', 1)[1], value)

            return True
        return False

    def reset_hardware(self):
        """
        Reset all hardware states into their default value
        """
        self.hard_states = ParamUtils.read_ini_file(self("hardware_states_file"))

    def init_states(self):
        """
        This function initializes the game states.
        """
        self.hard_states = ParamUtils.read_ini_file(self("hardware_states_file"))
        self.soft_states = ParamUtils.read_ini_file(self("software_states_file"))
