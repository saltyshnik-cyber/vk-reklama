"""Приём заявки с сайта и из мини-приложения Telegram. Суммы считаются на сервере по products.json."""
import asyncio
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qsl

from aiogram import Bot

DATA = json.loads((Path(__file__).parent.parent / "products.json").read_text("utf-8"))
PRODUCTS = {p["id"]: p for p in DATA["items"]}


def check_init_data(init_data: str, token: str):
    """Возвращает пользователя Telegram, если подпись initData верна, иначе None."""
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    got = data.pop("hash", "")
    s = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    if not got or not hmac.compare_digest(hmac.new(key, s.encode(), hashlib.sha256).hexdigest(), got):
        return None
    return json.loads(data.get("user", "{}"))


def rub(n: int) -> str:
    return f"{n:,}".replace(",", " ") + "₽"


async def send(user, body):
    token = os.environ["BOT_TOKEN"]
    items = body.get("items") or []
    if not items or len(items) > 100:
        raise ValueError("items")
    lines, total, boxes, pcs = [], 0, 0, 0
    for it in items:
        p, q = PRODUCTS[it["id"]], int(it["qty"])
        if q < 1 or q > 9999:
            raise ValueError("qty")
        s = p["p"] * p["k"] * q
        lines.append(f"• {p['n']} {p['m']} × {q} кор. ({q * p['k']} шт) = {rub(s)}")
        total, boxes, pcs = total + s, boxes + q, pcs + q * p["k"]
    name = str(body.get("name", "")).strip()[:100]
    phone = str(body.get("phone", "")).strip()[:40]
    comment = str(body.get("comment", "")).strip()[:500]
    if not name or sum(c.isdigit() for c in phone) < 10:
        raise ValueError("contact")
    if user:
        who = f"@{user['username']}" if user.get("username") else f"id {user['id']}"
        src = f"мини-приложение Telegram ({who})"
    else:
        src = "сайт"
    text = (f"🆕 Новая заявка ({src})\n" + "\n".join(lines) +
            f"\n\nИтого: {boxes} кор., {pcs} шт, {rub(total)}\nКлиент: {name}\nТел: {phone}" +
            (f"\nКомментарий: {comment}" if comment else ""))
    bot = Bot(token)
    try:
        if os.environ.get("MANAGER_CHAT_ID"):
            await bot.send_message(int(os.environ["MANAGER_CHAT_ID"]), text)
        if user:
            await bot.send_message(user["id"], "Спасибо! Заявка принята, менеджер свяжется с вами.\n\n"
                                   + "\n".join(lines) + f"\n\nИтого: {rub(total)}")
    finally:
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def _r(self, code):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(b"ok" if code == 200 else b"error")

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
            if body.get("website"):  # ловушка для ботов: поле скрыто от людей
                return self._r(200)
            user = None
            if body.get("initData"):
                user = check_init_data(body["initData"], os.environ["BOT_TOKEN"])
                if not user:
                    return self._r(403)
            asyncio.run(send(user, body))
            self._r(200)
        except Exception as e:
            print("order error:", repr(e))
            self._r(400)
