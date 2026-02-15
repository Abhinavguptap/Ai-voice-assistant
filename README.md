# 🧠 AI Voice Assistant Automation System

An AI-powered desktop voice assistant built with **Python, Flask, and Gemini AI** that enables hands-free computer control through natural language voice commands.  
The assistant can automate system tasks such as application launch, web search, media control, brightness, volume, and real-time information retrieval.

---

## 🚀 Features

- 🎤 Speech recognition–based voice commands  
- 🔊 Text-to-speech responses (TTS)  
- 🤖 Gemini AI conversational integration  
- 💻 Desktop automation (apps, browser, media keys)  
- 🔆 Screen brightness control  
- 🔊 System volume control  
- 🔋 Battery status monitoring  
- ⏰ Time and date queries  
- 🌐 Web search automation  
- 🧵 Multithreaded background voice loop  
- 📡 Flask REST API + real-time web dashboard  

---

## 🏗️ Architecture

- **Backend:** Python + Flask REST API  
- **Voice Engine:** SpeechRecognition + pyttsx3  
- **AI Integration:** Google Gemini API  
- **Automation:** PyAutoGUI + OS commands  
- **System Control:** psutil + screen-brightness-control  
- **Frontend:** Embedded HTML/CSS dashboard  

The assistant runs a background listening loop while the Flask server provides control endpoints and UI synchronization.

---

## ⚙️ Installation

### 1️⃣ Clone repository
```bash
git clone https://github.com/yourusername/voice-assistant.git
cd voice-assistant
