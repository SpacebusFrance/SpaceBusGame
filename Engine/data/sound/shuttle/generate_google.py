from google_speech import Speech, SpeechSegment

# say "Hello World"
# text = "Pilote automatique activé. Corrections dynamiques désactivées par défaut. veuillez les réactiver manuellement."
# lang = "fr"
# # speech = Speech(text, lang)
# speech = SpeechSegment(text, lang, segment_num=1)
# speech.play(None)
# # print(speech.buildUrl(cache_friendly=True))
# file = speech.download(speech.buildUrl(cache_friendly=True))
# f = open('test.mp3', 'wb')
# f.write(file)
# f.close()


def generate_text(text, file_name):
    speech = SpeechSegment(text, "fr", segment_num=1)
    # speech.play(None)
    f = open(file_name + '.mp3', 'wb')
    f.write(speech.download(speech.buildUrl(cache_friendly=True)))
    f.close()


def test(text):
    # reverberance
    sox_effects = ("reverb", "1.5")
    speech = Speech(text, "fr")
    speech.play(("speed", "1.2",
                 "reverb", "80",
                 "pitch", "-300",
                 "pad", "1", "5",
                 # "oops",
                 #"lowpass", "100", "5"
                 ))


test("Batterie 3. Activée et en ligne")
# generate_text("ca va toi ?", "out")
# speech.save("test.mp3")

# you can also apply audio effects (using SoX)
# see http://sox.sourceforge.net/sox.html#EFFECTS for full effect documentation
# sox_effects = ("reverb", "1.5")
# speech.play(sox_effects)
