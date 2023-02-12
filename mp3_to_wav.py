import logging
import os
from pydub import AudioSegment

logging.basicConfig(level='INFO')


if __name__ == '__main__':
    folder = 'data/sound/'
    files = os.listdir(folder)
    for file in files:
        if file.endswith('.mp3') and file.replace('mp3', 'wav') not in files:
            logging.info(f'exporting "{file}" to wav')
            sound = AudioSegment.from_mp3(folder + file)
            sound.export(folder + file.replace('mp3', 'wav'), format="wav")
    logging.info('all done')
