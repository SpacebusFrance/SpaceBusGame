from os import listdir
import numpy as num

from engine.utils.logger import Logger
from engine.utils.ini_parser import read_file_as_list


class SoundManager:
    """
    The class managing sounds
    """
    def __init__(self, engine, load=True):
        self._sounds = dict()
        self._ambient_sounds = dict()
        self._engine = engine

        self._ambient_volume = 1.0
        self._ambient_loop = None
        self._bips = None
        self._ambient_tasks = []
        self._last_played = None

        self._protected_sounds = read_file_as_list(self._engine("non_overlapping_sounds"))
        self._queue = []
        self._is_playing = False
        if load:
            self.load_sounds()

    def _start_next(self, t=None):
        """
        Start the next sound in chain
        """
        self._is_playing = False
        if len(self._queue) > 0:
            last = self._queue.pop(0)
            self._is_playing = True
            last.play()

            self._engine.taskMgr.doMethodLater(last.length() + 0.2, self._start_next, name="music_overlap")

    def load_sounds(self):
        """
        Load all sounds
        """
        folder = self._engine("sound_folder")
        for file in listdir(folder):
            if file.endswith((".mp3", ".wav")) and 'old' not in file:
                Logger.info('loading sound : {}'.format(file.replace(".wav", "").replace(".mp3", "")))
                self._sounds[file.replace(".wav", "").replace(".mp3", "")] = self._engine.loader.loadSfx(folder + file)

        ambient_folder = self._engine("ambient_sound_folder")
        for file in listdir(ambient_folder):
            if file.endswith((".mp3", ".wav")):
                Logger.info('loading ambient sound : {}'.format(file.replace(".wav", "").replace(".mp3", "")))
                self._ambient_sounds[file.replace(".wav", "").replace(".mp3", "")] = self._engine.loader.loadSfx(ambient_folder + file)

        if self._engine("ambient_loop_file").replace(".wav", "").replace(".mp3", "") in self._ambient_sounds:
            self._ambient_loop = self._ambient_sounds.pop(self._engine("ambient_loop_file").replace(".wav", "").replace(".mp3", ""))
        if "bips" in self._ambient_sounds:
            self._bips = self._ambient_sounds.pop("bips")

    def reset(self, n=5, t_max=900):
        for id in range(len(self._ambient_tasks)):
            self._engine.taskMgr.remove(self._ambient_tasks.pop())

        # stop current playing sounds
        for sound in self._sounds:
            self.stop(sound)

        self._queue = []
        self._is_playing = False

        # random times
        for name in self._ambient_sounds:
            t = t_max * num.random.rand(n)
            for i in t:
                self._ambient_tasks.append(self._engine.taskMgr.doMethodLater(i,
                                                                              self._play_ambient,
                                                                              name="ambient",
                                                                              extraArgs=[name]))

    def set_ambient_volume(self, volume):
        self._ambient_volume = volume
        if self._ambient_loop is not None and self._ambient_loop.status() == self._ambient_loop.PLAYING:
            self._ambient_loop.setVolume(self._ambient_volume)
        if self._bips is not None:
            self._bips.setVolume(0.5 * self._ambient_volume)

    def _play_ambient(self, name):
        if name in self._ambient_sounds:
            self._ambient_sounds[name].setVolume(0.1 * self._engine("ambient_sound_volume"))
            self._ambient_sounds[name].play()

    def play_ambient_sound(self):
        if self._ambient_loop is not None:
            self._ambient_loop.setLoop(True)
            self._ambient_loop.setVolume(self._engine("ambient_sound_volume"))
            self._ambient_loop.play()
        self.play_bips()

    def play_bips(self):
        if self._bips is not None:
            self._bips.setLoop(True)
            self._bips.setVolume(0.5)
            self._bips.play()

    def stop_bips(self):
        if self._bips is not None:
            self._bips.stop()

    def stop_ambient_sound(self):
        if self._ambient_loop is not None and self._ambient_loop.status() == self._ambient_loop.PLAYING:
            self._ambient_loop.stop()

    def get_sound_length(self, name):
        if name in self._sounds:
            return self._sounds[name].length()
        else:
            return 0.0

    def play(self, name, loop=False, volume=None):
        if name in self._sounds:
            sound = self._sounds[name]

            # avoid playing the same sound many times
            if (len(self._queue) > 0 and name == self._queue[-1].get_name()) or sound.status() == sound.PLAYING:
                return

            if loop:
                sound.setLoop(True)
            if volume is not None:
                sound.setVolume(volume)
            if name in self._protected_sounds or (self._engine("voice_sound_do_not_overlap") and
                                                  ("voice" in name or "human" in name)):
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
            Logger.warning('sound {} does not exists'.format(name))

    def stop(self, name):
        if name in self._sounds:
            sound = self._sounds[name]
            if sound.status() == sound.PLAYING:
                sound.stop()
