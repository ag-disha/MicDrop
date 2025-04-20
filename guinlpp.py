import serial
import serial.tools.list_ports
import speech_recognition as sr
from transformers import pipeline
import tkinter as tk
from tkinter import ttk
import google.generativeai as genai

# === Setup Gemini API ===
genai.configure(api_key="AIzaSyDUquq8jQOTetYAFFlhdQ7M9QfNeIgo9gQ")  # API key
model = genai.GenerativeModel("gemini-1.5-pro")

# === Connection to Arduino ===
def get_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" in p.description or "USB Serial Device" in p.description:
            return p.device
    return None

arduino_port = get_arduino_port()
if arduino_port:
    arduino = serial.Serial(arduino_port, 9600, timeout=1)
    print(f"Connected to Arduino on {arduino_port}")
else:
    arduino = None
    print("⚠️ Arduino not detected. Continuing without Arduino input.")

# === Setup NLP Tools ===
recognizer = sr.Recognizer()
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


# === Speech Processing Functions ===
def transcribe_speech(duration=10):
    with sr.Microphone() as source:
        audio = recognizer.listen(source, phrase_time_limit=duration)
        try:
            return recognizer.recognize_google(audio)
        except:
            return ""

def summarize_text(text):
    summary = summarizer(text, max_length=30, min_length=10, do_sample=False)
    return summary[0]['summary_text']

def check_topic_relevance(text, topic):
    prompt = f"""Evaluate how relevant the following speech is to the topic '{topic}'.\n
    Speech: \"{text}\"\n
    Reply only with the relevance percentage (like: 72). No explanation."""
    try:
        response = model.generate_content(prompt)
        percentage = ''.join(filter(str.isdigit, response.text))
        return int(percentage) if percentage else 0
    except Exception as e:
        print(f"Gemini API error: {e}")
        return -1

def get_accuracy_from_gemini(topic, speech):
    prompt = f"""
    Given the topic: "{topic}"
    And the following speech transcript: "{speech}"
    Analyze how accurately the speech aligns with the topic and provide a single percentage number from 0 to 100.
    Respond ONLY with the number, nothing else.
    """
    try:
        response = model.generate_content(prompt)
        percentage = ''.join(filter(str.isdigit, response.text))
        return int(percentage) if percentage else 0
    except Exception as e:
        print(f"Gemini error: {e}")
        return -1

# === GUI Setup ===
root = tk.Tk()
root.title("MicDrop Dashboard")
root.geometry("800x600")
root.configure(bg="#f0f4f8")

# === Styling ===
style = ttk.Style()
style.configure("TLabel", background="#f0f4f8", font=("Arial", 12))
style.configure("TButton", font=("Arial", 12, "bold"), padding=6)

# === Title ===
title_label = ttk.Label(root, text="🎙️ MicDrop Speech Evaluator", font=("Arial", 18, "bold"))
title_label.pack(pady=20)

# === Topic Input ===
topic_frame = tk.Frame(root, bg="#f0f4f8")
topic_frame.pack(pady=10)
tk.Label(topic_frame, text="Enter Topic:", font=("Arial", 12), bg="#f0f4f8").pack(side=tk.LEFT, padx=5)
topic_entry = tk.Entry(topic_frame, width=40, font=("Arial", 12))
topic_entry.insert(0, " ")
topic_entry.pack(side=tk.LEFT, padx=5)

# === Output Display ===
output_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.GROOVE)
output_frame.pack(pady=15, fill=tk.BOTH, expand=True, padx=20)
output_text = tk.Text(output_frame, height=20, wrap=tk.WORD, font=("Consolas", 11), bg="#ffffff", fg="#333333")
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# === Start Button ===
tk.Button(root, text="🎤 Start Listening", command=lambda: process_speech(), bg="#007acc", fg="white", font=("Arial", 12, "bold"), padx=20, pady=10).pack(pady=10)

# === Process Speech Function ===
def process_speech():
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "Waiting for Arduino trigger...\n")
    root.update()

    if arduino:
        while True:
            if arduino.in_waiting > 0:
                line = arduino.readline().decode().strip()
                if line == "SPEAKING":
                    break
    else:
        output_text.insert(tk.END, "⚠️ Arduino not connected. Listening directly...\n")

    output_text.insert(tk.END, "\n🔊 Listening for speech...\n")
    root.update()

    spoken = transcribe_speech()
    if not spoken:
        output_text.insert(tk.END, "❌ Could not recognize speech.\n")
        return

    summary = summarize_text(spoken)
    topic = topic_entry.get()
    relevance_score = get_accuracy_from_gemini(topic, spoken)

    output_text.insert(tk.END, f"\n🗣 You said: {spoken}\n")
    output_text.insert(tk.END, f"\n📝 Summary: {summary}\n")
    output_text.insert(tk.END, f"\n📊 Relevance to Topic: {relevance_score}%\n")
    output_text.insert(tk.END, "\n----------------------------------------------\n")

root.mainloop()
