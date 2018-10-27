from Engine.ControlScreens.MainScreen import LoadIcon
from Engine.ControlScreens.Screen import Screen
from Engine.Utils.utils import read_ini_file


class TargetScreen(Screen):
    """
    The target screen to be unlocked
    """
    def __init__(self, mainScreen):
        Screen.__init__(self, mainScreen, "coordinates_lock",
                        entry_gimp_pos=(275, 305),
                        entry_size=0.5,
                        max_char=12)
        # getting the base name
        self.target_name = list(self.passwords)[0]
        self.name = "target_screen"

        self._listen_to_input = True
        self._current_target = None

        self.wait_logo = LoadIcon(self.main_screen)

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('target_screen_unlocked', False)

        self.add_on_screen_text(250, 250,
                                text="Longitude (N) de la base " + self.target_name,
                                size=1,
                                may_change=True,
                                name="text"
                                )

        self.add_on_screen_text(450, 310,
                                text="",
                                size=2,
                                name="target")

        self.hide_on_screen_texts("target")

        # do it twice to secure
        self._update()

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for key in passwords:
            if key.startswith('target_'):
                self.passwords[key.replace('target_', "")] = passwords[key]

    def _update(self):
        # take correction into account
        self.lock_text["text"] = self.lock_text["text"].replace(" ", "")
        text = ""
        for i, a in enumerate(self.lock_text["text"]):
            text += a
            if i in [1, 3]:
                text += "   "
        self.lock_text["text"] = text
        Screen._update(self)

    def process_text(self, char):
        if self._listen_to_input:
            if char == "enter":
                self.check_input()
            elif char == "back":
                if len(self.lock_text["text"]) > 0:
                    self.lock_text["text"] = self.lock_text["text"].replace(" ", "")
                    self.lock_text["text"] = self.lock_text["text"][0:-1]
                    self._update()
            elif len(self.lock_text["text"]) < self.max_char:
                self.lock_text["text"] += char
                self._update()

    def check_input(self):
        if self._current_target is None:
            # check if the passwords corresponds to one target
            for p in self.passwords:
                if str(self.passwords[p][0]) == self.lock_text["text"].replace(" ", ""):
                    self.reset_text("ok", update=False)
                    self.set_on_screen_text("text",
                                            "Latitude (E) de la base " + self.target_name,
                                            update=False)
                    self._current_target = p
                    self._update()
                    break

            if self._current_target is None:
                self.reset_text("wrong")

        elif str(self.passwords[self._current_target][1]) == self.lock_text["text"].replace(" ", ""):
            self.reset_text("ok", update=False)
            self.main_screen.set_background_image("coordinates_ok")
            self.wait_logo.set_pos(0.3, -0.3)
            self.wait_logo.start()

            self._listen_to_input = False

            self.main_screen.gameEngine.update_soft_state("target_name", self._current_target)
            self.hide_on_screen_texts("text")
            self.set_on_screen_text("target", self._current_target)
            self.show_on_screen_texts("target")

            self.main_screen.gameEngine.sound_manager.play("voice_target_ok")

            def unlock(t):
                self.wait_logo.stop()
                self.main_screen.gameEngine.update_soft_state('target_screen_unlocked', True)
                self.call_main_screen("default_screen")

            self.main_screen.gameEngine.taskMgr.doMethodLater(7.0,
                                                              self.main_screen.gameEngine.sound_manager.play,
                                                              "sound_ts",
                                                              extraArgs=["voice_target_on"])
            self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, "unlock")
            self._update()
        else:
            self.reset_text("wrong")