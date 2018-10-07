import time

import pygame
from direct.showbase.ShowBase import ShowBase

BUTTONON = pygame.USEREVENT + 1
BUTTONOFF = pygame.USEREVENT + 2


class InputListener:
    def __init__(self, base):
        pygame.init()
        self.gameEngine = base

        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            # check to avoid the accelerometer
            if "Accelerometer" not in pygame.joystick.Joystick(i).get_name():
                print("Joystick detected.")
                self._joysticks.append(pygame.joystick.Joystick(i))
                self._joysticks[-1].init()

        self.hardware = dict()
        self.times = dict()
        self.tasks = dict()
        self.lock_time = 0.05

        for j in range(3):
            for a in range(3):
                self.hardware['joystick' + str(j) + '-axis' + str(a)] = False
                self.times['joystick' + str(j) + '-axis' + str(a)] = time.time()
                self.tasks['joystick' + str(j) + '-axis' + str(a)] = None
            for b in range(10):
                self.hardware['joystick' + str(j) + '-button' + str(b)] = False
                self.times['joystick' + str(j) + '-button' + str(b)] = time.time()
                self.tasks['joystick' + str(j) + '-button' + str(b)] = None
        print("\033[92mReset\033[0m")

        self.gameEngine.taskMgr.add(self._event_polling, 'Hardware_Polling')

    def destroy(self):
        pygame.quit()

    def get_joysticks(self):
        return self._joysticks

    def get_joystick_number(self):
        return len(self._joysticks)

    def get_buttons_number(self, joy_number):
        if 0 <= joy_number < len(self._joysticks):
            return self._joysticks[joy_number].get_numbuttons()

    def send(self, name, value, dt):
        print("received event :\033[94m", name, "\033[0m with value : \033[95m", value, '\033[0m (', dt, ')')

    def _event_polling(self, task):
        event_name = ""
        value = None

        E = pygame.event.get()
        for ev in E:
            if ev.type is pygame.JOYBUTTONDOWN:
                event_name = 'joystick%d-button%d' % (ev.joy, ev.button)
                value = True
            elif ev.type is pygame.JOYBUTTONUP:
                event_name = 'joystick%d-button%d' % (ev.joy, ev.button)
                value = False
            elif ev.type is pygame.JOYAXISMOTION:
                event_name = 'joystick%d-axis%d' % (ev.joy, ev.axis)
                value = ev.value
            if len(event_name) > 0:
                if event_name in self.hardware and int(value) != int(
                        self.hardware[event_name]) or event_name not in self.hardware:
                    dT = time.time() - self.times[event_name]
                    if dT > self.lock_time:
                        self.hardware[event_name] = value
                        self.times[event_name] = time.time()
                        self.tasks[event_name] = self.gameEngine.task_mgr.do_method_later(1.1 * self.lock_time,
                                                                                          self.send,
                                                                                          name=event_name + "_send",
                                                                                          extraArgs=[event_name, value,
                                                                                                     dT])
                    else:
                        # print("\033[92mPossible ghost from", event_name, "\033[0m (", dT, ')')
                        self.hardware[event_name] = value

                        self.times[event_name] = time.time()
                        if self.tasks[event_name] is not None:
                            self.tasks[event_name].remove()
                        # self.gameEngine.remove_task(event_name+"_send")
        return task.cont


if __name__ == '__main__':
    print("listening for hardware")


    class Test(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.listener = InputListener(self)


    main = Test()
    main.run()
