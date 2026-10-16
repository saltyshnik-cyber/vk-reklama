"""Webhook Telegram-бота: приветствие, кнопка «Открыть магазин», контакты менеджеров."""
import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, MenuButtonWebApp,
                           Message, ReplyKeyboardMarkup, Update, WebAppInfo)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://dsp-bot.vercel.app")

CONTACTS = ("🏬 Москва, ТК «Южные ворота»\n8 линия (Ж8), павильон 18-20\n"
            "🚚 Доставка по всем регионам РФ\n🇨🇳 Прямые поставки из Китая")
MANAGERS = ("Менеджеры:\n"
            "Ислам — +7 925 451-06-00, https://t.me/IslamDsp\n"
            "Рахим — +7 925 381-57-55, https://t.me/mnvrkk\n"
            "Алим — +7 925 257-66-26, https://t.me/Alimdsp")

dp = Dispatcher()


def main_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Контакты"), KeyboardButton(text="📞 Менеджеры")]],
                               resize_keyboard=True)


@dp.message(CommandStart())
async def start(m: Message, bot: Bot):
    await bot.set_chat_menu_button(m.chat.id, MenuButtonWebApp(text="Каталог", web_app=WebAppInfo(url=WEBAPP_URL)))
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🛍 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await m.answer("Здравствуйте! Мы — официальные дистрибьюторы DSP-JAMAKY.\n"
                   "Бытовая техника оптом, прямые поставки из Китая. Откройте каталог 👇", reply_markup=kb)
    await m.answer("Контакты и менеджеры — в меню ниже.", reply_markup=main_menu())


@dp.message(F.text == "📍 Контакты")
async def contacts(m: Message):
    await m.answer(CONTACTS)


@dp.message(F.text == "📞 Менеджеры")
async def managers(m: Message):
    await m.answer(MANAGERS, disable_web_page_preview=True)


async def process(data: dict):
    bot = Bot(BOT_TOKEN)
    try:
        await dp.feed_update(bot, Update.model_validate(data, context={"bot": bot}))
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DSP bot is running")

    def do_POST(self):
        if WEBHOOK_SECRET and self.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            self.send_response(403)
            self.end_headers()
            return
        body = self.rfile.read(int(self.headers.get("content-length", 0)))
        try:
            asyncio.run(process(json.loads(body)))
        except Exception as e:  # всегда 200, иначе Telegram будет слать повторно
            print("error:", repr(e))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
