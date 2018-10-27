from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText, TextNode


class Screen:
    """
    This class represents the actual behaviour of the ControlScreen. Each different behaviour is encoded as a child class of this general Screen class
    """
    def __init__(self, MainScreen, image_name=None, entry_gimp_pos=None, entry_size=1.0, max_char=7):
        """
        Creates the class.
        @param MainScreen: The ControlScreen class
        @param image_name: the name of the background image to display.
        @param entry_gimp_pos: the position of the entry if there is one. Positions are given in Gimp positions.
        @param entry_size: The size of the entry text.
        @param max_char: The max number of characters accepted in the entry.
        """
        self.main_screen = MainScreen
        self.name = ""
        self.max_char = max_char
        if image_name is not None:
            self.main_screen.set_background_image(image_name)
        scale_x = .1 + entry_size * 0.05
        scale_y = scale_x
        self.lock_text = OnscreenText(text="",
                                      pos=self.main_screen.gimp_pos(
                                          *entry_gimp_pos) if entry_gimp_pos is not None else (0, 0),
                                      scale=(scale_x, scale_y
                                             ),
                                      align=TextNode.ABoxedLeft,
                                      font=self.main_screen.font,
                                      fg=self.main_screen.fg_color,
                                      parent=self.main_screen.gui_render_node,
                                      )
        self._listen_to_input = True
        self.on_screen_texts = dict()

        self.info_screen = None

        self.passwords = dict()
        self.load_passwords()

    def load_passwords(self):
        """
        To be implemented in each child class.
        """
        pass

    def add_on_screen_text(self, xg, yg, text, size=1.0, name=None, may_change=False, color=None):
        """
        Adds text on the screen
        @param xg: the x Gimp position of the text
        @param yg: the y Gimp position of the text
        @param text: the text itself
        @param size: the size of the text
        @param name: the name of this text (if you want to change it later)
        @param may_change: True if the text may change. False otherwise
        @param color: the color of the text, can be "green", "red" or black by default.
        """
        name = text if name is None else name
        if name not in self.on_screen_texts:
            if color == 'red':
                fg = self.main_screen.fg_color_red
            elif color == "green":
                fg = self.main_screen.fg_color_green
            else:
                fg = self.main_screen.fg_color
            x_scale = 0.04 + 0.01 * size
            y_scale = x_scale * 16 / 9
            self.on_screen_texts[name] = OnscreenText(text=text,
                                                      align=TextNode.ALeft,
                                                      mayChange=may_change,
                                                      pos=self.main_screen.gimp_pos(xg, yg),
                                                      scale=(x_scale, y_scale),
                                                      font=self.main_screen.font,
                                                      fg=fg,
                                                      parent=self.main_screen.gui_render_node,
                                                      )

    def hide_on_screen_texts(self, names=None):
        """
        Hide some texts displayed on the screen
        @param names: the names of the texts to hide. Can be a string or a list of strings. If None, all texts are hidden.
        """
        if names is None:
            for ost in self.on_screen_texts:
                self.on_screen_texts[ost].hide()
        elif isinstance(names, list):
            for l in names:
                if l in self.on_screen_texts:
                    self.on_screen_texts[l].hide()
        elif names in self.on_screen_texts:
            self.on_screen_texts[names].hide()

    def show_on_screen_texts(self, names=None):
        """
        Shows some texts displayed on the screen
        @param names: the names of the texts to hide. Can be a string or a list of strings. If None, all texts are hidden.
        """
        if names is None:
            for ost in self.on_screen_texts:
                self.on_screen_texts[ost].show()
        elif isinstance(names, list):
            for l in names:
                if l in self.on_screen_texts:
                    self.on_screen_texts[l].show()
        elif names in self.on_screen_texts:
            self.on_screen_texts[names].show()

    def set_on_screen_text(self, name, new_text, update=True, color=None):
        """
        Updates a text displayed on the screen
        @param name: the name of the text to update
        @param new_text : the new text to diaplay
        @param update : if the main screen is not automatically updated, updates the screen
        @param color: to set the new color of the text.
        """
        if name in self.on_screen_texts:
            self.on_screen_texts[name]["text"] = new_text
            if color is not None:
                if color == "green":
                    self.on_screen_texts[name]["fg"] = self.main_screen.fg_color_green
                elif color == "red":
                    self.on_screen_texts[name]["fg"] = self.main_screen.fg_color_red
                else:
                    self.on_screen_texts[name]["fg"] = color
            if update:
                self._update()

    def listen_to_input(self, listen):
        """
        Specifies if keyboard input are considered or not.
        @param listen: a boolean
        """
        self._listen_to_input = listen

    def call_main_screen(self, message):
        """
        Sends a message (event) to the main ControlScreeen (e.g. changing the screen)
        @param message: the message (event)
        """
        self.main_screen.event(message)

    def _update(self):
        self.main_screen.update()

    def destroy(self):
        """
        Destroys the current screen
        """
        self.lock_text.destroy()
        for element in self.on_screen_texts.values():
            element.destroy()

    def check_input(self):
        """
        To be implemnetd in child class. Check if the input in the entry corresponds to the desired password or not
        """
        pass

    def check_password(self, key, text=None):
        """
        Checks if the text corresponds to te password named 'key'
        @param key: the key of the password
        @param text: the text to check. If None, the text is the one entered in the entry.
        @return: a boolean
        """
        text = text if text is not None else self.lock_text["text"]
        if len(text) > 0 and key in self.passwords:
            return text in self.passwords[key]
        return False

    def reset_text(self, sound=None, update=True):
        """
        Resets the entry text.
        @param sound: name of the sound to play
        @param update: update or not the screen
        """
        self.lock_text["text"] = ""
        if sound is not None:
            self.main_screen.gameEngine.sound_manager.play(sound)
        if update:
            self._update()

    def transition_screen(self, image, time):
        """
        Creates a transition screen. An image is popup while listening to input is set to False
        @param image: the image name
        @param time: the lifetime of the popup.
        """
        new_image = OnscreenImage(self.main_screen.image_path + image + ".png",
                                  parent=self.main_screen.gui_render_node,
                                  pos=(0, 0, 0),
                                  )
        new_image.set_bin("fixed", 10)
        new_image.show()
        self._update()

        # hidding on_screen_texts
        for o in self.on_screen_texts:
            self.on_screen_texts[o].hide()

        relisten = False
        if self._listen_to_input:
            self._listen_to_input = False
            relisten = True
            self.lock_text.hide()

        def to_call(relisten):
            if relisten:
                self._listen_to_input = True
                self.lock_text.show()

            new_image.destroy()
            # showing on_screen_texts
            for o in self.on_screen_texts:
                self.on_screen_texts[o].show()

            self._update()

        self.main_screen.gameEngine.taskMgr.doMethodLater(time, to_call, name="update", extraArgs=[relisten])

    def process_text(self, char):
        """
        Process the incoming text
        @param char: the sent string
        """
        if self._listen_to_input:
            if char == "enter":
                self.check_input()
            elif char == "back":
                if len(self.lock_text["text"]) > 0:
                    self.lock_text["text"] = self.lock_text["text"][0:-1]
                    self._update()
            elif len(self.lock_text["text"]) < self.max_char:
                self.lock_text["text"] += char
                self._update()