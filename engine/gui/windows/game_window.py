import os
from typing import Optional

import numpy as np
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence, Parallel
from direct.task.Task import Task
from direct.task.TaskManagerGlobal import taskMgr
from panda3d.core import TransparencyAttrib, KeyboardButton, Vec3, TextNode

from engine.gui.windows.window import Window
from engine.utils.event_handler import event
from engine.utils.logger import Logger


class Rock:
    def __init__(self, speed, sprite, radius, w):
        self._speed = Vec3(np.random.random() - 0.5, 0, -np.random.random()).normalized() * speed
        self._pos = Vec3(1.5 * (np.random.rand() - 0.5), 0, 1 + 0.2 * np.random.random())
        self._sprite = sprite
        self._w = w
        self._sprite.hide()
        self._radius_square = radius ** 2

    def remove_node(self):
        self._sprite.remove_node()

    def collides(self, other_pos, other_radius):
        return (self._pos.x - other_pos.x) ** 2 + (self._pos.z - other_pos.z) ** 2 <= self._radius_square + \
            other_radius ** 2

    def update(self):
        if self._pos.z < 1:
            self._sprite.show()
        new_rock_pos = self._pos + self._speed
        if abs(new_rock_pos.x) > 1 or new_rock_pos.z < -1:
            # remove rock
            self._sprite.remove_node()
            return False
        else:
            self._sprite.set_pos(new_rock_pos)
            self._sprite.set_r(self._sprite.get_r() + self._w)
            self._pos = new_rock_pos
            return True


class Star(Rock):
    def __init__(self, speed, sprite, radius, w):
        super().__init__(speed, sprite, radius, w)
        self._speed = Vec3(0, 0, -1) * speed


