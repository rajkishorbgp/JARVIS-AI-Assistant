import speech_recognition as sr


r = sr.Recognizer()
with sr.Microphone() as source:
        print('Speak Anything : ')
        r.pause_threshold = 1
        audio = r.listen(source)
        print("audio record")

        try:
            print("Execut .. try.")
            text = r.recognize_google(audio,language="hi-in")
            print('you said : {}'.format(text))
        except:
            print('Sorry could not recognize your voice')
