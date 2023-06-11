import datetime
from math import sqrt
from typing import Any

from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import WindowProperties
from direct.showbase.ShowBase import ShowBase, ClockObject
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AntialiasAttrib, LVector3f

from engine.display.camera import FreeCameraControl
from engine.display.screens import FakeScreen3D
from engine.game_state import GameStateManager, GameState
from engine.gui.gui import Gui
from engine.hardware.hardware_handler import HardwareHandler
from engine.meshes.asteroids import Asteroid
from engine.meshes.basis import CartesianBasis
from engine.meshes.flat_earth import Earth
from engine.meshes.flat_moon import Moon
from engine.meshes.flat_sun import Sun
from engine.meshes.grid import Grid
from engine.meshes.moon_base_spacecraft import NewSpaceCraft
from engine.meshes.sky_dome import SkyDome
from engine.scenario.scenario_handler import Scenario
from engine.shuttle.shuttle_frame import ShuttleFrame
from engine.sound.sound_manager import SoundManager
from engine.utils.ini_parser import ParamUtils
from engine.utils.logger import Logger


class Game(ShowBase):
    def __init__(self, param_file, default_param_file):
        ShowBase.__init__(self)

        # splashscreen
        props = WindowProperties()
        props.set_undecorated(True)
        props.set_size(800, 600)
        self.win.request_properties(props)
        self.splashscreen = OnscreenImage(image='data/gui/images/splashscreen.png', parent=self.render2d)
        # render three (?) frames to actually see it
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()

        # loading start
        self.params = ParamUtils.read_ini_file(param_file)
        # add the path to the parameter file
        self.params['param_file'] = param_file

        # set default parameters
        self.default_params = ParamUtils.read_ini_file(default_param_file)
        self.default_params['param_file'] = param_file

        # store clock object
        self.clock = globalClock

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
            self.accept('enter', self.sound_manager.play_sfx, extraArgs=['engine_fails'])
            self.accept('space', self.sound_manager.play_sfx, extraArgs=['engine_starts'])
        else:
            # hardware
            self.hardware = HardwareHandler(self)

            # state manager
            GameState.engine = self
            self.state_manager = GameStateManager()

            # scenario
            self.scenario = Scenario(self)

            # sound manager
            self.sound_manager = SoundManager(self, load=self('play_sound'))

            # control screen
            self.gui = Gui(self)

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
            if self('max_fps') is not None:
                globalClock.setMode(ClockObject.MLimited)
                globalClock.setFrameRate(self('max_fps'))
            # self.setFrameRateMeter(True)
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
            Logger.error(f'option {key} does not exists')
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
        self.splashscreen.remove_node()
        self.gui.set_single_window(self('show_3d_windows'), screen_number=self('screen_number'))

        if self("show_3d_windows"):
            # and setting the other display regions
            self.screens.clear()
            screen_number = self('screen_number')
            if screen_number >= 2:
                self.screens.append(FakeScreen3D(self, 1, shuttle_angle=-90, shift_y=-4.0))
            if screen_number >= 3:
                self.screens.append(FakeScreen3D(self, 2, shuttle_angle=-self("front_screen_angle")))
            if screen_number >= 4:
                self.screens.append(FakeScreen3D(self, 3, shuttle_angle=self("front_screen_angle")))
            if screen_number >= 5:
                self.screens.append(FakeScreen3D(self, 4, shuttle_angle=90, shift_y=-4.0))

            # correct gui position
            self.aspect2d.set_pos(1/screen_number - 1, 0, 0)

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
        # remove admin key trigger
        self.ignore(self('admin_key'))
        # ignore step fulfill
        self.ignore(self('force_step_key'))

        self.clock.reset()
        self.sound_manager.reset()
        self.hardware.all_leds_off()
        self.hardware.disable_inputs()

        # reset hardware (reset leds)
        self.state_manager.reset()

        # reset scenario
        self.scenario.reset()
        if isinstance(scenario, str):
            # load a new scenario
            self.scenario.load_scenario(scenario)

        # reset shuttle
        self.shuttle.reset()
        # reset ui
        self.gui.reset(show_menu=not start)

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
        # always listen to admin key
        self.accept(self('admin_key'), self.gui.admin_screen)
        self.accept(self('force_step_key'), self.scenario.fulfill_current_step)

        self.gui.hide_cursor()
        self.sound_manager.stop_music()
        self.sound_manager.play_ambient_sound()
        self.scenario.start_game()

    # new state management

    def can_set_state(self, state_name: str, value: Any) -> bool:
        # cannot set one of these values if "pilote_automatique" is on
        if state_name in ["correction_roulis", "correction_direction", "correction_stabilisation"] \
                and value \
                and not self.state_manager.pilote_automatique.is_on():
            return False

        # cannot set any battery if global batteries is off
        if state_name.startswith("batterie") \
                and state_name != "batteries" \
                and not self.state_manager.batteries.is_on():
            # plays a sound with wrong batteries
            self.sound_manager.play_sfx("batterie_wrong")
            return False

        # cannot set any moteur (engine) if collision occurred in first scenario
        if state_name.startswith("moteur") \
                and value \
                and self.state_manager.collision_occurred.is_on():
            # engine failing sound
            self.sound_manager.play_sfx("engine_fails")
            return False

        return True

    def check_hardware_state_update(self, state_name: str, value: Any, **kwargs) -> None:
        """
        Update the game states accordingly to some hardware inputs
        such as joystick and switches.

        Args:
            state_name (str): GameState name
            value (any): GameState value
        """
        if state_name == "sp_orientation_h" and value != 0:
            # joystick control solar panel (sp) horizontal orientation
            # update the value of solar panel offset x
            new_value = self.state_manager.offset_ps_x.get_value() - value
            self.state_manager.offset_ps_x.set_value(
                min(10, max(-10, new_value)),
                **kwargs
            )
        elif state_name == "sp_orientation_v" and value != 0:
            # joystick control solar panel (sp) vertical orientation
            # update the value of solar panel offset y
            new_value = self.state_manager.offset_ps_y.get_value() + value
            self.state_manager.offset_ps_y.set_value(
                min(10, max(-10, new_value)),
                **kwargs
            )
        elif state_name == "freq_moins" and value:
            # button controlling communication frequency
            # decrease the state "freq_comm"
            self.state_manager.freq_comm.set_value(
                self.state_manager.freq_comm.get_value() - self('freq_comm_increment'),
                **kwargs
            )
        elif state_name == "freq_plus" and value:
            # button controlling communication frequency
            # increase the state "freq_comm"
            self.state_manager.freq_comm.set_value(
                self.state_manager.freq_comm.get_value() + self('freq_comm_increment'),
                **kwargs
            )
        elif state_name[:-1] == 'pilote_automatique':
            # global state "pilote_automatique" is set if both
            # "pilote_automatique1" and "pilote_automatique2" are set
            # otherwise, unset it
            other = 'pilote_automatique1' if state_name[-1] == '2' else 'pilote_automatique2'
            if value and self.state_manager.get_state(other).is_on():
                self.state_manager.pilote_automatique.set_value(True, **kwargs)
            elif not value and not self.state_manager.get_state(other).is_on():
                self.state_manager.pilote_automatique.set_value(False, **kwargs)

        elif state_name in ['offset_ps_x', 'offset_ps_y']:
            # Check if solar panels are nominal, i.e. if game states ``offset_ps_x`` and
            # ``offset_ps_y`` are both set to 0. In that case, plays a sound and lights a LED
            is_nominal = self.state_manager.offset_ps_x.get_value() == self.state_manager.offset_ps_y.get_value() == 0
            if is_nominal:
                self.sound_manager.play_sfx("sp_nominal")
                self.state_manager.ps_nominal.set_led_on()
            else:
                self.state_manager.ps_nominal.set_led_off()

    def update_power(self) -> None:
        """
        Compute shuttle global power from all GameState, depending if there are
        on or off and the amount of power they produce/consume.

        Update the game states ``sp_power`` and ``main_power``
        """
        power = 0
        for item in self.state_manager.states().values():
            if item.is_on():
                power += item.power

        self.state_manager.sp_power.set_value(
            round(
                self.state_manager.sp_max_power.get_value() /
                sqrt(1 + self.state_manager.offset_ps_x.get_value() ** 2
                     + self.state_manager.offset_ps_y.get_value() ** 2),
                3),
            update_power=False
        )
        self.state_manager.main_power.set_value(
            self.state_manager.sp_power.get_value() + power,
            update_power=False
        )
