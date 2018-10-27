from Engine.Utils.utils import read_ini_file


class Param:
    def __init__(self):
        self._params = read_ini_file("params.ini")

    def __call__(self, key):
        if key in self._params:
            return self._params[key]
        else:
            return None
    #
    # def load_file(self, name="params.ini"):
    #     try:
    #         file = open(name, "r")
    #         lines = file.readlines()
    #         file.close()
    #         self._params.clear()
    #         for line in lines:
    #             if '=' in line:
    #                 self._params[line.split("=")[0].strip()] = smart_cast(line.split("=")[1].strip())
    #     except FileNotFoundError:
    #         print('ERROR : file', name, "does not exists !")
