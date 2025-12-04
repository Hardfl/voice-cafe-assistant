import os
import json
import wave
import tempfile
import time

import sounddevice as sd
from scipy.io.wavfile import write
from vosk import Model, KaldiRecognizer
import pyttsx3

# ===================== MENU DATA ===================== #

MENU = [
    # Coffees
    {
        "id": "classic_latte",
        "name": "Classic Latte",
        "type": "coffee",
        "description": "Smooth espresso with steamed milk.",
        "popularity": 75,
    },
    {
        "id": "caramel_latte",
        "name": "Caramel Latte",
        "type": "coffee",
        "description": "Latte with sweet caramel syrup.",
        "popularity": 95,  # fan favorite
    },
    {
        "id": "iced_mocha",
        "name": "Iced Mocha",
        "type": "coffee",
        "description": "Iced coffee with chocolate and milk.",
        "popularity": 80,
    },
    {
        "id": "americano",
        "name": "Americano",
        "type": "coffee",
        "description": "Espresso topped with hot water.",
        "popularity": 60,
    },
    {
        "id": "espresso_shot",
        "name": "Espresso Shot",
        "type": "coffee",
        "description": "Strong single shot of espresso.",
        "popularity": 65,
    },

    # Teas
    {
        "id": "english_breakfast",
        "name": "English Breakfast Tea",
        "type": "tea",
        "description": "Bold black tea, great with milk.",
        "popularity": 70,
    },
    {
        "id": "green_jasmine",
        "name": "Green Jasmine Tea",
        "type": "tea",
        "description": "Light green tea with jasmine aroma.",
        "popularity": 85,
    },
    {
        "id": "chai_latte",
        "name": "Chai Latte",
        "type": "tea",
        "description": "Spiced tea with steamed milk.",
        "popularity": 90,
    },
    {
        "id": "peppermint",
        "name": "Peppermint Tea",
        "type": "tea",
        "description": "Caffeine-free refreshing herbal tea.",
        "popularity": 65,
    },
    {
        "id": "iced_peach",
        "name": "Iced Peach Tea",
        "type": "tea",
        "description": "Sweet iced tea with peach flavour.",
        "popularity": 78,
    },
]


def get_menu_by_type(drink_type: str):
    return [d for d in MENU if d["type"] == drink_type]


def get_fan_favorite():
    return max(MENU, key=lambda d: d["popularity"])


def find_drink_in_text(text: str):
    """
    Try to match a drink from the MENU based on its name or keywords in the text.
    """
    t = text.lower()
    best_match = None

    # Try matching first 1–2 words of each drink name
    for d in MENU:
        name_words = d["name"].lower().split()
        if all(word in t for word in name_words[:2]):
            best_match = d
            break

    # Fallback keyword map for fuzzier matches
    if not best_match:
        keyword_map = {
            "caramel": "caramel_latte",
            "mocha": "iced_mocha",
            "americano": "americano",
            "espresso": "espresso_shot",
            "chai": "chai_latte",
            "peppermint": "peppermint",
            "peach": "iced_peach",
            "jasmine": "green_jasmine",
            "english": "english_breakfast",
            "breakfast": "english_breakfast",
            "latte": "classic_latte",
        }
        for word, drink_id in keyword_map.items():
            if word in t:
                for d in MENU:
                    if d["id"] == drink_id:
                        best_match = d
                        break
            if best_match:
                break

    return best_match


# ===================== VOSK MODEL PATH ===================== #

VOSK_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "vosk-model-en-us-0.22"  # <-- change this if your folder name is different
)

if not os.path.isdir(VOSK_MODEL_PATH):
    raise RuntimeError(
        f"Vosk model not found at {VOSK_MODEL_PATH}. "
        "Check the folder path and name."
    )

vosk_model = Model(VOSK_MODEL_PATH)

# ===================== TTS ENGINE ===================== #
# We will initialize a NEW engine inside speak() every time.
# This avoids the "first speak works, others are silent" bug.

def speak(text: str):
    """Offline text-to-speech for normal messages (re-init engine each call)."""
    print(f"[TTS] {text}")
    try:
        engine = pyttsx3.init(driverName='sapi5')  # explicit SAPI5 on Windows
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        # small pause so audio fully flushes out before next I/O
        time.sleep(0.05)
        print("[TTS] Finished speaking.")
    except Exception as e:
        print("TTS error:", e)


# ===================== AUDIO & STT ===================== #

def record_audio(seconds=4, fs=16000):
    """Record from microphone and save to a temporary WAV file."""
    print(f"\n[REC] Recording for {seconds} seconds... speak now.")
    recording = sd.rec(int(seconds * fs), samplerate=fs,
                       channels=1, dtype="int16")
    sd.wait()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    write(tmp.name, fs, recording)
    tmp.close()
    print(f"[REC] Saved temp audio to {tmp.name}")
    return tmp.name


