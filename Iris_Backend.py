import speech_recognition as sr
import datetime
import webbrowser
import os
import webview
import threading
import time
import urllib.parse
import random
import edge_tts
import pygame
import json
import asyncio

pygame.mixer.init()
# State tracker
va = False
window = None
window_ready = False  # Track if the window has fully initialized
 # Make sure to add this import at the very top of your file

def speak(text):
    print("Iris:", text)
    
    # 1. Update your UI frame safely
    if window and window_ready:
        try:
            js_safe_text = json.dumps(text)
            window.evaluate_js(f"updateIrisSpeech({js_safe_text});") 
        except Exception as e:
            print("JS Error:", e)
            
    if not text.strip():
        return

    # 2. Define the premium neural voice profile
    # 'en-IN-NeerjaNeural' is incredibly smooth, professional, and clear.
    # Alternative cinematic option: 'en-US-AvaNeural' or 'en-GB-SoniaNeural'
    VOICE = "en-AU-NatashaNeural" 
    temp_audio = os.path.join(cache_dir, "iris_voice.mp3")

    # 3. Create an inner async function to handle the neural generation
    async def generate_voice():
        # +15% speed makes her sound sharp and alert
        # -10Hz pitch takes away the high-pitched artificial ring
        communicate = edge_tts.Communicate(text, VOICE, rate="+0%", pitch="-0Hz")
        await communicate.save(temp_audio)

    try:
        # Run the async voice generator inside your current thread
        asyncio.run(generate_voice())

        # 4. Play the premium audio file
        pygame.mixer.music.load(temp_audio)
        pygame.mixer.music.play()
        
        # Wait for IRIS to finish speaking before listening again
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        pygame.mixer.music.unload()
        
    except Exception as e:
        print("Neural Voice Error:", e)

def listen(long=False):
    r = sr.Recognizer()
    
    # === SENSITIVITY TWEAKS FOR WHISPERING ===
    # 1. Lower the energy threshold. Default is usually 300+. 
    # Setting it between 50 and 100 makes the mic pick up very faint/low voices.
    r.energy_threshold = 70  
    
    # 2. Prevent the automatic adjuster from resetting your low threshold
    r.dynamic_energy_threshold = False  
    
    with sr.Microphone() as source:
        print("Listening ...")
        
        # 3. Reduce ambient noise adjustment time so it doesn't calibrate 
        # your whisper out as "noise"
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        # How long she waits after you finish a phrase before processing
        r.pause_threshold = 1.0

        try:
            if long:
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
            else:
                audio = r.listen(source, timeout=4, phrase_time_limit=4)
        except:
            return ""

    try:
        # Using en-IN handles the subtle cadence changes when speaking softly locally
        command = r.recognize_google(audio, language='en-IN')
        print("You (whisper):", command)
        
        if window and window_ready:
            try:
                window.evaluate_js(f"updateUserSpeech('{command}');")
            except:
                pass
        return command.lower()
    except:
        return ""

# The keys are keywords Iris listens for, values are the system commands or paths
APPS_LOOKUP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "spotify": "start spotify",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": "msedge.exe",
    "code": "code", # Opens VS Code if it's in your system PATH
    "project folder": r"C:\Users\HP\Desktop\Yaksh\Iris",
    "power point":"powerpoint",
    "word":"word"
}   

