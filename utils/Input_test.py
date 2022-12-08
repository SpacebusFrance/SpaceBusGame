import pygame
import serial
import time
from direct.showbase import DirectObject
from direct.showbase.MessengerGlobal import messenger
import serial.tools.list_ports
from direct.showbase.ShowBase import ShowBase
from utils import read_ini_file, get_key_from_value


class WriteOnlyArduino:
    def __init__(self, gameEngine):
        self.task_mgr = gameEngine.task_mgr
        self.gameEngine = gameEngine
        ports = list(serial.tools.list_ports.comports())
        self.board = None
        for p in ports:
            print(p, p[2], 'description :', p.description)
            if "ttyACM0" in p.description:
                self.board = serial.Serial(p[0], 9600, timeout=5)

        if self.board is None:
            print("No _arduino connected !")
        else:
            if self.board.isOpen():
                print("port is open. Closing it")
                self.board.close()

            print("opening the port")
            self.board.open()

        time.sleep(1.0)
        self.all_off()

    def hello_world(self):
        self.all_off()
        for i in range(50):
            self.led_on(i)
            time.sleep(.1)
        time.sleep(1.0)
        self.all_off()

    def send(self, s):
        if self.board is not None:
            self.board.write(str.encode(str(s.strip())))

    def led_on(self, id):
        if isinstance(id, list):
            for i in id:
                self.send("<" + str(i) + "-1>")
        else:
            self.send("<" + str(id) + "-1>")

    def led_off(self, id):
        if isinstance(id, list):
            for i in id:
                self.send("<" + str(i) + "-0>")
        else:
            self.send("<" + str(id) + "-0>")

    def all_on(self):
        self.send("<on>")

    def all_off(self):
        self.send("<off>")


class HardwareHandler(DirectObject.DirectObject):
    def __init__(self, base):
        DirectObject.DirectObject.__init__(self)
        pygame.init()

        self.gameEngine = base

        self.events_dict = read_ini_file(self.gameEngine.params("hardware_map_file"))
        # controlled leds
        self.controlled_leds = read_ini_file(self.gameEngine.params("controled_leds_file"))

        # looking for Arduino
        self.arduino = WriteOnlyArduino(self.gameEngine)

        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            # check to avoid the accelerometer
            if "Accelerometer" not in pygame.joystick.Joystick(i).get_name():
                self._joysticks.append(pygame.joystick.Joystick(i))
                self._joysticks[-1].init()

        # add the task only if it makes sense
        if len(self._joysticks) > 0:
            self.gameEngine.taskMgr.add(self._event_polling, 'Hardware_Polling')

        # ghost firewall
        self.times = dict()
        self.tasks = dict()
        self.firewall_time = self.gameEngine.params("hardware_input_firewall_time")
        for j in range(3):
            for b in range(10):
                self.times['joystick'+str(j)+'-button'+str(b)] = self.gameEngine.get_time(round_result=False)
                self.tasks['joystick'+str(j)+'-button'+str(b)] = None

        self.all_leds_off()

    def _hardware_state(self, key):
        if key is None:
            return self.gameEngine.hard_states
        return self.gameEngine.get_hard_state(key)

    def reset_leds(self):
        """
        Reads the initial state of all switches and sets the corresponding leds to on/off
        """
        hardwares = self._hardware_state(None)

        for val in hardwares:
            if val.startswith('l_'):
                if hardwares[val]:
                    self.set_led_on(val)
                else:
                    self.set_led_off(val)

        # new loop over dependant leds
        for led_name in self.controlled_leds:
            if led_name in hardwares:
                if hardwares[led_name]:
                    self.set_led_on(led_name)
                else:
                    self.set_led_off(led_name)

    def all_leds_on(self):
        self.arduino.all_on()

    def all_leds_off(self):
        self.arduino.all_off()

    def hello_world(self):
        self.arduino.hello_world()

    def set_led_on(self, led_name):
        for key in self.events_dict:
            if self.events_dict[key] == led_name:
                self.arduino.led_on(key)
                return
        print("Led on.", led_name, "not found in self.event_dict")

    def set_led_off(self, led_name):
        for key in self.events_dict:
            if self.events_dict[key] == led_name:
                self.arduino.led_off(key)
                return
        print("Led off.", led_name, "not found in self.event_dict")

    def destroy(self):
        pygame.quit()

    # def get_joysticks(self):
    #     return self._joysticks
    #
    # def get_joystick_number(self):
    #     return len(self._joysticks)
    #
    # def get_buttons_number(self, joy_number):
    #     if 0 <= joy_number < len(self._joysticks):
    #         return self._joysticks[joy_number].get_numbuttons()

    def simulate_input(self, event_code, value):
        if event_code in self.events_dict:
            messenger.send(self.events_dict[event_code], [value])
        else:
            print(event_code, "is not in the event list !!")

    def check_constrained_led(self, event_name, value):
        if event_name in self.controlled_leds:
            if value:
                print("\033[96m (info) setting led", event_name, "on\033[0m")
                self.set_led_on(self.controlled_leds[event_name])
            else:
                print("\033[96m (info) setting led", event_name, "off\033[0m")
                self.set_led_off(self.controlled_leds[event_name])

    def _event_polling(self, task):
        event_name = ""
        value = None
        for ev in pygame.event.get():
            if ev.type is pygame.JOYBUTTONDOWN or ev.type is pygame.JOYBUTTONUP:
                event_name = 'joystick%d-button%d' % (ev.joy, ev.button)
                value = ev.type is pygame.JOYBUTTONDOWN
            elif ev.type is pygame.JOYAXISMOTION:
                event_name = 'joystick%d-axis%d' % (ev.joy, ev.axis)
                value = ev.value

            in_game_name = self.events_dict.get(event_name, None)
            if in_game_name is not None:
                t0 = self.gameEngine.get_time(round_result=False)
                if event_name in self.times:
                    dt = t0 - self.times[event_name]
                else:
                    dt = 10.
                self.times[event_name] = t0

                if dt > self.firewall_time:
                    # if it is a switch, we just reverse its value
                    if in_game_name.startswith("s_"):
                        value = not self._hardware_state(in_game_name)
                    self.tasks[event_name] = self.gameEngine.task_mgr.do_method_later(1.1 * self.firewall_time,
                                                                                      self._process_event,
                                                                                      name=event_name,
                                                                                      extraArgs=[in_game_name, value])
                else:
                    # firewall !
                    if self.tasks[event_name] is not None:
                        print("\033[92mPossible ghost from", event_name, "\033[0m (", dt, ')')
                        self.tasks[event_name].remove()
        return task.cont

    def _process_event(self, in_game_name, value):
        self.gameEngine.update_hard_state(in_game_name, value)


if __name__ == '__main__':

    class Test(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.arduino = WriteOnlyArduino(self)
            # self._arduino.led_on([1, 2, 25, 17, 16, 8, 35, 15, 12, 10])
            self.arduino.all_off()
            # self._arduino.led_on(54)
            # self._arduino.led_on(55)
            # time.sleep(5)
            # self._arduino.all_off()
            # self._arduino.hello_world()
            # self._arduino.led_off(54)
            # self._arduino.led_off(55)

    main = Test()
    # main.run()
