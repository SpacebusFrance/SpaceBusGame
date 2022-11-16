from panda3d.core import Quat, look_at
import numpy as np


def get_hpr(vector):
    quaternion = Quat()
    look_at(quaternion, vector, (0, 0, 1))
    return quaternion.get_hpr()


def get_distance(pos1, pos2):
    return np.sqrt((pos2[0] - pos1[0]) ** 2 +
                   (pos2[1] - pos1[1]) ** 2 +
                   (pos2[2] - pos1[2]) ** 2)