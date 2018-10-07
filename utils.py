import os
import subprocess
import sys
from pathlib import Path

import numpy as num
from PIL import Image, ImageEnhance
from panda3d.core import Quat, look_at, TextureStage, TexGenAttrib


class Logger:
    @staticmethod
    def info(*args):
        print('[INFO]:', *args)

    @staticmethod
    def warning(*args):
        print('[WARNING]:', *args)

    @staticmethod
    def error(*args):
        print('[ERROR]:', *args)


def get_screen_resolutions():
    p = subprocess.Popen(['xrandr'], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '*'], stdin=p.stdout, stdout=subprocess.PIPE)
    p.stdout.close()

    a, _ = p2.communicate()
    a = a.decode("utf-8")
    res = []
    for line in a.splitlines():
        r = line.strip().split(" ")[0].strip()
        res.append((int(r.split("x")[0].strip()), int(r.split("x")[1].strip())))
    return res


def get_key_from_value(d, value):
    for k, v in d.items():
        if v == value:
            return k
    return None


def get_hpr(vector):
    quat = Quat()
    look_at(quat, vector, (0, 0, 1))
    return quat.get_hpr()


def safe_min(a, b):
    if a is None and b is None:
        return None
    elif a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a, b)


def get_distance(pos1, pos2):
    return num.sqrt((pos2[0] - pos1[0]) ** 2 +
                    (pos2[1] - pos1[1]) ** 2 +
                    (pos2[2] - pos1[2]) ** 2)


def create_sky_boxes(file, sky_box_name=None):
    if sky_box_name is None:
        sky_box_name = file.split("/")[-1].split(".")[0].strip()

    path = "data/Map/" + sky_box_name + "/" + sky_box_name
    image = Image.open(file)
    w, h = image.size
    t = int(w / 4)
    if t != int(h / 3):
        print("ERROR : file is not well sized !")
    else:
        print("creating new skybox", sky_box_name)
        if not os.path.exists("data/Map/" + sky_box_name + "/"):
            os.makedirs("data/Map/" + sky_box_name + "/")
        image.crop((2 * t, t, 3 * t, 2 * t)).save(path + "_0.png")
        image.crop((0, t, t, 2 * t)).save(path + "_1.png")
        image.crop((t, 2 * t, 2 * t, 3 * t)).save(path + "_2.png")
        image.crop((t, 0, 2 * t, t)).save(path + "_3.png")
        image.crop((t, t, 2 * t, 2 * t)).save(path + "_4.png")
        image.crop((3 * t, t, 4 * t, 2 * t)).save(path + "_5.png")
    image.close()


def smart_cast(s):
    if s == "True":
        return True
    elif s == "False":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def read_xml_args(line):
    r = dict()
    parts = line.split("=")
    for i, part in enumerate(parts[:-1]):
        r[part.split()[-1].strip()] = smart_cast(parts[i + 1].split('"')[1].strip())
    return r


def string_to_smart_list(s, cast=True):
    if ',' in s:
        l = list()
        parts = s.split(",")
        for e in parts:
            if len(e) > 0:
                if cast:
                    l.append(smart_cast(e.strip()))
                else:
                    l.append(e.strip())
        return l
    else:
        return smart_cast(s.strip())


def read_file_as_list(file_name, cast=True):
    try:
        file = open(file_name, "r")
        lines = file.readlines()
        file.close()
        l = []
        if cast:
            for line in lines:
                l.append(smart_cast(line.strip()))
        else:
            for line in lines:
                l.append(line.strip())
        return l
    except FileNotFoundError:
        print('ERROR : file', file_name, "does not exists !")
        return None


def read_ini_file(file_name, cast=True):
    try:
        file = open(file_name, "r")
        lines = file.readlines()
        file.close()
        params = dict()
        for line in lines:
            if not line.strip().startswith(';') and '=' in line:
                params[line.split("=")[0].strip()] = string_to_smart_list(line.split("=")[1].strip(), cast=cast)
        return params
    except FileNotFoundError:
        print('ERROR : file', file_name, "does not exists !")
        return None


def file_exists(file):
    return Path(file).is_file()


def folder_exists(folder):
    return Path(folder).is_dir()


def create_folder_if_not_exists(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)


def apply_contrast(image, value):
    contrast = ImageEnhance.Contrast(image)
    return contrast.enhance(value)


