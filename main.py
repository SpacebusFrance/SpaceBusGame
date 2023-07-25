import logging
from panda3d.core import loadPrcFileData
from engine.main_engine import Game
from pathlib import Path

loadPrcFileData("", "textures-power-2 none")

if __name__ == '__main__':
    # check if 'params.ini' file exists, otherwise create it as a copy of params_default.ini
    custom_params = Path('params.ini')
    if not custom_params.exists():
        logging.info('custom parameter file does not exist, creating it.')
        src = Path('params_default.ini')
        custom_params.write_text(src.read_text())  # for text files

    # start game
    game = Game(param_file='params.ini', default_param_file='params_default.ini')
    game.run()
