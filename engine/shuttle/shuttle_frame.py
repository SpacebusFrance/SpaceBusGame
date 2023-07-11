import numpy as num
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
        # HardwareHandler.__init__(self, _engine)

        self._engine = engine

        self.frame = NodePath("shuttle_frame")
        self.frame.reparentTo(self._engine.render)

        # u follows the line of sight
        self._u = LVector3f(-1.0, 0.0, 0.0)
        # n is orthogonal to the camera
        self._n = LVector3f(0.0, 0.0, 0.0)

        self.reset()

        self.mwn = engine.mouseWatcherNode
        self.main_task = self._engine.taskMgr.add(self.cam_move_task, 'cam_move_task')

        # dynamics

        self.boost_time = 0.2
        self.update_freq = 60
        self.dt = 1 / self.update_freq
        self._last_update = 0
        self._is_boost = False
        self.a = self._engine.get_option("shuttle_velocity") * self.dt / self.boost_time
        self.a_spin = self._engine.get_option("shuttle_spin_velocity") * self.dt / self.boost_time

        self.velocity_mean = self._engine.get_option("shuttle_velocity")

        self.velocity = LVector3f(0, 0, 0)
        self.acceleration = LVector3f(0, 0, 0)
        self.spinning_velocity = LVector3f(0, 0, 0)
        self.spinning_acceleration = LVector3f(0, 0, 0)
        self._mvt_tasks = None

    def main_window_focus(self):
        wp = WindowProperties()
        wp.setForeground(True)
        self._engine.win.requestProperties(wp)

    def reset(self):
        self._engine.space_craft.connect_to_shuttle(self.frame)
        self.velocity = LVector3f(0, 0, 0)
        self.acceleration = LVector3f(0, 0, 0)
        self.spinning_velocity = LVector3f(0, 0, 0)
        self.spinning_acceleration = LVector3f(0, 0, 0)
        self.frame.set_hpr(self.frame.get_hpr())
        self.compute_unit_vectors()

    def impact(self, t=None):
        def shake_task(task):
            if task.time > 5:
                return task.done
            else:
                self.frame.set_p(self.frame.get_p() - TO_DEG * num.sin(task.time * 15)/(1 + 5*task.time)**2*0.1)
                self.frame.set_h(self.frame.get_h() + TO_DEG * num.sin(task.time * 10)/(1 + 5*task.time)**2*0.05)
                return task.cont

        self.stop(play_sound=False)
        task = Task(shake_task)
        self._engine.taskMgr.add(task, "shaking", extraArgs=[task])
        self._engine.sound_manager.play_sfx("impact", volume=1.5)

    def align_along(self, axis):
        d = {'x': LVector3f(1, 0, 0),
             "-x": LVector3f(-1, 0, 0),
             "y": LVector3f(0, 1, 0),
             "-y": LVector3f(0, -1, 0),
             "z": LVector3f(0, 0, 1),
             "-z": LVector3f(0, 0, -1),
             }
        if axis in d:
            self.stop()
            self.look_at(self.frame.get_pos() + d[axis])

    def dynamic_goto_hpr(self, hpr, time=5, update_is_moving=True, end_func=None):
        self.stop()

        if update_is_moving:
            self._engine.state_manager.is_moving.set_value(True)
        self._mvt_tasks = self.frame.hprInterval(time, hpr, self.frame.get_hpr(), blendType='easeInOut')

        self._mvt_tasks.start()

        def end(_):
            self.stop(play_sound=False)
            if update_is_moving:
                self._engine.state_manager.is_moving.set_value(False)
            if hasattr(end_func, '__call__'):
                end_func.__call__()

        self._boost_sound(max(0.1, time - 1.5))
        self._engine.taskMgr.doMethodLater(time, end, name="stabilization_end")

    def fake_movement(self):
        self.stop(play_sound=False)

    def dynamic_look_at(self, target=None, time=5, update_is_moving=True, end_func=NodePath):
        self.stop()
        v = LVector3f(target if target is not None else (0, 0, 0))

        if update_is_moving:
            self._engine.state_manager.is_moving.set_value(True)
            # self._engine.state_manager.is_moving.set_value(True)

        self._mvt_tasks = self.frame.hprInterval(time, get_hpr(v - self.frame.get_pos()), self.frame.get_hpr(),
                                                 blendType='easeInOut')

        self._mvt_tasks.start()

        def end(_):
            self.stop(play_sound=False)
            if update_is_moving:
                self._engine.state_manager.is_moving.set_value(False)
            if hasattr(end_func, '__call__'):
                end_func.__call__()

        self._boost_sound(max(0.1, time - 1.5))
        self._engine.taskMgr.doMethodLater(time, end, name="stabilization_end")

    def show_shuttle(self):
        model = self._engine.loader.load_model("data/models/shuttle.egg")
        model.set_bin("fixed", 10)
        model.reparentTo(self.frame)

    def dynamic_goto(self, target, power=1, t_spin=5.0, end_func=None):
        self._engine.state_manager.is_moving.set_value(True)
        self.stop()

        v = LVector3f(target if target is not None else (0, 0, 0))

        self._mvt_tasks = self.frame.hprInterval(t_spin, get_hpr(v - self.frame.get_pos()), self.frame.get_hpr(),
                                                 blendType='easeInOut')
        self._boost_sound(max(0.1, t_spin - 1.5))

        move_time = get_distance(self.frame.get_pos(), target) / (power * self.velocity_mean)

        # d = {'time': move_time,
        #      'pos': self.frame.get_pos(),
        #      'target': target,
        #      'power': power,
        #      'mean v': self.velocity_mean}
        # Logger.info('new_move : \n\t- {}'.format('\n\t-'.join(['{0} : {1}'.format(k, d[k]) for k in d])))

        def start(_):
            self._mvt_tasks = None
            self.compute_unit_vectors()
            self.boost("f", power)

        def end(_):
            self.stop(play_sound=False)
            self._engine.state_manager.is_moving.set_value(False)
            if hasattr(end_func, '__call__'):
                end_func.__call__()

        self._mvt_tasks.start()
        self._engine.taskMgr.doMethodLater(t_spin, start, name="goto_start")
        self._boost_sound(t_spin + move_time - 1.5)
        self._engine.taskMgr.doMethodLater(t_spin + move_time, end, name="goto_end")

    def _boost_sound(self, t=0.0):
        if t > 0.0:
            self._engine.taskMgr.doMethodLater(t, self._engine.sound_manager.play_sfx, name="boost_sound", extraArgs=["boost_new"])
        else:
            self._engine.sound_manager.play_sfx("boost_new")

    def boost(self, direction, power=1, play_sound=True):
        if not self._is_boost:
            self.compute_unit_vectors()

            if direction == 'f':
                self.acceleration += self._u * self.a * power
            elif direction == 'b':
                self.acceleration -= self._u * self.a * power
            elif direction == 'r':
                self.acceleration += self._n * self.a * power
            elif direction == 'l':
                self.acceleration -= self._n * self.a * power
            elif direction == 'tp':
                self.spinning_acceleration[0] += self.a_spin * power
            elif direction == 'tm':
                self.spinning_acceleration[0] -= self.a_spin * power
            elif direction == 'pp':
                self.spinning_acceleration[1] += self.a_spin * power
            elif direction == 'pm':
                self.spinning_acceleration[1] -= self.a_spin * power
            elif direction == 'dp':
                self.spinning_acceleration[2] += self.a_spin * power
            elif direction == 'dm':
                self.spinning_acceleration[2] -= self.a_spin * power
            else:
                return

            self._is_boost = True
            self._engine.taskMgr.doMethodLater(self.boost_time, self._reset_acc, name="end_boost_" + direction)
            if play_sound:
                self._boost_sound()

    def _reset_acc(self, t=None):
        self._is_boost = False
        self.acceleration = LVector3f(0., 0., 0.)
        self.spinning_acceleration = LVector3f(0., 0., 0.)

    def set_pos(self, pos):
        self.frame.set_pos(pos)

    def look_at(self, target):
        self.frame.set_hpr(get_hpr(LVector3f(target if target is not None else (0, 0, 0)) - self.frame.get_pos()))
        self.compute_unit_vectors()

    def stop(self, play_sound=True):
        if self._mvt_tasks is not None:
            # eventually stops the ongoing tasks
            self._mvt_tasks.finish()
            self._mvt_tasks = None
        # remove goto tasks
        self._engine.taskMgr.remove("goto_start")
        self._engine.taskMgr.remove("goto_end")
        self.velocity = LVector3f(0, 0, 0)
        self.spinning_velocity = LVector3f(0, 0, 0)
        self.compute_unit_vectors()
        # set is_moving to False
        self._engine.state_manager.is_moving.set_value(False)
        if play_sound:
            self._boost_sound()

    def compute_unit_vectors(self):
        h = TO_RAD * self.frame.get_h()
        p = TO_RAD * self.frame.get_p()
        r = TO_RAD * self.frame.get_r()
        self._u = LVector3f(- num.sin(h) * num.cos(p),
                            num.cos(h) * num.cos(p),
                            num.sin(p))
        self._n = LVector3f(num.cos(h) * num.cos(r),
                            num.sin(h) * num.cos(r),
                            - num.sin(r))

    def cam_move_task(self, task):
        """
        The main task.
        """
        # this limits the udpate to 60 fps.
        if task.time - self._last_update > self.dt:
            # print("update !")
            self._last_update = task.time
            if self._is_boost:
                self.velocity += self.acceleration
                self.spinning_velocity += self.spinning_acceleration

            self.frame.set_pos(self.frame.get_pos() + self.velocity * self.dt)
            if self.spinning_velocity[0] != 0.0 or self.spinning_velocity[1] != 0.0 or self.spinning_velocity[2] != 0.0:
                self.frame.set_r(self.frame.get_r() + self.spinning_velocity[2] * self.dt)
                self.frame.set_p(self.frame.get_p() + self.spinning_velocity[0] * self.dt)
                self.frame.set_h(self.frame.get_h() + self.spinning_velocity[1] * self.dt)
                # self.compute_unit_vectors()

        return task.cont
