import re
from os import listdir
import numpy as np
from direct.showbase.DirectObject import DirectObject

from engine.utils.logger import Logger
from engine.utils.ini_parser import read_file_as_list


class SoundManager(DirectObject):
    """
    Sound management class
    """
    def __init__(self, engine, load=True):
        super().__init__()
        self._sounds = dict()
        self._ambient_sounds = dict()
        self._music = dict()
        self._engine = engine
        # only wav files supported
        self._supported_sound_format = ('wav', )

        self._ambient_volume = 1.0
        self._ambient_loop = None
        self._bips = None
        self._ambient_tasks = []
        self._last_sfx_played = None
        self._last_music_played = None

        # list of sounds that should not be stopped or overridden
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

    @staticmethod
    def _get_file_name(name: str) -> str:
        """
        Remove sound extension
        """
        return name.split('.')[0]

    def load_sounds(self):
        """
        Load all sounds
        """
        Logger.info('loading sfx')
        folder = self._engine("sfx_sound_folder")
        files = listdir(folder)
        np.random.shuffle(files)
        for file in files:
            key = self._get_file_name(file)
            if file.endswith(self._supported_sound_format) and 'old' not in file:
                self._sounds[key] = self._engine.loader.loadSfx(folder + file)

        Logger.info('loading ambient musics')
        ambient_folder = self._engine("ambient_sound_folder")
        for file in listdir(ambient_folder):
            key = self._get_file_name(file)
            if file.endswith(self._supported_sound_format):
                Logger.info(f'loading ambient sound : {key}')
                self._ambient_sounds[key] = self._engine.loader.loadSfx(ambient_folder + file)

        # getting the loop ambient sound
        ambient_loop_file = self._get_file_name(self._engine("ambient_loop_file"))
        if ambient_loop_file in self._ambient_sounds:
            self._ambient_loop = self._ambient_sounds.pop(ambient_loop_file)
        else:
            Logger.warning('no ambient loop file !')
        # idem for bips
        if "bips" in self._ambient_sounds:
            self._bips = self._ambient_sounds.pop("bips")
        else:
            Logger.warning('no bips file !')

        Logger.info('loading music files')
        music_folder = self._engine("music_sound_folder")
        for file in listdir(music_folder):
            key = self._get_file_name(file)
            if file.endswith(self._supported_sound_format):
                Logger.info(f'loading music sound : {key}')
                self._music[key] = self._engine.loader.loadMusic(music_folder + file)

    def reset(self, n=5, t_max=900):
        for _ in range(len(self._ambient_tasks)):
            self._engine.taskMgr.remove(self._ambient_tasks.pop())

        # stop current playing sounds
        for sound in self._sounds:
            self.stop(sound)

        # stop music
        self.stop_music()

        # ignore all events
        self.ignore_all()

        self._queue = []
        self._is_playing = False

        # random times
        # for ambient sounds
        for name in self._ambient_sounds:
            t = t_max * np.random.rand(n)
            for i in t:
                self._ambient_tasks.append(self._engine.taskMgr.doMethodLater(
                    i,
                    self._play_ambient,
                    name="ambient",
                    extraArgs=[name])
                )

    def set_ambient_volume(self, volume):
        self._ambient_volume = volume
        if self._ambient_loop is not None and self._ambient_loop.status() == self._ambient_loop.PLAYING:
            self._ambient_loop.setVolume(self._ambient_volume)
        if self._bips is not None:
            self._bips.setVolume(0.5 * self._ambient_volume)

    def _play_ambient(self, name):
        if name in self._ambient_sounds:
            self._ambient_sounds[name].setVolume(self._engine("volume_ambient"))
            self._ambient_sounds[name].play()

    def play_ambient_sound(self):
        if self._ambient_loop is not None:
            self._ambient_loop.setLoop(True)
            self._ambient_loop.setVolume(self._engine("volume_ambient"))
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

    @property
    def is_music_playing(self) -> bool:
        """
        Check if a music is currently playing

        Returns:
            bool: Is a music playing
        """
        music = self._music.get(self._last_music_played, None)
        return music is not None and music.status() == music.PLAYING

    def stop_music(self) -> None:
        """
        Stops current music if it exists
        """
        if self.is_music_playing:
            self._music[self._last_music_played].stop()

    def resume_music(self, loop: bool = True) -> None:
        """
        Restarts previously played music if it exists

        Args:
            loop (bool, optional): Plays music in loop. Default to ``True``
        """
        if self._last_music_played is not None:
            self.play_music(self._last_music_played, loop=loop)

    def play_music(self, name: str, loop: bool = True) -> None:
        """
        Starts a music

        Args:
            name (str): music name
            loop (bool, optional): Plays music in loop. Default to True

        """
        # remember the name if overriden
        # below
        raw_name = name
        if name not in self._music:
            # if name is not in self._music
            # we check if there is a music matching
            # "name_<x>" where "<x>" is a digit.
            # If it is the case, we pick one random item
            # in the list.
            regex = re.compile(f"{name}_[0-9]+")
            matches = [k for k in self._music if re.match(regex, k)]
            if len(matches) > 0:
                # pick a random one
                name = np.random.choice(matches)
                Logger.info(f'picking a random music "{name}" from name "{raw_name}"')

        if name in self._music:
            music = self._music[name]

            # if another music is played, stop it except if it is the same
            if self.is_music_playing:
                if self._last_music_played != name:
                    self._music[self._last_music_played].stop()
                else:
                    return

            if loop:
                # instead of calling `set_loop(True)`
                # we send an event when music is done
                # and listen for this event once.
                # Event name is the raw_name of the music
                # played, so that if there are several
                # files matching this name, a new one
                # can be played, instead of repeating the
                # same file again and again
                music.set_finished_event(raw_name)
                self.accept_once(raw_name, lambda *args: self.play_music(raw_name, loop=True))
            music.set_volume(self._engine('volume_music'))

            self._last_music_played = name
            Logger.info(f'playing new music "{name}"')
            music.play()
        else:
            Logger.error(f'no music named "{name}"')

    def play_sfx(self, name, loop=False, volume=None, avoid_playing_twice=True):
        if name in self._sounds:
            # get sound file
            sound = self._sounds[name]

            # avoid playing the same sound many times
            # except if avoid_playing_twice is False
            if avoid_playing_twice and \
                    ((len(self._queue) > 0 and name == self._queue[-1].get_name())
                     or sound.status() == sound.PLAYING):
                return

            if loop:
                # set loop
                sound.setLoop(True)

            # set volume
            is_voice = 'voice' in name or 'human' in name
            volume = volume if volume is not None \
                else self._engine('volume_voice') if is_voice \
                else self._engine('volume_sfx')
            sound.setVolume(volume)

            if name in self._protected_sounds or (self._engine("voice_sound_do_not_overlap") and
                                                  ("voice" in name or "human" in name)):
                # if playing sound is protected or either "voice" or "human" is in file name, we queue it
                self._queue.append(sound)
                self._last_sfx_played = name
                if not self._is_playing:
                    # no sound is playing right now, get next sound in queue
                    self._start_next()
            else:
                # not protected, just set it
                self._last_sfx_played = name
                sound.play()
        elif name == "bips":
            # it bips, just play it
            self.play_bips()
        # else:
        #     Logger.warning('sound {} does not exists'.format(name))

    def stop(self, name: str) -> None:
        """
        Stop a played sound

        Args:
            name (str): Sound name to stop
        """
        if name in self._sounds:
            sound = self._sounds[name]
            if sound.status() == sound.PLAYING:
                sound.stop()

    def __getitem__(self, item):
        """
        Get a sound file
        """
        return self._sounds.get(item, None)
