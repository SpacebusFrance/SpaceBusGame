import logging
from gtts import gTTS

# This module is imported so that we can
# play the converted audio
import os
import pyttsx3

if __name__ == '__main__':
    engine = pyttsx3.init()
    text = "Bonjour équipage Equality. Je suis Kora, votre IA de bord. Tous les systèmes sont en ligne, nous pouvons " \
           "amorcer la procédure de démarrage"
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)
    engine.say(text)
    # play the speech
    engine.runAndWait()
