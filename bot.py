import logging
import os
import threading
from aiogram import Bot, Dispatcher, executor, types
from twilio.rest import Client
from dotenv import load_dotenv
from flask import Flask, request

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
BASE_URL = os.getenv("BASE_URL")

# Telegram bot setup
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Twilio client
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

# Flask app for Twilio callbacks
app = Flask(__name__)

@app.route("/connect", methods=["POST"])
def connect():
    friend = request.args.get("friend")
    return f"""
        <Response>
            <Dial callerId="{TWILIO_NUMBER}">{friend}</Dial>
        </Response>
    """, 200, {"Content-Type": "text/xml"}


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("👋 Hi! Use /call <yourNumber> <friendNumber> to start a masked call.")


@dp.message_handler(commands=["call"])
async def call_command(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply("Usage: /call <yourNumber> <friendNumber>")
            return

        user_number, friend_number = parts[1], parts[2]

        call = twilio_client.calls.create(
            to=user_number,
            from_=TWILIO_NUMBER,
            url=f"{BASE_URL}/connect?friend={friend_number}"
        )

        await message.reply(f"📞 Calling {friend_number} via Twilio...\nCall SID: {call.sid}")

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run Flask server in separate thread
    def run_flask():
        app.run(host="0.0.0.0", port=5000)

    threading.Thread(target=run_flask, daemon=True).start()

    # Run Telegram bot
    executor.start_polling(dp, skip_updates=True)
