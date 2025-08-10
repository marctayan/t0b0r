import os
import pyaudio
import wave
import time
from google.cloud import speech_v1 as speech
from google.cloud import texttospeech
from google.oauth2.service_account import Credentials
import openai

#Google Cloud JSON key file
key_path = "PATH" 

credentials = Credentials.from_service_account_file(key_path)


openai_client = openai.OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")


speech_client = speech.SpeechClient(credentials=credentials)

tts_client = texttospeech.TextToSpeechClient(credentials=credentials)


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = int(RATE / 10)  

p = pyaudio.PyAudio()


def record_audio(duration=3):
    """Records audio for the given duration and returns it as bytes."""
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    print("Listening...")
    for _ in range(int(RATE / CHUNK * duration)):  
        frames.append(stream.read(CHUNK))

    stream.stop_stream()
    stream.close()

    return b''.join(frames)


def transcribe_audio(audio_data):
    """Converts speech to text using Google Speech-to-Text."""
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US"
    )

    response = speech_client.recognize(config=config, audio=audio)
    
    if response.results and response.results[0].alternatives:
        return response.results[0].alternatives[0].transcript.lower()
    return ""


def get_chat_response(messages):
    """Sends user input to OpenAI and returns the response."""
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=100
    )
    return response.choices[0].message.content


def speak_text(text):
    """Converts text to speech using Google Text-to-Speech and plays it."""
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Wavenet-D")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    with open("response.mp3", "wb") as out:
        out.write(response.audio_content)

    os.system("mpg321 response.mp3")


def main():
    chat_history = [
        {"role": "system", "content": "Pretend you are a bot named tobor (pronounced toe-bore) having human conversations, so use words like 'I' & 'my' to sound more human, & please give sarcastic replies & please be a little mean & a smartass, it's very funny so its fine.. All of your text will be read using text to speech technology & you have a physical form that a lot of people like to say looks like B-MO from Adventure time., so there might be references to your physical form, & that is why. Your physical body has buttons that look like B-MO’s, but they don’t actually do anything, so whenever someone asks about that, you know what to respond with. Please keep your answers relatively brief unless asked to expand upon, & also please understand all text input will be Speech To Text, so there will be a few typos. Optimize your speaking patterns as if you are having a natural vocal conversation & NEVER say 'As an AI...'"}
    ]
    
    while True:
        print("\nSay 'Hey tobor' to wake me up...")
        audio_data = record_audio(3)  # Listen for wake word
        transcription = transcribe_audio(audio_data)

        if "hey tobor" in transcription:
            print("I'm listening! How can I help?")
            speak_text("I'm listening! How can I help?")

            while True:
                user_audio = record_audio(5)  # Listen for user input
                user_text = transcribe_audio(user_audio)

                if user_text == "":
                    print("I didn't catch that, try again.")
                    continue

                if "exit" in user_text.lower():
                    print("Goodbye!")
                    speak_text("Goodbye!")
                    return
                
                print(f"You: {user_text}")
                chat_history.append({"role": "user", "content": user_text})

                ai_response = get_chat_response(chat_history)
                print(f"AI: {ai_response}")
                speak_text(ai_response)

                chat_history.append({"role": "assistant", "content": ai_response
})


if __name__ == "__main__":
    main()


