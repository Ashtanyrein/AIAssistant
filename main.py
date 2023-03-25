from datetime import datetime
import requests
import speech_recognition as sr
import sys
import pyttsx3
import webbrowser
import wikipedia
import wolframalpha
import openai
import os
from dotenv import load_dotenv
load_dotenv()

# Speech engine install
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # 0 = male, 1 = female
activationWord = 'computer'  # Single Word

# Browser config
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))

# Wolframalpha Client
appID = "H4EWAY-QEUWQWA3UH"
wolframClient = wolframalpha.Client(appID)

def speak(text, rate=120):

    engine.setProperty('rate', rate)
    engine.say(text)
    engine.runAndWait()


def parseCommand():
    listener = sr.Recognizer()
    print('Listening for command')

    with sr.Microphone() as source:
        listener.pause_threshold = 2
        input_speech = listener.listen(source)

    try:
        print('Recognizing speech...')
        query = listener.recognize_google(input_speech, language='en_gb')
        print(f"The input speech was: {query}")

    except Exception as exception:
        print("I did not quite catch that")
        speak('I did not quite catch that')

        print(exception)
        return "None"

    return query


def search_wikipedia(query=''):
    searchResults = wikipedia.search(query)
    if not searchResults:
        print("No wikipedia result")
        return 'No result received'
    try:
        wikipage = wikipedia.page(searchResults[0])
    except wikipage.DisambiguationError as error:
        wikipage = wikipedia.page(error.options[0])
    print(wikipage.title)
    wikiSummary = str(wikipage.summary)
    return wikiSummary


def listorDict(var):
    if isinstance(var, list):
        return var[0]['plaintext']
    else:
        return var['plaintext']


def search_wolframalpha(query=''):
    response = wolframClient.query(query)

    # @success: Wolfram Alpha was able to resolve the query
    # @numpods: Number of results returned
    # pod: List of results. This can also contain subpods
    if response['@success'] == 'false':
        return 'Could not compute'
    else:
        result = ''
        # Question
        pod0 = response['pod'][0]

        pod1 = response['pod'][1]
        # May contain the answer
        if ('result' in pod1['@title'].lower()) or (pod1.get('@primary', 'false') == 'true') or (
                'definition' in pod1['@title'].lower()):
            result = listorDict(pod1['subpod'])
            # remove brackets
            return result.split('(')[0]
        else:
            question = listorDict(pod0['subpod'])
            # remove brackets
            return result.split('(')[0]
            # Search Wikipedia Instead
            speak('Computation failed. Searching Wikipedia Instead.')
            search_wikipedia(question)

def query_openai(prompt = ""):
    openai.organization = os.environ['OPENAI_ORG']
    openai.api_key = os.environ['OPENAI_API_KEY']

    # Measure of randomness
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.3,
        max_tokens=120,
    )
    return response.choices[0].text


# Main loop
if __name__ == '__main__':
    speak("All systems nominal.")

    while True:
        # Parse as a list
        query = parseCommand().lower().split()

        if query[0] == activationWord:
            query.pop(0)

            # List commands
            if query[0] == 'say':
                if 'hello' in query:
                    speak("Greetings, all.")
                else:
                    query.pop(0)  # Remove Say
                    speech = ' '.join(query)
                    speak(speech)

            # Website Navigation
            if query[0] == "go" and query[1] == "to":
                speak('Opening...')
                query = " ".join(query[2:])
                webbrowser.get('chrome').open_new(query)

            # Wikipedia
            if query[0] == "wikipedia":
                query = " ".join(query)
                speak("Querying the universal databank.")
                speak(search_wikipedia(query))

            # Wolframalpha
            if query[0] == "compute" or query[0] == 'computer':
                query = " ".join(query)
                speak("Computing")
                try:
                    result = search_wolframalpha(query)
                    print(result)
                    speak(result)
                except:
                    speak("Unable to compute")

            # NoteTaking
            if query[0] == "log":
                speak("Ready to record your note")
                newNote = parseCommand().lower()
                now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

                with open('note_%s.txt' % now, 'w') as newFile:
                    newFile.write(newNote)
                speak("Note written")

            # Chat GPT
            if query[0] == 'chat':
                query.pop(0)
                query = " ".join(query)
                speech = query_openai(query)
                speak("Ok")
                print(speech)
                speak(speech)

            # Weather
            if query[0] == 'weather':
                query.pop(0)
                query = " ".join(query)
                weather_data = requests.get(
                    f'http://api.openweathermap.org/data/2.5/weather?q={query}&appid={os.environ["OPENWEATHER_API_KEY"]}&units=metric').json()

                weather = weather_data['weather'][0]['main']
                temp = round(weather_data['main']['temp'])

                weather_output = f'The weather in {query} is {weather} with a temperature of {temp} degrees'

                print(weather_output)
                speak(weather_output)

            # Restart
            if query[0] == 'restart':
                speak('Restarting')
                os.execv(sys.executable, ['python'] + sys.argv)

            # Exit
            if query[0] == 'exit':
                speak('Goodbye')
                break

