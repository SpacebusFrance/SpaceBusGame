import random

from Engine.ControlScreens.MainScreen import LoadIcon
from Engine.ControlScreens.Screen import Screen
from Engine.Utils.utils import read_ini_file


class LockScreen(Screen):
    """
    The lock screen that must be unlocked by crew.
    """
    def __init__(self, mainScreen, num_player=None):
        self.current_lock = 0
        self._listen_to_input = True
        self.crew_list = list()
        self.main_screen = mainScreen
        self.max_lock = num_player if num_player is not None else self.main_screen.gameEngine.params(
            "default_num_player")

        # done after since it needs crew_list
        Screen.__init__(self, mainScreen,
                        image_name="crew_lock",
                        entry_gimp_pos=(375, 357),
                        entry_size=0,
                        max_char=6)

        self.name = "lock_screen"
        self.wait_logo = LoadIcon(self.main_screen)

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('crew_screen_unlocked', False)

        self.add_on_screen_text(97, 352,
                                text="test",
                                size=2,
                                name="crew",
                                may_change=True,
                                )

        self.set_screen()
        self._update()
        self._update()

    def set_screen(self):
        self.set_on_screen_text("crew",
                                self.crew_list[self.current_lock].strip(),
                                update=False)

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for c in passwords:
            if c.startswith('crew_'):
                name = c.replace('crew_', '')
                self.crew_list.append(name)
                self.passwords[name] = passwords[c]
        # select random names
        if self.max_lock < len(self.crew_list):
            new_list = []
            new_pass = dict()
            for i in range(self.max_lock):
                new_list.append(self.crew_list.pop(random.choice(range(len(self.crew_list)))))
                new_pass[new_list[-1]] = self.passwords[new_list[-1]]
            self.crew_list = new_list
            self.passwords = new_pass

    def check_input(self):
        if self.check_password(self.crew_list[self.current_lock]):
            self.current_lock += 1

            self.reset_text(sound="ok", update=False)

            if self.current_lock >= self.max_lock:
                self.main_screen.set_background_image("unlocked")
                self._listen_to_input = False
                self.hide_on_screen_texts()

                self.wait_logo.set_pos(0.2, -0.16)
                self.wait_logo.start()

                self.main_screen.gameEngine.sound_manager.play("voice_identify_ok")

                def unlock(t):
                    self.wait_logo.stop()
                    self.main_screen.gameEngine.update_soft_state('crew_screen_unlocked', True)
                    self.call_main_screen("default_screen")

                # tell the game that the screen is unlocked
                self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, name="unlock")
            else:
                # setting new screen
                self.set_screen()
                # self.set_screen(time=2)
                self.transition_screen("crew_ok", time=2)

            self._update()
        else:
            self.transition_screen("crew_wrong", time=2)
            self.reset_text(sound="wrong")