# bot/main.py
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os

# Load config
BOT_TOKEN = os.getenv("BOT_TOKEN", "5975058740:AAEE7HBv0koieZUSk9Su8wFNAWK4W2-65tI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002228131301") 
MINI_APP_URL = os.getenv("MINI_APP_URL", "https://your-vercel-app.vercel.app")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Command to send navigation post
@dp.message(Command("post"))
async def send_channel_post(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔍 Open Navigation",
            web_app=types.WebAppInfo(url=MINI_APP_URL)
        )]
    ])
    
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="📌 Browse our channel posts by category:",
            reply_markup=keyboard
        )
        await message.answer("✅ Post sent to channel!")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())