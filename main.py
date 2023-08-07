
import speech_recognition as sr
import webbrowser
import os
import datetime
import openai
from config import apikey
from voice import winSpeak


# Initialize chatStr variable
chatStr = ""

# Function to generate chat-based response using OpenAI API
def ai(query):
    # Set the OpenAI API key
    openai.api_key = apikey

    # Create the text variable to store the response
    text = f"OpenAI response for Prompt: {query}\n *********************************************\n\n\n\n"

    # Call the OpenAI API to get the response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": query
            },
            {
                "role": "user",
                "content": ""
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Check if the response contains the 'choices' key
    if "choices" in response:
        # Check if the first choice contains the 'message' key
        if "message" in response["choices"][0]:
            # Check if the 'content' key is present in the 'message'
            if "content" in response["choices"][0]["message"]:
                # Append the response text to the 'text' variable
                text += response["choices"][0]["message"]["content"]

                # Create the "Openai" directory if it doesn't exist
                if not os.path.exists("Openai"):
                    os.mkdir("Openai")

                # Save the response text to a file
                with open(f"Openai/{''.join(query.split('intelligence')[1:]).strip()}.txt", "w") as f:
                    f.write(text)
            else:
                print("Error: 'content' key not found in the response message.")
        else:
            print("Error: 'message' key not found in the response.")
    else:
        print("Error: 'choices' key not found in the response.")


def chat(query):
    global chatStr
    # Set the OpenAI API key
    openai.api_key = apikey

    chatStr += f"Raj: {query}\nJarvis: "
    # Call the OpenAI API to get the response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": chatStr
            },
            {
                "role": "user",
                "content": ""
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Check if the response contains the 'choices' key
    if "choices" in response:
        # Check if the first choice contains the 'message' key
        if "message" in response["choices"][0]:
            # Check if the 'content' key is present in the 'message'
            if "content" in response["choices"][0]["message"]:
                # Append the response text to the 'text' variable
                response_text = response["choices"][0]["message"].get("content", "")
                chatStr += f"{response_text}\n"
                print(chatStr)
                speak(response_text)
            else:
                print("Error: 'content' key not found in the response message.")
        else:
            print("Error: 'message' key not found in the response.")
    else:
        print("Error: 'choices' key not found in the response.")
    return response["choices"][0]["message"]["content"]


def takeCommand():
    ans = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening...')
        ans.pause_threshold = 0.5
        audio = ans.listen(source)

        try:
            print("Recognizing...")
            text = ans.recognize_google(audio, language="en-in")

        except Exception as e:
            print("Sorry could not recognize your voice!!!")
            speak('Sorry could not recognize your voice')
            return " "
        return text

def speak(query):
    winSpeak(query)

query = "Hello sir, I'm jarvis."
speak(query)
while True:
    query = takeCommand()
    # todo Add more sites
    sites = [["youtube", "https://www.youtube.com/"], ["instagram", "https://www.instagram.com/"],
             ["facebook", "https://www.facebook.com/"],
             ["wikipedia", "https://www.wikipedia.org/"], ["google", "https://www.google.com/"]]

    for site in sites:
        if f"Open {site[0]}".lower() in query.lower():
            query = f"Opening {site[0]} sir..."
            webbrowser.open(site[1])
            speak(query)

    if "open music" in query:
        musicPath = "Music\\raj.mp3"
        query = f"Opening music"
        os.startfile(musicPath)
        speak(query)

    elif "Using artificial intelligence".lower() in query.lower():
        ai(query)

    elif "input query".lower() in query.lower():
        query = input("Enter any query: ")
        speak(f"Sir, Your query is {query}")
        ai(query)

    elif "the time" in query:
        hour = datetime.datetime.now().strftime("%H")
        min = datetime.datetime.now().strftime("%M")
        sec = datetime.datetime.now().strftime("%S")
        speak(f"Sir Time is {hour} bus ke {min} minutes or {sec} second")

    elif "jarvis Quit".lower() in query.lower():
        speak(f"Okay Sir")
        exit()

    else:
        chat(query)