def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using Vosk (offline)."""
    print(f"[STT] Transcribing {file_path} ...")
    wf = wave.open(file_path, "rb")

    if wf.getnchannels() != 1:
        raise ValueError("Audio must be mono (we record mono, so this should be fine).")

    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    pieces = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            pieces.append(res.get("text", ""))

    res = json.loads(rec.FinalResult())
    pieces.append(res.get("text", ""))

    wf.close()
    text = " ".join(pieces).strip()
    print(f"[STT] Final text: '{text}'")
    return text


# ===================== INTENT HELPERS ===================== #

def parse_size(text: str) -> str:
    t = text.lower()
    if "small" in t:
        return "small"
    if "large" in t or "big" in t:
        return "large"
    if "medium" in t or "regular" in t:
        return "medium"
    return "medium"


def detect_intent(text: str):
    """
    Detects what the user is asking:
      - 'menu_coffee'
      - 'menu_tea'
      - 'menu_all'
      - 'favorite'
      - 'order'
      - 'stop' (quit)
      - 'unknown'
    """
    t = text.lower()

    # explicit stop intent
    if any(word in t for word in ["quit", "exit", "stop listening", "stop"]):
        return "stop", {}

    # Menu questions
    if any(word in t for word in ["menu", "options", "flavors", "flavours", "drinks"]):
        if "coffee" in t:
            return "menu_coffee", {}
        if "tea" in t:
            return "menu_tea", {}
        return "menu_all", {}

    # Fan favorite / most popular
    if any(
        phrase in t
        for phrase in ["favorite", "favourite", "most popular", "best seller", "best drink"]
    ):
        return "favorite", {}

    # Order intent
    if any(word in t for word in ["order", "want", "get", "have"]) or "coffee" in t or "tea" in t:
        return "order", {}

    return "unknown", {}


def build_menu_text(drinks):
    names = [d["name"] for d in drinks]
    return "; ".join(names)


# ===================== MAIN LOOP ===================== #

def main():
    print("=== Offline Voice Cafe (Terminal Version) ===")
    print("You can ask things like:")
    print(" - 'What coffees are on the menu?'")
    print(" - 'What teas do you have?'")
    print(" - 'What's the most popular drink?'")
    print(" - 'I want to order a large caramel latte.'")
    print("\nType 'q' and press Enter to quit, or say 'stop' / 'quit' / 'exit' in your voice.\n")

    speak("Welcome to the voice enabled cafe. Ask about the menu or place an order.")

    while True:
        user = input("\nPress Enter to record, or type q to quit: ").strip().lower()
        if user == "q":
            reply = "Goodbye. Thanks for visiting the cafe."
            print("[BOT]", reply)
            speak(reply)
            input("Press Enter to close the cafe app...")
            print("Exiting...")
            break

        audio_path = record_audio()
        try:
            text = transcribe_audio(audio_path)
        except Exception as e:
            print("Transcription error:", e)
            speak("Sorry, something went wrong while understanding you. Please try again.")
            continue

        if not text:
            print("[STT] Didn't catch anything.")
            speak("Sorry, I didn't catch that. Try again.")
            continue

        print(f"[STT] Heard: {text}")

        intent, _ = detect_intent(text)
        print(f"[INTENT] Detected: {intent}")

        if intent == "stop":
            reply = "Okay, stopping now. Goodbye."
            print("[BOT]", reply)
            speak(reply)
            input("Press Enter to close the cafe app...")
            print("User requested stop. Exiting...")
            break

        if intent.startswith("menu"):
            if intent == "menu_coffee":
                drinks = get_menu_by_type("coffee")
                menu_text = build_menu_text(drinks)
                reply = (
                    "Our coffee menu includes: " + menu_text +
                    ". You can order any coffee in small, medium, or large size."
                )
            elif intent == "menu_tea":
                drinks = get_menu_by_type("tea")
                menu_text = build_menu_text(drinks)
                reply = (
                    "Our tea menu includes: " + menu_text +
                    ". Available sizes are small, medium, and large."
                )
            else:
                reply = (
                    "Here are all our drinks: " + build_menu_text(MENU) +
                    ". You can order drinks in small, medium, or large sizes."
                )

            print("[BOT]", reply)
            speak(reply)
            continue

        if intent == "favorite":
            fav = get_fan_favorite()
            reply = f"Our fan favorite is the {fav['name']}. {fav['description']}"
            print("[BOT]", reply)
            speak(reply)
            continue

        if intent == "order":
            drink = find_drink_in_text(text)
            if not drink:
                reply = (
                    "I heard you want to order, but I couldn't find a drink name. "
                    "Try saying something like 'I want a large caramel latte' or "
                    "'Can I get an iced peach tea?'."
                )
                print("[BOT]", reply)
                speak(reply)
                continue

            # Check if user mentioned a size; if not, ask and listen again
            lower_t = text.lower()
            size_words_present = any(
                s in lower_t for s in ["small", "medium", "regular", "large", "big"]
            )

            if not size_words_present:
                ask = "What size would you like? Small, medium, or large?"
                print("[BOT]", ask)
                speak(ask)

                size_audio = record_audio(seconds=3)
                size_text = transcribe_audio(size_audio)
                print(f"[STT size] Heard: {size_text}")

                if not size_text:
                    size = "medium"
                    info = "I didn't catch a size clearly, so I'll make it medium."
                    print("[BOT]", info)
                    speak(info)
                else:
                    size = parse_size(size_text)
            else:
                size = parse_size(text)

            reply = f"Placing an order for a {size} {drink['name']}."
            print("[BOT]", reply)
            speak(reply)
            print("[ORDER] Size:", size, "| Drink:", drink["name"])
            continue

        # Unknown
        reply = (
            "I didn't understand that. "
            "You can ask about the menu, ask for the fan favorite, "
            "or say you want to order a specific drink."
        )
        print("[BOT]", reply)
        speak(reply)


if __name__ == "__main__":
    main()
