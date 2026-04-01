# teaandcoffee_management

Offline Tea & Coffee Management System with Voice Ordering.

This project is a small cafe-style ordering system where a user can:
- Ask what coffees are on the menu
- Ask what teas are on the menu
- Ask which drink is the most popular / fan favorite
- Place an order by voice (e.g., “I want to order a large caramel latte”)

All of this runs **offline** using:

- **Vosk** – speech-to-text (STT) running locally with an English model  
- **pyttsx3** – text-to-speech (TTS) using the system voices  
- **Python** – to manage the menu, detect intents, and handle orders in the terminal

## Features

- 11 drink menu:
  - 5 coffees (Classic Latte, Caramel Latte, Iced Mocha, Americano, Espresso Shot)
  - 6 teas (English Breakfast, Hibiscus Rose-Tea, Chai Latte, Peppermint, Iced Peach Tea, Iced Matcha Latte)
- Voice intents:
  - “What coffees are on the menu?”
  - “What teas do you have?”
  - “What’s the most popular drink?”
  - “I want to order a large caramel latte.”
- Simple order print-out in the terminal:
  - Shows the drink and size, e.g. `Size: large | Drink: Caramel Latte`
- Quit options:
  - Type `q` in the terminal
  - Or say “stop”, “quit”, or “exit” to end the session

## How to Run (local)

1. Clone this repo and enter the folder:

   ```bash
   git clone https://github.com/Hardfl/voice-cafe-assistant.git
   cd voice-cafe-assistant
