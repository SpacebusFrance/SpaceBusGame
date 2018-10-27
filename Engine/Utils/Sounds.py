from os import listdir
import numpy as num
from Engine.Utils.utils import read_file_as_list, Logger


class SoundManager:
    def __init__(self, gameEngine):
        self._sounds = dict()
        self._ambiant_sounds = dict()
        self.gameEngine = gameEngine

        self._ambiant_volume = 1.0
        self._ambiant_loop = None
        self._bips = None
        self._ambiant_tasks = []

        self._protected_sounds = read_file_as_list(self.gameEngine.params("non_overlapping_sounds"))
        self._queue = []
        self._is_playing = False
        self._last_played = None

        self.load_sounds()

    def _start_next(self, t=None):
        self._is_playing = False
        if len(self._queue) > 0:
            last = self._queue.pop(0)
            self._is_playing = True
            last.play()

            self.gameEngine.taskMgr.doMethodLater(last.length() + 0.2, self._start_next, name="music_overlap")

    def load_sounds(self):
        folder = self.gameEngine.params("sound_folder")
        for file in listdir(folder):
            if file.endswith((".mp3", ".wav")):
                self._sounds[file.replace(".wav", "").replace(".mp3", "")] = self.gameEngine.loader.loadSfx(
                    folder + file)

        ambiant_folder = self.gameEngine.params("ambiant_sound_folder")
        for file in listdir(ambiant_folder):
            if file.endswith((".mp3", ".wav")):
                self._ambiant_sounds[file.replace(".wav", "").replace(".mp3", "")] = self.gameEngine.loader.loadSfx(
                    ambiant_folder + file)

        if self.gameEngine.params("ambiant_loop_file").replace(".wav", "").replace(".mp3", "") in self._ambiant_sounds:
            self._ambiant_loop = self._ambiant_sounds.pop(
                self.gameEngine.params("ambiant_loop_file").replace(".wav", "").replace(".mp3", ""))
        if "bips" in self._ambiant_sounds:
            self._bips = self._ambiant_sounds.pop("bips")

    def reset(self, n=5, t_max=900):
        for id in range(len(self._ambiant_tasks)):
            self.gameEngine.taskMgr.remove(self._ambiant_tasks.pop())

        # stop current playing sounds
        for sound in self._sounds:
            self.stop(sound)

        self._queue = []
        self._is_playing = False

        # random times
        for name in self._ambiant_sounds:
            t = t_max * num.random.rand(n)
            for i in t:
                self._ambiant_tasks.append(self.gameEngine.taskMgr.doMethodLater(i,
                                                                                 self._play_ambiant,
                                                                                 name="ambiant",
                                                                                 extraArgs=[name]))

    def set_ambiant_volume(self, volume):
        self._ambiant_volume = volume
        if self._ambiant_loop is not None and self._ambiant_loop.status() == self._ambiant_loop.PLAYING:
            self._ambiant_loop.setVolume(self._ambiant_volume)
        if self._bips is not None:
            self._bips.setVolume(0.5 * self._ambiant_volume)

    def _play_ambiant(self, name):
        if name in self._ambiant_sounds:
            self._ambiant_sounds[name].setVolume(0.1 * self.gameEngine.params("ambiant_sound_volume"))
            self._ambiant_sounds[name].play()

    def play_ambiant_sound(self):
        if self._ambiant_loop is not None:
            self._ambiant_loop.setLoop(True)
            self._ambiant_loop.setVolume(self.gameEngine.params("ambiant_sound_volume"))
            self._ambiant_loop.play()
        self.play_bips()

    def play_bips(self):
        if self._bips is not None:
            self._bips.setLoop(True)
            self._bips.setVolume(0.5)
            self._bips.play()

    def stop_bips(self):
        if self._bips is not None:
            self._bips.stop()

    def stop_ambiant_sound(self):
        if self._ambiant_loop is not None and self._ambiant_loop.status() == self._ambiant_loop.PLAYING:
            self._ambiant_loop.stop()

    def get_sound_length(self, name):
        if name in self._sounds:
            return self._sounds[name].length()
        else:
            return 0.0

    def play(self, name, loop=False, volume=None):
        if name in self._sounds:
            sound = self._sounds[name]

            # avoid playing the same sound many times
            if name == self._last_played and sound.status() == sound.PLAYING:
                return

            if loop:
                sound.setLoop(True)
            if volume is not None:
                sound.setVolume(volume)
            if name in self._protected_sounds or (
                    self.gameEngine.params("voice_sound_do_not_overlap") and ("voice" in name or "human" in name)):
                self._queue.append(sound)
                self._last_played = name
                if not self._is_playing:
                    self._start_next()
            else:
                self._last_played = name
                sound.play()
        elif name == "bips":
            self.play_bips()
        else:
            Logger.warning("Sound", name, "does not exists.")

    def stop(self, name):
        if name in self._sounds:
            sound = self._sounds[name]
            if sound.status() == sound.PLAYING:
                sound.stop()
