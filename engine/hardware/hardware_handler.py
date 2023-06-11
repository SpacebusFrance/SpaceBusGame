from typing import Union, Any

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
        self._axes_value = dict()

        # self.firewall_time = 0.05
        self.firewall_time = self.engine('hardware_input_firewall_time')
        for j in range(3):
            for b in range(10):
                self.times[f'joystick{j}-button{b}'] = self.engine.get_time(round_result=False)
                self.tasks[f'joystick{j}-button{b}'] = None

    @event('enable_hardware')
    def enable_inputs(self) -> None:
        """
        Enable hardware inputs
        """
        # remove all stored events
        pygame.event.clear()
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
        self._arduino.led_off(led_id)

    def destroy(self):
        """
        Destroy this class
        """
        pygame.quit()

    def _event_polling(self, task):

        for ev in pygame.event.get():
            event_name = ""
            value = None
            axis_moved = True
            if ev.type == pygame.JOYBUTTONDOWN or ev.type == pygame.JOYBUTTONUP:
                event_name = 'joystick%d-button%d' % (ev.joy, ev.button)
                value = ev.type == pygame.JOYBUTTONDOWN
            elif ev.type == pygame.JOYAXISMOTION:
                event_name = 'joystick%d-axis%d' % (ev.joy, ev.axis)
                # value should be [-1, 0, 1]
                value = round(ev.value)
                # only trigger an event if axes changed value
                # as in 0 to 1 or -1 to 0 etc
                axis_moved = value != self._axes_value.get(event_name, 0)
                # store this value for next comparison
                self._axes_value[event_name] = value

            if len(event_name) > 0 and axis_moved and not event_name.endswith('axis2'):
                # try to avoid repetition of the same
                # event in a short time. We start by
                # computing time delta from previous
                # record of the same event
                t0 = self.engine.get_time(round_result=False)
                dt = t0 - self.times.get(event_name, t0 - 10.0)
                # we store event time in corresponding
                # event
                self.times[event_name] = t0

                # todo: only listen for registrered events !!
                if dt > self.firewall_time:
                    # if delta is larger than
                    # firewall_time, we send an event in
                    # 1.1 * firewall_time
                    # the risk is that the same event is fired
                    # a few µs latter, hence the event is
                    # effectively sent after firewall_time
                    Logger.info(f'sending event "{event_name}" in {self.firewall_time} seconds')
                    # todo: check why that does work ...
                    # messenger.send(event_name, sentArgs=[value])
                    self.tasks[event_name] = self.engine.task_mgr.do_method_later(
                        self.firewall_time,
                        # messenger.send,
                        # extraArgs=[event_name, {'sentArgs': value}],
                        self._process_event,
                        extraArgs=[event_name, value],
                        # lambda *_: messenger.send(event_name, sentArgs=[value]),
                        name=event_name
                    )

                elif self.tasks[event_name] is not None:
                    # the same event was fired just before,
                    # we consider that this event and the previous
                    # one are ghost. We remove the task
                    Logger.warning(f"possible ghost from {event_name} with value {value}.")
                    self.tasks[event_name].remove()
        return task.cont

    @staticmethod
    def _process_event(event_name: str, value: Any) -> None:
        messenger.send(event_name, sentArgs=[value])


if __name__ == '__main__':
    class Test(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.arduino = WriteOnlyArduino(self)
            self.arduino.all_off()
            self.arduino.led_on('54')
            # self.arduino.led_on('55')


    main = Test()
    # main.run()
