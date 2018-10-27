from Engine.ControlScreens.MainScreen import LoadIcon
from Engine.ControlScreens.Screen import Screen
from Engine.Utils.utils import read_ini_file


class AlertScreen(Screen):
    """
    The alert screen that popups after the collision
    """
    def __init__(self, mainScreen):
        self.current_task = 0
        self.task_list = list()

        Screen.__init__(self, mainScreen, "alert",
                        entry_gimp_pos=(508, 430),
                        entry_size=0.3)
        self.name = "alert_screen"
        self._listen_to_input = False

        # tell the game that the screen is locked
        self.main_screen.gameEngine.update_soft_state('alert_screen_unlocked', False)

        self.add_on_screen_text(319, 440, name="task", may_change=True, size=0, text="")
        self.hide_on_screen_texts()

        self.main_screen.gameEngine.sound_manager.play("alarm", loop=True,
                                                       volume=self.main_screen.gameEngine.params("alarm_volume"))

        self.wait_logo = LoadIcon(mainScreen, x=0.3, y=-0.38)
        self.wait_logo.start()
        self._update()

        # showing the unlock screen in a few secs.
        def task(t):
            self._listen_to_input = True
            self.wait_logo.stop()
            self.main_screen.set_background_image("alert_lock")
            self.set_screen()
            self.main_screen.gameEngine.sound_manager.play("voice_mdp")
            self.main_screen.info_text("Entrer le mot de passe inscrit sur la valve O2-5 qui se trouve dans la navette")
            self._update()

        self.main_screen.gameEngine.taskMgr.doMethodLater(2, self.main_screen.gameEngine.sound_manager.play, "as1",
                                                          extraArgs=['voice_alert'])
        self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, task, "as2")

    def set_screen(self):
        self.set_on_screen_text("task", self.task_list[self.current_task], False)
        self.show_on_screen_texts()

    def load_passwords(self):
        passwords = read_ini_file(self.main_screen.gameEngine.params("control_screen_code_file"), cast=False)
        for task in passwords:
            if task.startswith('alert_'):
                name = task.replace('alert_', '')
                self.task_list.append(name)
                self.passwords[name] = passwords[task]

    def check_input(self):
        if self.check_password(self.task_list[self.current_task]):
            self.reset_text(sound="ok", update=False)
            self.current_task += 1
            if self.current_task >= len(self.task_list):
                self._listen_to_input = False
                self.main_screen.set_background_image("alert_ok")
                self.hide_on_screen_texts()
                self.wait_logo.set_pos(0, -0.5)
                self.wait_logo.start()

                self.main_screen.gameEngine.sound_manager.stop("alarm")

                def unlock(t):
                    self.wait_logo.stop()
                    self.main_screen.gameEngine.update_soft_state('alert_screen_unlocked', True)
                    self.call_main_screen("default_screen")

                self.main_screen.gameEngine.taskMgr.doMethodLater(1, self.main_screen.gameEngine.sound_manager.play,
                                                                  "unlock0", extraArgs=["voice_alert_done"])
                self.main_screen.gameEngine.taskMgr.doMethodLater(10.0, unlock, "unlock")
            else:
                self.set_screen()
            self._update()
        else:
            self.reset_text("wrong")