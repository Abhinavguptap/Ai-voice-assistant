#!/usr/bin/env python3
"""
Voice Assistant - STABLE VERSION
=================================
Fixes: Won't crash, keeps running, better error handling
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import os
import traceback

# Voice imports
import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import datetime
try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except:
    BRIGHTNESS_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except:
    PYAUTOGUI_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except:
    PSUTIL_AVAILABLE = False


app = Flask(__name__)
CORS(app)

STATE = {
    'status': 'INITIALIZING',
    'info': 'Starting...',
    'transcript': 'Initializing...',
    'running': False
}


class StableVoiceAssistant:
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 STABLE VOICE ASSISTANT")
        print("="*70)
        
        # Speech recognizer
        self.recognizer = sr.Recognizer()
        print("✓ Speech recognizer ready")
        
        # Text-to-speech with error recovery
        self.engine = None
        self.init_tts()
        
        # Gemini - try to connect but don't fail if it doesn't work
        self.gemini = None
        self.init_gemini()
        
        # Apps
        self.apps = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'chrome': 'chrome.exe',
            'edge': 'msedge.exe',
        }
        print(f"✓ {len(self.apps)} apps available")
        
        print("\n" + "="*70)
        print("✅ READY!")
        print("="*70 + "\n")
        
        STATE['status'] = 'READY'
        STATE['info'] = 'Click START'
        STATE['transcript'] = '✨ Ready! Click START.'
    
    def init_tts(self):
        """Initialize text-to-speech with retry"""
        print("\n🔊 Initializing Speech...")
        
        for attempt in range(3):
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 1.0)
                
                # Test it
                self.engine.say("Ready")
                self.engine.runAndWait()
                
                print("✓ Speech working!")
                return
                
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)
                    self.engine = None
        
        print("❌ Speech failed after 3 attempts")
        print("   Assistant will work but won't speak")
    
    def init_gemini(self):
        """Initialize Gemini without crashing"""
        print("\n🤖 Setting up Gemini...")
        
        if not GEMINI_AVAILABLE:
            print("❌ google-generativeai not installed")
            print("   Fix: pip install google-generativeai")
            return
        
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  No GEMINI_API_KEY environment variable")
            print("   Set it with: set GEMINI_API_KEY=your-key")
            print("   Or get key at: https://aistudio.google.com/app/apikey")
            
            # Try hardcoded key as fallback
            api_key = 'INSERT_KEY_HERE'
            print(f"   Trying fallback key: {api_key[:20]}...")
        
        try:
            genai.configure(api_key=api_key)
            
            # Try models in order
            models = [
                'gemini-2.5-flash',
            ]
            
            for model_name in models:
                try:
                    print(f"   Testing {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    chat = model.start_chat(history=[])
                    response = chat.send_message("Hi")
                    
                    # Success!
                    self.gemini = model.start_chat(history=[])
                    print(f"✓ Gemini connected: {model_name}")
                    return
                    
                except Exception as e:
                    error_msg = str(e)
                    if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
                        print(f"   ❌ Invalid API key!")
                        print(f"   Get new key: https://aistudio.google.com/app/apikey")
                        return
                    elif "404" in error_msg:
                        print(f"   ✗ {model_name} not available")
                    else:
                        print(f"   ✗ {error_msg[:50]}")
            
            print("❌ All Gemini models failed")
            print("   Get API key: https://aistudio.google.com/app/apikey")
            
        except Exception as e:
            print(f"❌ Gemini setup error: {e}")
    
    def speak(self, text):
        """Speak with error recovery"""
        print(f"🔊 {text}")
        
        if not self.engine:
            # Try to reinitialize
            try:
                self.engine = pyttsx3.init()
            except:
                print("   (Speech unavailable)")
                return
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"   Speech error: {e}")
            # Reset engine
            self.engine = None
            try:
                self.engine = pyttsx3.init()
                self.engine.say(text)
                self.engine.runAndWait()
            except:
                print("   (Speech failed)")
    
    def listen(self):
        """Listen with better error handling"""
        try:
            with sr.Microphone() as source:
                STATE['status'] = 'LISTENING'
                STATE['info'] = '🎤 Listening...'
                print("\n🎤 Listening...")
                
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=12)
                
                STATE['status'] = 'PROCESSING'
                STATE['info'] = 'Processing...'
                
                text = self.recognizer.recognize_google(audio)
                STATE['transcript'] = f"👤 YOU: {text}"
                print(f"✓ Heard: {text}")
                return text.lower()
                
        except sr.WaitTimeoutError:
            print("⏱️ Timeout")
            STATE['status'] = 'READY'
            STATE['info'] = 'Timeout - speak again'
            return ""
            
        except sr.UnknownValueError:
            print("❓ Couldn't understand")
            STATE['status'] = 'READY'
            STATE['info'] = 'Couldn\'t understand'
            return ""
            
        except Exception as e:
            print(f"❌ Listen error: {e}")
            STATE['status'] = 'READY'
            STATE['info'] = 'Error - try again'
            return ""
    
    def process(self, cmd):
        """Process command without crashing"""
        print(f"\n📝 Command: {cmd}")
        
        if not cmd:
            return True  # Keep running
        
        try:
            # Gemini
            if 'gemini' in cmd:
                question = cmd.replace('use gemini', '').replace('ask gemini', '').replace('gemini', '').strip()
                
                if not question:
                    STATE['transcript'] = "🤖 What's your question?"
                    self.speak("What's your question?")
                    return True
                
                if self.gemini:
                    STATE['status'] = 'THINKING'
                    STATE['info'] = '🧠 Asking Gemini...'
                    print(f"🤖 Question: {question}")
                    
                    try:
                        response = self.gemini.send_message(question)
                        answer = response.text
                        
                        print(f"✓ Answer: {answer[:100]}...")
                        
                        STATE['status'] = 'RESPONDING'
                        STATE['transcript'] = f"🤖 GEMINI: {answer[:300]}..."
                        
                        # Speak short version
                        short = answer[:200] if len(answer) > 200 else answer
                        self.speak(short)
                        
                    except Exception as e:
                        print(f"❌ Gemini error: {e}")
                        STATE['transcript'] = "🤖 Gemini error occurred"
                        self.speak("Gemini encountered an error")
                else:
                    STATE['transcript'] = "🤖 Gemini not available - check API key"
                    self.speak("Gemini is not available")
            
            # Time
            elif 'time' in cmd:
                t = datetime.datetime.now().strftime('%I:%M %p')
                STATE['transcript'] = f"🤖 The time is {t}"
                self.speak(f"The time is {t}")
            
            # Date
            elif 'date' in cmd:
                d = datetime.datetime.now().strftime('%A, %B %d')
                STATE['transcript'] = f"🤖 Today is {d}"
                self.speak(f"Today is {d}")
            
            # Battery
            elif 'battery' in cmd:
                if PSUTIL_AVAILABLE:
                    try:
                        battery = psutil.sensors_battery()
                        if battery:
                            msg = f"Battery at {battery.percent} percent"
                            STATE['transcript'] = f"🤖 {msg}"
                            self.speak(msg)
                        else:
                            STATE['transcript'] = "🤖 No battery"
                            self.speak("No battery detected")
                    except:
                        STATE['transcript'] = "🤖 Battery error"
                        self.speak("Can't check battery")
                else:
                    STATE['transcript'] = "🤖 Battery monitoring not available"
                    self.speak("Battery monitoring not available")
            
            # Open
            elif 'open' in cmd:
                app = cmd.replace('open', '').strip()
                
                if app in self.apps:
                    subprocess.Popen(self.apps[app], shell=True)
                    STATE['transcript'] = f"🤖 Opening {app}"
                    self.speak(f"Opening {app}")
                else:
                    webbrowser.open(f"https://www.google.com/search?q={app}")
                    STATE['transcript'] = f"🤖 Searching {app}"
                    self.speak(f"Searching {app}")
            
            # Search
            elif 'search' in cmd:
                q = cmd.replace('search for', '').replace('search', '').strip()
                if q:
                    webbrowser.open(f"https://www.google.com/search?q={q}")
                    STATE['transcript'] = f"🤖 Searching {q}"
                    self.speak(f"Searching {q}")
            
            # Media
            elif 'play' in cmd and PYAUTOGUI_AVAILABLE:
                pyautogui.press('playpause')
                STATE['transcript'] = "🤖 Playing"
                self.speak("Playing")
            
            elif 'pause' in cmd and PYAUTOGUI_AVAILABLE:
                pyautogui.press('playpause')
                STATE['transcript'] = "🤖 Paused"
                self.speak("Paused")
            
            # Volume
            elif 'volume up' in cmd and PYAUTOGUI_AVAILABLE:
                for _ in range(3):
                    pyautogui.press('volumeup')
                STATE['transcript'] = "🤖 Volume up"
                self.speak("Volume up")
            
            elif 'volume down' in cmd and PYAUTOGUI_AVAILABLE:
                for _ in range(3):
                    pyautogui.press('volumedown')
                STATE['transcript'] = "🤖 Volume down"
                self.speak("Volume down")
            # ===== Brightness =====
            elif ("brightness up" in cmd or "increase brightness" in cmd) and BRIGHTNESS_AVAILABLE:
                current = sbc.get_brightness(display=0)
                if isinstance(current, list):
                    current = current[0]
                new = min(100, current + 10)
                sbc.set_brightness(new)
                self.speak("Brightness up")

            elif ("brightness down" in cmd or "decrease brightness" in cmd) and BRIGHTNESS_AVAILABLE:
                current = sbc.get_brightness(display=0)
                if isinstance(current, list):
                    current = current[0]
                new = max(0, current - 10)
                sbc.set_brightness(new)
                self.speak("Brightness down")            
            # Help
            elif 'help' in cmd:
                msg = "Say: time, date, battery, open app, search, or use gemini"
                STATE['transcript'] = f"🤖 {msg}"
                self.speak(msg)
            
            # Stop
            elif any(w in cmd for w in ['stop', 'exit', 'quit']):
                STATE['transcript'] = "🤖 Goodbye!"
                self.speak("Goodbye!")
                STATE['running'] = False
                return False  # Stop loop
            
            # Unknown
            else:
                STATE['transcript'] = "🤖 Try: time, search, open app, use gemini"
                self.speak("Try saying time, search, or use gemini")
            
        except Exception as e:
            print(f"❌ Process error: {e}")
            traceback.print_exc()
            STATE['transcript'] = "🤖 Error occurred"
            self.speak("An error occurred")
        
        STATE['status'] = 'READY'
        STATE['info'] = 'Ready'
        return True  # Keep running
    
    def loop(self):
        """Main loop that never crashes"""
        print("\n🔄 Starting loop...")
        
        loop_count = 0
        
        while STATE['running']:
            try:
                loop_count += 1
                print(f"\n--- Loop {loop_count} ---")
                
                cmd = self.listen()
                
                if cmd:
                    should_continue = self.process(cmd)
                    if not should_continue:
                        print("🛑 Stopping by command")
                        break
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n⌨️ Keyboard interrupt")
                break
                
            except Exception as e:
                print(f"❌ Loop error: {e}")
                traceback.print_exc()
                print("Continuing anyway...")
                STATE['status'] = 'READY'
                STATE['info'] = 'Recovered from error'
                time.sleep(1)
        
        print("🛑 Loop ended\n")
        STATE['status'] = 'STOPPED'
        STATE['running'] = False


# Initialize
assistant = StableVoiceAssistant()


# Routes
@app.route('/')
def home():
    return HTML


@app.route('/status')
def status():
    return jsonify(STATE)


@app.route('/start', methods=['POST'])
def start():
    print("\n▶️ START")
    if not STATE['running']:
        STATE['running'] = True
        STATE['status'] = 'READY'
        STATE['info'] = 'Listening...'
        threading.Thread(target=assistant.loop, daemon=True).start()
        print("✅ Started")
    return jsonify({'ok': True})


@app.route('/stop', methods=['POST'])
def stop():
    print("\n⏹️ STOP")
    STATE['running'] = False
    STATE['status'] = 'PAUSED'
    STATE['info'] = 'Paused'
    print("✅ Stopped")
    return jsonify({'ok': True})


@app.route('/cmd', methods=['POST'])
def cmd():
    c = request.json.get('cmd')
    print(f"\n📨 Quick: {c}")
    STATE['transcript'] = f"👤 YOU: {c}"
    threading.Thread(target=lambda: assistant.process(c), daemon=True).start()
    return jsonify({'ok': True})


HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>Stable Voice Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: monospace; background: #050810; color: #00f0ff;
            display: flex; flex-direction: column; align-items: center;
            justify-content: center; height: 100vh;
        }
        .brain { font-size: 8rem; margin-bottom: 2rem; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
        .status { font-size: 3rem; font-weight: bold; margin-bottom: 1rem; }
        .info { font-size: 1.2rem; margin-bottom: 2rem; color: #00ff88; }
        .transcript {
            position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
            width: 80%; max-width: 700px; background: rgba(0,0,0,0.7);
            border: 2px solid #00f0ff; border-radius: 10px; padding: 1.5rem;
            max-height: 150px; overflow-y: auto;
        }
        .controls { position: fixed; top: 2rem; right: 2rem; display: flex; gap: 1rem; }
        button {
            padding: 1rem 2rem; background: rgba(0,240,255,0.2);
            border: 2px solid #00f0ff; color: #00f0ff; border-radius: 5px;
            cursor: pointer; font-size: 1rem; font-weight: bold;
        }
        button:hover { background: rgba(0,240,255,0.4); }
        button.active { background: #00f0ff; color: #000; }
        .quick { position: fixed; top: 2rem; left: 2rem; max-width: 250px; }
        .quick div {
            background: rgba(0,240,255,0.1); border-left: 3px solid #00f0ff;
            padding: 0.7rem 1rem; margin-bottom: 0.5rem; cursor: pointer;
            font-size: 0.9rem;
        }
        .quick div:hover { background: rgba(0,240,255,0.2); transform: translateX(3px); }
    </style>
</head>
<body>
    <div class="brain">🧠</div>
    <div class="status" id="status">READY</div>
    <div class="info" id="info">Click START</div>
    <div class="transcript" id="transcript">Ready to start!</div>
    <div class="controls">
        <button id="start">START</button>
        <button id="stop">STOP</button>
    </div>
    <div class="quick">
        <div onclick="cmd('use gemini explain gravity')">🤖 Ask Gemini</div>
        <div onclick="cmd('what is the time')">⏰ Time</div>
        <div onclick="cmd('what is the date')">📅 Date</div>
        <div onclick="cmd('battery status')">🔋 Battery</div>
        <div onclick="cmd('open calculator')">🔢 Calculator</div>
        <div onclick="cmd('search for python')">🔍 Search</div>
        <div onclick="cmd('volume up')">🔊 Volume Up</div>
        <div onclick="cmd('volume down')">🔉 Volume Down</div>
        <div onclick="cmd('play music')">▶️ Play/Pause</div>
        <div onclick="cmd('brightness up')">💡 Brightness Up</div>
<div onclick="cmd('brightness down')">🌙 Brightness Down</div>

    </div>
    <script>
        function update() {
            fetch('/status').then(r => r.json()).then(d => {
                document.getElementById('status').textContent = d.status;
                document.getElementById('info').textContent = d.info;
                document.getElementById('transcript').textContent = d.transcript;
                
                const start = document.getElementById('start');
                const stop = document.getElementById('stop');
                
                if (d.running) {
                    start.classList.add('active');
                    stop.classList.remove('active');
                } else {
                    start.classList.remove('active');
                    stop.classList.add('active');
                }
            }).catch(() => {});
        }
        
        setInterval(update, 400);
        
        document.getElementById('start').onclick = () => {
            fetch('/start', {method: 'POST'});
        };
        
        document.getElementById('stop').onclick = () => {
            fetch('/stop', {method: 'POST'});
        };
        
        function cmd(c) {
            fetch('/cmd', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cmd: c})
            });
        }
        
        update();
    </script>
</body>
</html>'''


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🌐 STABLE VOICE ASSISTANT SERVER")
    print("="*70)
    print("\n✅ Open: http://localhost:5000")
    print("✅ This version won't crash!")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