def iris_core_logic():
    global va, window, window_ready
    
    # Wait until the window is confirmed to be initialized
    while not window_ready:
        time.sleep(0.5)
    
    while True:
        if window:
            try:
                if va:
                    window.evaluate_js("setVisualState('active');")
                else:
                    window.evaluate_js("setVisualState('idle');")
            except:
                pass

        command = listen()

        if "iris" in command or "hey iris" in command or "iris listen" in command or "wake" in command or "arise" in command:
            va = True
            if window:
                try:
                    window.show()  
                except:
                    pass
            wake_up_options = [
                "How can i help you Yaksh",
                
                "Hello yaksh",
                
                "i am here to assist you yaksh",
                
                "what task i have yaksh"
            ]
            
            # 2. Pick a random phrase from the options list
            chosen_greeting = random.choice(wake_up_options)
            
            # 3. Say it out loud cleanly using your multi-line safe speak function
            speak(chosen_greeting)
            

        if va:
            if "hello" in command:
                speak("Hello Yaksh, how can I help you?")

            elif "time" in command:
                time_now = datetime.datetime.now().strftime("%H:%M")
                speak(f"The time is {time_now}")
                
            elif "open youtube" in command:
                speak("Opening YouTube for you, Yaksh")
                webbrowser.open("https://youtube.com")

            elif "open google" in command:
                speak("Opening Google for you, Yaksh")
                webbrowser.open("https://google.com")

            elif "search" in command:
                speak("What should I search?")
                query = listen(long=True)
                if query:
                    quoted_query = urllib.parse.quote(query)
                    webbrowser.open(f"https://www.google.com/search?q={quoted_query}")
                    speak("Here is what I found...")

            elif "notepad" in command:
                speak("Opening Notepad for you, Yaksh")
                os.system("notepad")

            elif "joke" in command:
                speak("Why do programmers hate nature? Too many bugs.")

            elif "who are you" in command:
                speak("I am Iris, your personal assistant created by Yaksh.")

            elif "are you there" in command:
                speak("Yes, I am here")
                
            elif "open" in command:
                app_opened = False
                
                for app_name, app_path in APPS_LOOKUP.items():
                    if app_name in command:
                        speak(f"Opening {app_name} for you, Yaksh.")
                        
                        # If it's a full path or folder, use startfile; otherwise run system command
                        if "\\" in app_path or ":" in app_path:
                            os.startfile(app_path)
                        else:
                            os.system(app_path)
                            
                        app_opened = True
                        break # Stop looking once we found a match
                
                if not app_opened:
                    speak("I couldn't find that application in my registry, Yaksh.")
            
            elif "sleep" in command:
                va = False
                speak("Going to sleep")
                if window:
                    try:
                        window.hide()  
                    except:
                        pass
            
            elif "exit" in command or "stop" in command or "log off" in command:
                speak("Logging off.")
                if window:
                    try:
                        window.hide()
                    except:
                        pass 
                os._exit(0)

def on_window_loaded():
    """Callback function that runs the moment the UI window successfully loads"""
    global window_ready
    window_ready = True
    print("Iris UI loaded successfully.")

# Setup UI Window Path
current_dir = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(current_dir, 'index.html')

# Local cache setup
cache_dir = os.path.join(current_dir, '.iris_cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Create the desktop layout window
window = webview.create_window(
    'Iris AI', 
    r'C:\Users\HP\Desktop\Yaksh\Iris\index.html',
    frameless=True,    
    easy_drag=True,    
    background_color='#090d16',
    width=450,
    height=600,
    hidden=True        
)
def start_listening_loop(win):
    """Safely boots your background microphone thread *after* the GUI structure exists"""
    # Force set the loaded state flag to release your while-loop guard
    global window_ready
    window_ready = True
    
    background_thread = threading.Thread(target=iris_core_logic)
    background_thread.daemon = True
    background_thread.start()
    print("Iris background logic thread attached and monitoring.")

# --- SPYDER KERNEL RUNTIME START ---
# Pass the function and target window context straight into the main event loop
webview.start(start_listening_loop, window, storage_path=cache_dir, gui='edgechromium')
# Start the Python voice listener loop in a background thread

# --- SPYDER KERNEL FIX ---
# 1. We bind the logic to run ONLY after the window frame loads using `window.events.loaded`
window.events.loaded += on_window_loaded

# 2. We set GUI loop handling explicitly to keep Spyder's IPython kernel happy
webview.start(storage_path=cache_dir, gui='edgechromium')