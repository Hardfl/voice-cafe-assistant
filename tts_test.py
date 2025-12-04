import pyttsx3

engine = pyttsx3.init()

# Optional: tweak these so it's clearly audible
engine.setProperty("rate", 170)   # speaking speed
engine.setProperty("volume", 1.0) # max volume

voices = engine.getProperty("voices")
print("Available voices:")
for i, v in enumerate(voices):
    print(i, v.id)

if voices:
    engine.setProperty("voice", voices[0].id)  # pick the first voice

engine.say("This is a test of text to speech for the tea and coffee project.")
engine.runAndWait()
