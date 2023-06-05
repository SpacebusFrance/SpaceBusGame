from typing import Union

import pygame
from engine.utils.event_handler import EventObject, event, send_event
from direct.showbase.MessengerGlobal import messenger
from direct.showbase.ShowBase import ShowBase

from engine.hardware.arduino import WriteOnlyArduino
from engine.utils.logger import Logger


class HardwareHandler(EventObject):
    def __init__(self, engine):
        super().__init__()
        pygame.init()

        self.engine = engine

        # self.events_dict = dict()
        # self.controlled_leds = dict()

        # build the dictionaries
        # for c, l in self.engine.hardware_map[['hardware_key', 'id', 'led_id']].iterrows():
        #     if l['led_id'] != "":
        #         self.events_dict[str(int(l["led_id"]))] = "l_" + l["id"].replace('s_', '').replace('b_', "").replace("j_", "")
        #         self.controlled_leds[l["id"].replace('s_', '').replace('b_', "").replace("j_", "")] = \
        #             "l_" + l["id"].replace('s_', '').replace('b_', "").replace("j_", "")
        #     if l["hardware_key"] != "":
        #         self.events_dict[l["hardware_key"]] = l['id']

        # looking for Arduino
        self._arduino = WriteOnlyArduino(self.engine)

        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            # check to avoid the accelerometer
            if "Accelerometer" not in pygame.joystick.Joystick(i).get_name():
                self._joysticks.append(pygame.joystick.Joystick(i))
                self._joysticks[-1].init()

        # ghost firewall
        self.times = dict()
        self.tasks = dict()
        # self.firewall_time = 0.05
        self.firewall_time = self.engine('hardware_input_firewall_time')
        for j in range(3):
            for b in range(10):
                self.times[f'joystick{j}-button{b}'] = self.engine.get_time(round_result=False)
                self.tasks[f'joystick{j}-button{b}'] = None

    # def myFunc(self, keyname):
    #         print('key down:', keyname)

    # def _hardware_state(self, key):
    #     if key is None:
    #         return self.engine.hard_states
    #     return self.engine.get_hard_state(key)

    @event('enable_hardware')
    def enable_inputs(self) -> None:
        """
        Enable hardware inputs
        """
        self.engine.taskMgr.add(self._event_polling, 'Hardware_Polling')
        # self.engine.update_soft_state("listen_to_hardware", True)
        self.engine.state_manager.listen_to_hardware.set_value(True)

    @event('disable_hardware')
    def disable_inputs(self) -> None:
        """
        Disable hardware inputs
        """
        self.engine.taskMgr.remove('Hardware_Polling')
        # self.engine.update_soft_state("listen_to_hardware", False)
        self.engine.state_manager.listen_to_hardware.set_value(False)

    def reset(self):
        """
        Set all leds off
        """
        self._arduino.all_off()

    # def init_states(self):
    #     """
    #     Reads the initial state of all switches and sets the corresponding leds
    #     """
    #     states = self._hardware_state(None)
    #
    #     for val in states:
    #         if val.startswith('l_'):
    #             if states[val]:
    #                 self.set_led_on(val)
    #             else:
    #                 self.set_led_off(val)
    #
    #     # new loop over dependant leds
    #     for led_name in self.controlled_leds:
    #         if led_name in states:
    #             if states[led_name]:
    #                 self.set_led_on(led_name)
    #             else:
    #                 self.set_led_off(led_name)

    def all_leds_on(self):
        """
        Set all leds on
        """
        self._arduino.all_on()

    def all_leds_off(self):
        """
        Switch all leds off
        """
        self._arduino.all_off()

    def hello_world(self):
        """
        switch all leds on, one after each other and switch them off
        """
        self._arduino.hello_world()

    def switch_led_on(self, led_id: Union[int, str]) -> None:
        """
        Set a led on

        Args:
            led_id (str): the *id* of the led
        """
        self._arduino.led_on(led_id)

    def switch_led_off(self, led_id: Union[int, str]) -> None:
        """
        Switch a led off

        Args:
            id_id (str): the *id* of the led
        """
        self._arduino.led_on(led_id)

    def destroy(self):
        """
        Destroy this class
        """
        pygame.quit()

    # def simulate_input(self, event_code, value):
    #     """
    #     Simulate an input
    #
    #     Args:
    #         event_code (str): the name of the event
    #         value (bool): the value
    #     """
    #     if event_code in self.events_dict:
    #         messenger.send(self.events_dict[event_code], [value])
    #     else:
    #         Logger.warning(event_code, "is not in the event list !")

    # def check_constrained_led(self, event_name, value):
    #     """
    #     React to an event and switch on/off the led if there is one attached
    #
    #     Args:
    #         event_name (str): the name of the event
    #         value (bool): the value
    #     """
    #     if event_name in self.controlled_leds:
    #         if value:
    #             Logger.info("setting led", event_name, "on")
    #             self.set_led_on(self.controlled_leds[event_name])
    #         else:
    #             Logger.info("setting led", event_name, "off")
    #             self.set_led_off(self.controlled_leds[event_name])

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

            if len(event_name) > 0:
                # in_game_name = self.events_dict.get(event_name, None)
                # if in_game_name is not None:
                t0 = self.engine.get_time(round_result=False)
                if event_name in self.times:
                    dt = t0 - self.times[event_name]
                else:
                    dt = 10.
                self.times[event_name] = t0

                if dt > self.firewall_time:
                    Logger.warning(f'sending event "{event_name}" in {1.1 * self.firewall_time:.2f} seconds')
                    self.tasks[event_name] = self.engine.task_mgr.do_method_later(
                        1.1 * self.firewall_time,
                        lambda *_: messenger.send(event_name, sentArgs=[value]),
                        name=event_name
                    )

                    # # if it is a switch, we just reverse its value
                    # if in_game_name.startswith("s_"):
                    #     value = not self._hardware_state(in_game_name)
                    # self.tasks[event_name] = self.engine.task_mgr.do_method_later(
                    #     1.1 * self.firewall_time,
                    #     self._process_event,
                    #     name=event_name,
                    #     extraArgs=[in_game_name, value])
                elif self.tasks[event_name] is not None and self.engine("show_buttons_ghosts"):
                    Logger.warning("possible ghost from", event_name)
                    self.tasks[event_name].remove()
        return task.cont

    def _process_event(self, in_game_name, value):
        self.engine.update_hard_state(in_game_name, value)


if __name__ == '__main__':
    class Test(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.arduino = WriteOnlyArduino(self)
            self.arduino.all_off()
            self.arduino.led_off(54)
            self.arduino.led_off(55)


    main = Test()
    # main.run()
