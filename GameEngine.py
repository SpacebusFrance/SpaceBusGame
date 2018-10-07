import datetime
from math import sqrt

from direct.showbase.ShowBase import ShowBase, ClockObject
from panda3d.core import AntialiasAttrib, LVector3f

from Camera import FreeCameraControl
from ControlScreen import ControlScreen
from EventHandler import EventHandler
from GlobalStates import PowerHandler
from Hardware import HardwareHandler
from Meshes import CartesianBasis, Earth, Moon, Sun, SkyDome, NewSpaceCraft, Grid, Asteroid
from Parameters import Param
from Screens import Screen3D, FakeScreen3D
from Shuttle import ShuttleFrame
from Sounds import SoundManager
from utils import read_ini_file, smart_cast


class Game(ShowBase):
    """
    The main class of the game. Reads configuration from the params.ini file.
    """
    def __init__(self):
        ShowBase.__init__(self)

        self.params = Param()
        self.generate_files()

        self._admin_task = None
        self.clock = ClockObject()

        if self.params("test_3D"):
            self.earth = Earth(self)
            self.moon = Moon(self)
            self.sun = Sun(self)
            self.space_craft = NewSpaceCraft(self, quality=self.params("quality"))

            self.sound_manager = SoundManager(self)
            self.sound_manager.play_ambiant_sound()

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
            self.hard_states = dict()
            self.soft_states = dict()
            self.init_states()

            # hardware
            self.hardware = HardwareHandler(self)

            # power
            self.power = PowerHandler(self)
            self.power.compute_power()

            # scenario
            self.scenario = EventHandler(self)

            # sound manager
            self.sound_manager = SoundManager(self)

            # control screen
            self.control_screen = ControlScreen(self)

            # environment
            self.earth = Earth(self)
            self.moon = Moon(self)
            self.sun = Sun(self)
            self.space_craft = NewSpaceCraft(self, quality=self.params("quality"))

            self.asteroid = Asteroid(self)

            # initial position and angle
            self.space_craft.set_hpr(5, -122, 18)
            self.space_craft.set_solar_panel_angle(125.)

            # shuttle frame
            self.shuttle = ShuttleFrame(self)

            self.screens = []

            if self.params("enable_free_camera"):
                self.screens.append(Screen3D(self, 1, shuttle_angle=0))

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
            if self.params("show_basis"):
                cb = CartesianBasis()
                self.render.attachNewNode(cb)
            if self.params("show_grid"):
                grid = Grid(x_extend=[-10, 10], y_extend=[-10, 10], x_color=(1, 1, 1, 0.1), y_color=(1, 1, 1, 0.1))
                self.render.attach_new_node(grid)
            if self.params("show_ship_bounds"):
                self.space_craft.show_bounds()
            if self.params("show_sky_dome"):
                self.sky_sphere = SkyDome(self)
            else:
                self.setBackgroundColor(0, 0, 0)

            # automatic shader
            self.render.setShaderAuto()
            self.sky_sphere.set_luminosity(self.params("background_luminosity"))

            if self.params("show_frame_rate"):
                self.setFrameRateMeter(True)
            if self.params("anti_aliasing"):
                self.render.setAntialias(AntialiasAttrib.MAuto)
            if self.params("play_scenario"):
                self.load_scenario(self.params('scenario'))

            self.reset_game()

    def generate_spacebus_screens(self):
        """
        Creates the screen(s)
        """
        if self.params("one_single_window"):
            # setting set size of the main window
            self.control_screen.set_single_window()

            if self.params("show_3d_windows"):
                # and setting the other display regions
                self.screens.clear()
                self.screens.append(FakeScreen3D(self, 1, shuttle_angle=-90, shift_y=-4.0))
                self.screens.append(FakeScreen3D(self, 2, shuttle_angle=-self.params("front_screen_angle")))
                self.screens.append(FakeScreen3D(self, 3, shuttle_angle=self.params("front_screen_angle")))
                self.screens.append(FakeScreen3D(self, 4, shuttle_angle=90, shift_y=-4.0))
        else:
            if self.params("show_3d_windows"):
                for i in range(len(self.screens)):
                    self.screens.pop().destroy()
                self.screens.append(Screen3D(self, 1, shuttle_angle=-90, shift_y=-4.0))
                self.screens.append(Screen3D(self, 2, shuttle_angle=-self.params("front_screen_angle")))
                self.screens.append(Screen3D(self, 3, shuttle_angle=self.params("front_screen_angle")))
                self.screens.append(Screen3D(self, 4, shuttle_angle=90, shift_y=-4.0))

            if self.params("fullscreen"):
                self.control_screen.set_fullscreen()
                for s in self.screens:
                    s.set_fullscreen(True)
                self.control_screen.request_focus()

    def get_time(self, string_format=False, round_result=True):
        """
        Returns the elapsed time in seconds since the last begining (reset) of the game.
        @param string_format: if True, returns the numbers of seconds as string
        @param round_result: if True, round at the seconds level
        @return: the elapsed time in secs.
        """
        if string_format:
            return str(datetime.timedelta(seconds=round(self.clock.get_real_time(), 1)))
        else:
            if round_result:
                return round(self.clock.get_real_time(), 1)
            else:
                return self.clock.get_real_time()

    def reset_game(self):
        """
        Resets the game. Load the scenario if the scenario must be played.
        """
        # TODO : log file
        # redirect print
        # sys.stdout = open("output.txt", "w")

        self.clock.reset()
        self.sound_manager.reset()
        self.init_states()
        self.power.reset()
        self.hardware.reset()
        self.control_screen.event("image_screen")

        if self.params("play_scenario"):
            self.scenario.reset()
            self.load_scenario(self.params('scenario'))

        self.sound_manager.play_ambiant_sound()
        self.shuttle.reset()

    def load_scenario(self, scenario):
        """
        Load the desired scenario
        @param scenario: the string name of the .xml file of the scenario
        """
        self.scenario.load_scenario(scenario)

    def start_game(self):
        """
        Starts the current scenario
        """
        self.scenario.start_game()

    def get_soft_state(self, state_key):
        """
        Gets the desired software tate
        @param state_key: the name of the state
        @return: the state
        """
        return self.soft_states.get(state_key, None)

    def get_hard_state(self, state_key):
        """
        Gets the desired hardware state
        @param state_key: the name of the state
        @return: the state
        """
        return self.hard_states.get(state_key, None)

    def generate_files(self):
        """
        Reads the main_hardware_file and creates the following files :
            - controlled_led_file
            - hardware_map_file
            - power_file
            - soft_state_file
            - hard_state_file
            - hardware_keyboard_map_file
        """
        file = open(self.params("main_hardware_file"), "r")
        lines = file.readlines()[1:]
        file.close()

        controlled_led_file = ""
        hardware_map_file = ""
        power_file = ""
        soft_state_file = ""
        hard_state_file = ""
        hardware_keyboard_map_file = ""

        class Element:
            def __init__(self, line):
                parts = line.split(',')
                self.name = parts[0].strip()
                self.hard_id = parts[1].strip()
                self.type = smart_cast(parts[2].strip())
                self.led_id = parts[3].strip()
                self.init_value = smart_cast(parts[4].strip())
                self.power = smart_cast(parts[5].strip().replace(",", "."))
                self.define_state = smart_cast(parts[6].strip())
                self.keyboard_key = parts[7].strip()

        elements = dict()
        for line in lines:
            e = Element(line)
            elements[e.name] = e
            if isinstance(e.power, (int, float)):
                if e.define_state:
                    power_file += e.name[2:] + "=" + str(e.power) + "\n"
                else:
                    power_file += e.name + "=" + str(e.power) + "\n"

            if e.type == "SOFT":
                soft_state_file += e.name + "=" + str(e.init_value) + "\n"

                if len(e.led_id) > 0:
                    hard_state_file += "l_" + e.name + "=" + str(e.init_value) + "\n"
                    hardware_map_file += e.led_id + "=" + "l_" + e.name + "\n"
                    controlled_led_file += e.name + "=" + "l_" + e.name + "\n"
            else:
                if e.define_state:
                    soft_state_file += e.name[2:] + "=" + str(e.init_value) + "\n"

                if len(e.keyboard_key) > 0:
                    hardware_keyboard_map_file += e.keyboard_key + "=" + e.name + "\n"

                if len(e.hard_id) > 0:
                    hardware_map_file += e.hard_id + "=" + e.name + "\n"

                if len(e.led_id) > 0:
                    hard_state_file += "l_" + e.name[2:] + "=" + str(e.init_value) + "\n"
                    hardware_map_file += e.led_id + "=" + "l_" + e.name[2:] + "\n"
                    if e.define_state:
                        controlled_led_file += e.name[2:] + "=" + "l_" + e.name[2:] + "\n"
                    else:
                        controlled_led_file += e.name + "=" + "l_" + e.name[2:] + "\n"

                hard_state_file += e.name + "=" + str(e.init_value) + "\n"

        def write_to(content, name):
            f = open(self.params(name), "w")
            f.write(content)
            f.close()

        write_to(power_file, "power_balance_file")
        write_to(hardware_map_file, "hardware_map_file")
        write_to(hardware_keyboard_map_file, "hardware_keyboard_map_file")
        write_to(controlled_led_file, "controled_leds_file")
        write_to(hard_state_file, "hardware_states_file")
        write_to(soft_state_file, "software_states_file")

    def update_soft_state(self, state_key, value, force_power=False, silent=False):
        """
        Update a software state of the shuttle and tells the game that the shuttle is updated.
        If this acton requires some power, the engine checks if this action can be performed and update the shuttle power.
        Depending on the name of state, some action are performed and the shuttle is correctly updated.

        @param state_key: must be one of the strings defined in self.game_states
        @param value: the new value (int, float, bool or string depending on the state_key)
        @param force_power: If this action consumes some power, set is to True to ignore the power limits.
        @param silent: if True, no automatic sound is played. Otherwise, the game searches for a sound corresponding to the new state of the soft_state and plays it.
        @return: True if the state exists. False otherwise
        """
        if state_key in self.soft_states:
            if (not self.params("use_power") or force_power or not value or (
                    value and self.params("use_power") and self.power.can_be_switched_on(state_key))) and \
                    self.soft_states[state_key] != value:

                # first, there may be some conditions
                if state_key in ["correction_roulis", "correction_direction",
                                 "correction_stabilisation"] and value and not self.soft_states["pilote_automatique"]:
                    return True
                if state_key.startswith("batterie") and not state_key.endswith('s') and not self.soft_states[
                    "batteries"]:
                    self.sound_manager.play("batterie_wrong")
                    return True
                if state_key.startswith("moteur") and value and self.get_soft_state("collision_occurred"):
                    self.sound_manager.play("engine_fails")
                    return True

                # now we switch it on

                print('\033[93m', "(soft_state): ", state_key, ':', value, '\033[0m')
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

                # check for control_screen:
                self.control_screen.event("update_state", key=state_key)

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
                self.scenario.update_shuttle_state()

                # this may append if the task is automatically fulfilled with f1.
                if state_key == "pilote_automatique_failed" and value:
                    self.soft_states["pilote_automatique_failed"] = False
                    print('\033[93m', "(soft_state): ", state_key, ':', False, '\033[0m')
            else:
                if state_key.startswith('moteur') and value:
                    self.sound_manager.play("engine_fails")
                elif value and not self.power.can_be_switched_on(state_key):
                    self.sound_manager.play("voice_energy_denied")

                    if state_key == "pilote_automatique":
                        # sets the failed to True and immediately after to False.
                        self.soft_states["pilote_automatique_failed"] = True
                        print('\033[93m', "(soft_state): ", state_key, ':', True, '\033[0m')
                        self.scenario.update_shuttle_state()
                        self.soft_states["pilote_automatique_failed"] = False
                        print('\033[93m', "(soft_state): ", state_key, ':', False, '\033[0m')
            return True
        return False

    def update_hard_state(self, state_key, value, silent=False):
        """
        Update a hardware state of the shuttle and tells the game that the shuttle is updated. This can only append if
        the variable 'listen_to_hardware' is set to True. In this case, the game checks if a leds corresponds to this
        new hardware states and switch it on/off. If the hardware states correspnds to a software one, the corresponding
        software state is automatically updated.

        @param state_key: must be one of the strings defined in self.game_states
        @param value: the new value (int, float, bool or string depending on the state_key)
        @param silent: if True, no automatic sound is played. Otherwise, the game searches for a sound corresponding to the new state of the soft_state and plays it.
        @return: True if the state exists. False otherwise
        """
        if state_key == "b_admin":
            self.hard_states[state_key] = value
            # always listen to it
            self.scenario.update_shuttle_state()

        # only do it if the key exists and if we listen to hardware and if the value is different from the previous one (to avoid spamminf of joysticks_axis = 0.0
        elif state_key in self.hard_states and self.get_soft_state("listen_to_hardware") and value != self.hard_states[
            state_key]:
            print('\033[94m', "(hard_state): ", state_key, ':', value, '\033[0m')
            self.hard_states[state_key] = value

            # check if it is associated to one led
            self.hardware.check_constrained_led(state_key, value)

            # maybe it plays an automatic sound
            if not silent:
                if value:
                    self.sound_manager.play(state_key + "_on")
                else:
                    self.sound_manager.play(state_key + "_off")

            self.scenario.update_shuttle_state()

            # particular cases:
            if state_key == "b_freq_moins" and value:
                self.update_soft_state("freq_comm",
                                       self.get_soft_state("freq_comm") - self.params("freq_comm_increment"),
                                       silent=silent)
            elif state_key == "b_freq_plus" and value:
                self.update_soft_state("freq_comm",
                                       self.get_soft_state("freq_comm") + self.params("freq_comm_increment"),
                                       silent=silent)
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
            else:
                # now check if it controls a software value
                self.update_soft_state(state_key.split('_', 1)[1], value)

            return True
        return False

    def init_states(self):
        """
        This reads the game states.
        """
        self.hard_states = read_ini_file(self.params("hardware_states_file"))
        self.soft_states = read_ini_file(self.params("software_states_file"))
