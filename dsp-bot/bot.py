import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
MANAGER_CHAT_ID = int(os.environ["MANAGER_CHAT_ID"]) if os.getenv("MANAGER_CHAT_ID") else None
PRODUCTS = {p["id"]: p for p in json.loads(Path(__file__).with_name("products.json").read_text("utf-8"))}

CONTACTS = ("🏬 ТК «Южные ворота»\nЛиния Ж8, павильон 18-20\n"
            "🚚 Доставка по всем регионам РФ\n🇨🇳 Прямые поставки из Китая")

dp = Dispatcher()


class Order(StatesGroup):
    qty = State()
    name = State()
    phone = State()


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📦 Каталог"), KeyboardButton(text="📍 Контакты")]],
        resize_keyboard=True)


def catalog_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']}₽", callback_data=f"p:{p['id']}")]
        for p in PRODUCTS.values()])


@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Здравствуйте! Мы — официальные дистрибьюторы DSP-JAMAKY.\n"
                   "Оптовые цены, прямые поставки. Выберите раздел 👇", reply_markup=main_menu())


@dp.message(F.text == "📦 Каталог")
async def catalog(m: Message):
    await m.answer("Каталог:", reply_markup=catalog_kb())


@dp.message(F.text == "📍 Контакты")
async def contacts(m: Message):
    await m.answer(CONTACTS)


@dp.callback_query(F.data.startswith("p:"))
async def product(c: CallbackQuery):
    p = PRODUCTS[c.data[2:]]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🛒 Оставить заявку", callback_data=f"o:{p['id']}")]])
    await c.message.answer(f"*{p['name']}*\nЦена: {p['price']}₽\n{p['pack']}\n\n{p['desc']}",
                           parse_mode="Markdown", reply_markup=kb)
    await c.answer()


@dp.callback_query(F.data.startswith("o:"))
async def order_start(c: CallbackQuery, state: FSMContext):
    await state.update_data(pid=c.data[2:])
    await state.set_state(Order.qty)
    await c.message.answer("Сколько коробок нужно? (число)")
    await c.answer()


@dp.message(Order.qty)
async def order_qty(m: Message, state: FSMContext):
    if not (m.text or "").isdigit() or int(m.text) < 1:
        return await m.answer("Введите число, например 5")
    await state.update_data(qty=int(m.text))
    await state.set_state(Order.name)
    await m.answer("Как к вам обращаться?")


@dp.message(Order.name)
async def order_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await state.set_state(Order.phone)
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
                             resize_keyboard=True, one_time_keyboard=True)
    await m.answer("Телефон для связи (или нажмите кнопку):", reply_markup=kb)


@dp.message(Order.phone)
async def order_phone(m: Message, state: FSMContext, bot: Bot):
    phone = m.contact.phone_number if m.contact else m.text
    d = await state.get_data()
    p = PRODUCTS[d["pid"]]
    text = (f"🆕 Новая заявка\nТовар: {p['name']}\nКоробок: {d['qty']}\n"
            f"Клиент: {d['name']}\nТел: {phone}\nTelegram: @{m.from_user.username or m.from_user.id}")
    if MANAGER_CHAT_ID:
        await bot.send_message(MANAGER_CHAT_ID, text)
    else:
        logging.warning("MANAGER_CHAT_ID не задан, заявка:\n%s", text)
    await state.clear()
    await m.answer("Спасибо! Менеджер свяжется с вами в ближайшее время.", reply_markup=main_menu())


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(Bot(BOT_TOKEN))


if __name__ == "__main__":
    asyncio.run(main())
