from gtts import gTTS

file = open("generated_text.txt")
lines = file.readlines()
file.close()
for line in lines:
    key = line.split("=")[0].strip()
    text = line.split("=")[1].strip()
    tts = gTTS(text=text, lang='fr')
    tts.save(key + ".mp3")
