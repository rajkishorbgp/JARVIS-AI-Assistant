import gtts
import playsound
import win32com.client

def gttsSpeak(query):
    test = query
    sound = gtts.gTTS(test, lang="hi")
    sound.save("jarvis.mp3")
    playsound.playsound("jarvis.mp3")


def winSpeak(query):
    speakar = win32com.client.Dispatch("SAPI.SpVoice")
    speakar.Speak(query)

# winSpeak("aisha")



# from vosk import Model,KaldiRecognizer
# import pyaudio
#
# model = Model("./vosk/vosk-model-small-en-in-0.4")
# recognizer = KaldiRecognizer(model, 16000)
#
# mic = pyaudio.PyAudio()
# stream = mic.open(rate=1600, channels=1, format=pyaudio.paInt16, input=True,
#                   frames_per_buffer=8192)
# stream.start_stream()
# while True:
#     data = stream.read(4096)
#     if recognizer.AcceptWaveform(data):
#         print(recognizer.Result())
