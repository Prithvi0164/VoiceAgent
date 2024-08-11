#import streamlit as st
import time
import pyttsx3
import speech_recognition as sr
import spacy
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play

# Initialize OpenAI client with your API key
client = OpenAI()

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Initialize the speech engine
engine = pyttsx3.init()
recognizer = sr.Recognizer()

# Function to speak text
# def speak(text):
#     engine.say(text)
#     engine.runAndWait()


def speak(text):
    # Generate speech using OpenAI's TTS model
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    
    # Save the audio to a file
    response.stream_to_file("output.mp3")
    
    # Load and play the audio file using pydub
    audio = AudioSegment.from_mp3("output.mp3")
    play(audio)

# Convert audio from the microphone into text using the Google Speech Recognition service
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            return ""
        except sr.RequestError:
            print("Sorry, my speech service is down.")
            return ""

       

# Function to extract name using spaCy NER
def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return ''

# Step 1: Create an Assistant with File Search Enabled
def create_assistant():
    assistant = client.beta.assistants.create(
        name="Concise Human-Like Assistant",
        instructions="You are an assistant that answers questions based on the documents provided. Answer in clear, concise terms, using the fewest words possible, and respond as if you are a human speaking naturally.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )
    return assistant

# Step 2: Create a Vector Store and Upload Files
def create_vector_store_and_upload_files(file_paths):
    vector_store = client.beta.vector_stores.create(name="My Documents")
    file_streams = [open(path, "rb") for path in file_paths]

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    return vector_store.id

# Step 3: Update the Assistant to Use the Vector Store
def update_assistant_with_vector_store(assistant_id, vector_store_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        #tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    return assistant

# Step 4: Create a Thread for Interaction
def create_thread():
    thread = client.beta.threads.create()
    return thread.id

# Step 5: Ask Questions Based on Uploaded Documents
def ask_question(assistant_id, thread_id, question, user_name):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    last_message = next(
        (msg for msg in (messages.data) if msg.role == "assistant"),
        None
    )

    if last_message:
        response_text = last_message.content[0].text.value
        speak(f"{user_name}, {response_text}")
        print(response_text)

# # Main function to initialize the assistant and vector store
# def initialize():
#     # File paths to upload
#     file_paths = [r"C:\Users\prith\Downloads\document\CloudPoint.txt", r"C:\Users\prith\Downloads\document\CloudSocial.txt"]

#     # Create the assistant
#     assistant = create_assistant()

#     #print(f"Assistant created with ID: {assistant.id}")

#     # Create vector store and upload files
#     vector_store_id = create_vector_store_and_upload_files(file_paths)

#     #print(f"Vector Store ID: {vector_store_id}")

#     # Update assistant with vector store
#     update_assistant_with_vector_store(assistant.id, vector_store_id)

#     #print(f"Assistant updated with Vector Store ID: {vector_store_id}")

#     # Create a thread for interaction
#     thread_id = create_thread()
#     print(f"Thread created with ID: {thread_id}")

#     return assistant.id, thread_id

# Main function to initialize the assistant and vector store
def initialize():
    # File paths to upload
    file_paths = [r"C:\Users\prith\Downloads\document\CloudPoint.txt", r"C:\Users\prith\Downloads\document\CloudSocial.txt"]

    # Create the assistant

    assistant_id ='asst_iR68QPcP4J2f3VH65nf3TiC2'
    #print(f"Assistant created with ID: {assistant.id}")

    # Create vector store and upload files
    
    vector_store_id ='vs_xd1zZGkahoePgMUwxxRI5zmM'
    #print(f"Vector Store ID: {vector_store_id}")

    # Update assistant with vector store
  
    update_assistant_with_vector_store(assistant_id, vector_store_id)
    #print(f"Assistant updated with Vector Store ID: {vector_store_id}")

    # Create a thread for interaction
    thread_id = create_thread()
    print(f"Thread created with ID: {thread_id}")

    return assistant_id, thread_id

# Main function to handle the question-answer loop
def main(assistant_id, thread_id):
    user_name = None

    # Welcome the user and ask for their name
    speak("Hello! Welcome to our service. What is your name?")
    user_response = listen()
    user_name = extract_name(user_response)
    
    # if user_response:
    #     # Attempt to extract the user's name
    #     user_name = extract_name(user_response)
    #     if not user_name:
    #         speak("I didn't quite catch your name. Could you please tell me your name again?")
    #         user_response = listen()
    #         user_name = extract_name(user_response)
        
    #     if user_name:
    #         speak(f"Nice to meet you, {user_name}. How can I assist you today?")
    #     else:
    #         user_name = "there"
    #         speak("Nice to meet you. How can I assist you today?")
    
    # Continuously ask questions until the user decides to quit
    while True:
        speak("Please ask your question or say exit to quit.")
        question = listen()
        if question and "exit" in question.lower():
            speak(f"Goodbye, {user_name}. Have a great day!")
            break
        if question:
            ask_question(assistant_id, thread_id, question, user_name)



if __name__ == "__main__":
     
        assistant_id, thread_id = initialize()  # Run this once to set up
        main(assistant_id, thread_id)  # Call this to start the Q&A session