class PlanetMaker:
    def __init__(self, base, planet_name, extension=".tga"):
        self.sphere = base.loader.loadModel("data/models/planet_sphere.egg")
        # Load a sphere with a radius of 1 unit and the faces directed inward.

        self.sphere.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        self.sphere.setTexProjector(TextureStage.getDefault(), base.render, self.sphere)
        self.sphere.setTexPos(TextureStage.getDefault(), 0, 0, 0)
        self.sphere.setTexScale(TextureStage.getDefault(), .5)
        # Create some 3D texture coordinates on the sphere. For more info on this, check the Panda3D manual.

        final_folder = "data/models/" + planet_name + "/"
        create_folder_if_not_exists(final_folder)

        if not file_exists(final_folder + planet_name + "_0.png"):
            if file_exists("data/Map/" + planet_name + "/" + planet_name + "_up" + extension):
                tab = {"up": "2", "dn": "3", "ft": "4", "lf": "1", "rt": "0", "bk": "5"}

                for key in tab:
                    im = Image.open("data/Map/" + planet_name + "/" + planet_name + "_" + key + extension)
                    if key != "up" and key != "dn":
                        im = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
                    elif key == "up":
                        im = im.rotate(90)
                    else:
                        im = im.rotate(-90)
                    im.save(final_folder + planet_name + "_" + tab[key] + ".png")
                    im.close()

            elif file_exists("data/Map/" + planet_name + "/py" + extension):
                tab = {"px": "0", "nx": "1", "ny": "2", "py": "3", "pz": "4", "nz": "5"}
                for key in tab:
                    im = Image.open("data/Map/" + planet_name + "/" + key + extension)
                    im.save(final_folder + planet_name + "_" + tab[key] + ".png")
                    im.close()

        tex = base.loader.loadCubeMap(final_folder + planet_name + "_#.png")
        self.sphere.setTexture(tex)
        self.sphere.setTexHpr(TextureStage.getDefault(), 0, 90, 0)
        # self.sphere.setTexHpr(TextureStage.getDefault(), 0, 90, 0)
        # Load the cube map and apply it to the sphere.

        self.sphere.writeBamFile(planet_name + ".bam")


class GenerateSkyDome:
    def __init__(self, base, texture_name, extension=".tga", model="InvertedSphere.egg", bam_name="sky_sphere.bam"):
        self.sphere = base.loader.loadModel("data/models/" + model)
        # Load a sphere with a radius of 1 unit and the faces directed inward.

        self.sphere.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldPosition)
        self.sphere.setTexProjector(TextureStage.getDefault(), base.render, self.sphere)
        self.sphere.setTexPos(TextureStage.getDefault(), 0, 0, 0)
        self.sphere.setTexScale(TextureStage.getDefault(), 0.5)
        # Create some 3D texture coordinates on the sphere. For more info on this, check the Panda3D manual.

        final_folder = "data/models/" + bam_name.replace(".bam", "/")
        create_folder_if_not_exists(final_folder)

        if not file_exists(final_folder + texture_name + "_0.png"):
            if file_exists("data/Map/" + texture_name + "/" + texture_name + "_up" + extension):
                tab = {"up": "2", "dn": "3", "ft": "4", "lf": "1", "rt": "0", "bk": "5"}

                for key in tab:
                    im = Image.open("data/Map/" + texture_name + "/" + texture_name + "_" + key + extension)
                    if key != "up" and key != "dn":
                        im = im.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
                    elif key == "up":
                        im = im.rotate(90)
                    else:
                        im = im.rotate(-90)
                    im.save(final_folder + texture_name + "_" + tab[key] + ".png")
                    im.close()

            elif file_exists("data/Map/" + texture_name + "/py" + extension):
                tab = {"px": "0", "nx": "1", "ny": "2", "py": "3", "pz": "4", "nz": "5"}
                for key in tab:
                    im = Image.open("data/Map/" + texture_name + "/" + key + extension)
                    im.save(final_folder + texture_name + "_" + tab[key] + ".png")
                    im.close()

        tex = base.loader.loadCubeMap(final_folder + texture_name + "_#.png")
        self.sphere.setTexture(tex)
        self.sphere.setTexHpr(TextureStage.getDefault(), 0, 70, 0)
        # Load the cube map and apply it to the sphere.

        self.sphere.setLightOff()
        # # Tell the sphere to ignore the lighting.
        #
        self.sphere.setScale(1000)
        # # Increase the scale of the sphere so it will be larger than the scene.
        #
        # self.sphere.reparentTo(base.render)
        # # Reparent the sphere to render so you can see it.
        self.sphere.writeBamFile(bam_name)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        create_sky_boxes(sys.argv[1])
    elif len(sys.argv) > 2:
        create_sky_boxes(sys.argv[1], sys.argv[2])
