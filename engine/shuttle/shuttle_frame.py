import logging

import numpy as num
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.LerpInterval import LerpHprInterval, LerpPosInterval
from direct.interval.MetaInterval import Sequence
from direct.showbase import DirectObject
from direct.task.Task import Task
from panda3d.core import LVector3f, NodePath, WindowProperties

from engine.utils.logger import Logger
from engine.utils.geometric_utils import get_hpr, get_distance

TO_RAD = 0.017453293
TO_DEG = 57.295779513


class ShuttleFrame(DirectObject.DirectObject):
    """
    The frame linked to the shuttle (where the players are).

    """
    def __init__(self, engine):
        DirectObject.DirectObject.__init__(self)

        self._engine = engine

        self.frame = NodePath("shuttle_frame")
        self.frame.reparentTo(self._engine.render)

        self.sequence = Sequence()
        self.reset()

        self.velocity_mean = self._engine.get_option("shuttle_velocity")

    def main_window_focus(self):
        wp = WindowProperties()
        wp.setForeground(True)
        self._engine.win.requestProperties(wp)

    def reset(self):
        if self.sequence is not None and self.sequence.is_playing():
            self.sequence.finish()
            self.sequence = None

        self._engine.space_craft.connect_to_shuttle(self.frame)

    def impact(self, t=None):
        def shake_task(task):
            if task.time > 5:
                return task.done
            else:
                self.frame.set_p(self.frame.get_p() - TO_DEG * num.sin(task.time * 15)/(1 + 5*task.time)**2*0.1)
                self.frame.set_h(self.frame.get_h() + TO_DEG * num.sin(task.time * 10)/(1 + 5*task.time)**2*0.05)
                return task.cont

        # self.stop(play_sound=False)
        task = Task(shake_task)
        self._engine.taskMgr.add(task, "shaking", extraArgs=[task])
        self._engine.sound_manager.play_sfx("impact", volume=1.5)

    def show_shuttle(self):
        model = self._engine.loader.load_model("data/models/shuttle.egg")
        model.set_bin("fixed", 10)
        model.reparentTo(self.frame)

    def dynamic_look_at(self, target=None, time=5):

        target = LVector3f(target if target is not None else (0, 0, 0))

        self.sequence = Sequence(
            Func(self.start_move),
            LerpHprInterval(
                nodePath=self.frame,
                duration=time,
                hpr=get_hpr(target - self.frame.get_pos()),
                blendType='easeInOut'
            ),
            Func(self.end_move),
        )
        self.sequence.start()

    def dynamic_goto(self, target, power=1, t_spin=5.0):
        target = LVector3f(target if target is not None else (0, 0, 0))

        duration = get_distance(self.frame.get_pos(), target) / (power * self.velocity_mean)

        self.sequence = Sequence(
            Func(self.start_move),
            LerpHprInterval(
                nodePath=self.frame,
                duration=t_spin,
                hpr=get_hpr(target - self.frame.get_pos()),
                blendType='easeInOut'
            ),
            Func(self._boost_sound),
            LerpPosInterval(
                nodePath=self.frame,
                duration=duration,
                pos=target,
                blendType='easeInOut'
            ),
            Func(self.end_move),
        )
        self.sequence.start()

    def _boost_sound(self, t=0.0):
        if t > 0.0:
            self._engine.taskMgr.doMethodLater(t, self._engine.sound_manager.play_sfx, name="boost_sound", extraArgs=["boost_new"])
        else:
            self._engine.sound_manager.play_sfx("boost_new")

    def set_pos(self, pos):
        self.frame.set_pos(pos)

    def look_at(self, target):
        self.frame.set_hpr(
            get_hpr(LVector3f(target if target is not None else (0, 0, 0)) - self.frame.get_pos())
        )

    def start_move(self):
        self._engine.state_manager.is_moving.set_value(True)
        self._boost_sound()

    def end_move(self):
        self._engine.state_manager.is_moving.set_value(False)
        self._boost_sound()