class GameWindow(Window):
    """
    Emulating a simple2d game
    """
    def __init__(self,
                 gui_engine,
                 goal,
                 **kwargs):
        super().__init__(gui_engine, size_x=2.0, size_y=1.8,
                         title=gui_engine.process_text('$la_game_title$'), text=None, **kwargs)

        self._game_background = self._get_sprite('game_background', parent=self._widget, scale=0.7, pos=(0, 0, -0.1))

        self._ship_speed = 0.03

        self._star_speed = 0.005
        self._star_radius = 0.05
        self._star_spawn_time = 1.0

        self._rock_speed = 0.01
        self._rock_rotation_max = 2
        # min, max
        self._rock_radius = [0.05, 0.1]
        self._rock_spawn_time = 0.4
        # goal
        self._max_stars = goal

        self._pad = (0.9, 0.9)
        self._ship = self._get_sprite('player_ship', parent=self._game_background, scale=0.1)

        self._is_down = self._gui_engine.engine.mouseWatcherNode.is_button_down
        self._buttons = {
            KeyboardButton.right(): Vec3(1, 0, 0),
            KeyboardButton.left(): Vec3(-1, 0, 0),
            KeyboardButton.up(): Vec3(0, 0, 1),
            KeyboardButton.down(): Vec3(0, 0, -1),
        }

        self._rocks = []
        self._stars = []
        self._status = 0
        self._task: Optional[Task] = None
        self._interval = None
        self._score = 0
        self._score_txt = OnscreenText(parent=self._game_background, scale=0.1, pos=(0, 1.1), fg=[1] * 4,
                                       align=TextNode.ALeft)
        self._last_rock_spawn_time = 0
        self._last_star_spawn_time = 0
        self._finished = False
        self.play_game()

    @event('current_step_end')
    def on_step_end(self) -> None:
        self._gui_engine.engine.sound_manager.stop('star_game_music')
        self._gui_engine.engine.sound_manager.resume_music()
        self._gui_engine.close_window_and_go()

    def play_game(self, *_):
        text = OnscreenText(parent=self._game_background, scale=0.15, pos=(0, 0.5),
                            fg=(1.0, 1.0, 1.0, 1.0),
                            text='')
        text.setTransparency(1)
        # play music
        self._gui_engine.engine.sound_manager.stop_music()
        self._gui_engine.engine.sound_manager.play_sfx('star_game_music', loop=True)

        if self._status == 0:
            def start():
                if not self._finished:
                    # reset task
                    if self._task is not None and self._task.is_alive():
                        self._task.remove()
                    self._task = taskMgr.add(self._run_game, uponDeath=self.play_game)
                    self._game_background.accept('a', self._spawn_rock)

            # start game

            # remove rocks
            for rock in self._rocks:
                rock.remove_node()
            self._rocks.clear()
            # remove stars
            for star in self._stars:
                star.remove_node()
            self._stars.clear()

            # reset counters
            self._last_rock_spawn_time = 0
            self._last_star_spawn_time = 0
            self._score = 0
            self._score_txt.setText(f"score : 0 / {self._max_stars}")

            # reset ship
            self._ship.set_pos(Vec3(0))

            # start sequence
            self._interval = Sequence(
                Func(text.setText, text='3'),
                Wait(1),
                Func(text.setText, text='2'),
                Wait(1),
                Func(text.setText, text='1'),
                Wait(1),
                Func(text.setText, text='Go !'),
                Wait(0.5),
                Func(text.remove_node),
                Func(start),
            )
            self._interval.start()

        elif self._status == 1:
            # win
            # stop music
            self._gui_engine.engine.sound_manager.stop('star_game_music')
            self._gui_engine.engine.sound_manager.resume_music()

            text.setText(self._gui_engine.process_text('$la_game_win$'))

            def done():
                if not self._finished:
                    self._gui_engine.close_window_and_go()

            self._interval = Sequence(
                Parallel(
                    text.colorScaleInterval(3, (1, 1, 1, 1), (1, 1, 1, 0)),
                    text.scaleInterval(3, 1, 0),
                         ),
                Wait(1),
                Func(text.remove_node),
                Func(done)
            )
            self._interval.start()
        else:
            pass

    def _run_game(self, task):
        dv = Vec3(0)
        for btn, vec in self._buttons.items():
            if self._is_down(btn):
                dv += vec

        dv = dv.normalized() * self._ship_speed
        new_pos = self._ship.get_pos() + dv
        # clamping position
        new_pos.x = min(self._pad[0], max(-self._pad[0], new_pos.x))
        new_pos.z = min(self._pad[1], max(-self._pad[1], new_pos.z))
        self._ship.set_pos(new_pos)

        # move rocks
        for rock in self._rocks.copy():
            if not rock.update():
                self._rocks.remove(rock)
                # # spawn another one
                # self._spawn_rock()
            elif rock.collides(new_pos, 0.1):
                # lost sound
                self._gui_engine.engine.sound_manager.play_sfx('star_game_loose', avoid_playing_twice=False)
                # lost, status on 0
                self._status = 0
                return task.done

        # move stars
        for star in self._stars.copy():
            if not star.update():
                self._stars.remove(star)
                # # spawn another one
                # self._spawn_rock()
            elif star.collides(new_pos, 0.1):
                # play sound
                self._gui_engine.engine.sound_manager.play_sfx('collect_star', avoid_playing_twice=False)
                # remove star and add to score
                self._score += 1
                self._stars.remove(star)
                star.remove_node()
                self._score_txt.setText(f"score : {self._score} / {self._max_stars}")

        # spawn rocks
        if task.time - self._last_rock_spawn_time > self._rock_spawn_time:
            self._spawn_rock()
            self._last_rock_spawn_time = task.time

        # spawn stars
        if task.time - self._last_star_spawn_time > self._star_spawn_time:
            self._spawn_star()
            self._last_star_spawn_time = task.time

        # check for win
        if self._score >= self._max_stars:
            # play music
            self._gui_engine.engine.sound_manager.play_sfx('star_game_win')
            self._status = 1
            return task.done
        return task.cont

    def _spawn_rock(self):
        radius = self._rock_radius[0] + (self._rock_radius[1] - self._rock_radius[0]) * np.random.random()
        self._rocks.append(
            Rock(
                sprite=self._get_sprite('rock' + np.random.choice(['1', '2', '3', '4', '5']),
                                        parent=self._game_background,
                                        scale=radius),
                speed=self._rock_speed,
                radius=radius,
                w=self._rock_rotation_max*(2*np.random.random()-1)
            )
        )

    def _spawn_star(self):
        self._stars.append(
            Star(
                sprite=self._get_sprite('game_star',
                                        parent=self._game_background,
                                        scale=self._star_radius),
                speed=self._star_speed,
                radius=self._star_radius,
                w=self._rock_rotation_max*(2*np.random.random()-1)
            )
        )

    def _get_sprite(self, name, **kwargs):
        sprite = OnscreenImage(
            image=os.path.join(self._gui_engine.engine('image_path'), name.replace('.png', '') + '.png'),
            **kwargs
        )
        sprite.setTransparency(TransparencyAttrib.MAlpha)
        return sprite

    def destroy(self):
        self._status = 2
        self._finished = True
        if self._task is not None: # and self._task.is_alive():
            self._task.cancel()
            self._task.remove()
        if self._interval is not None:
            self._interval.finish()

        for rock in self._rocks:
            rock.remove_node()
        self._rocks.clear()
        # remove stars
        for star in self._stars:
            star.remove_node()
        self._stars.clear()
        super().destroy()
