# DSP Telegram bot

Простой бот-каталог для оптового канала: меню, каталог из `products.json`, заявка менеджеру.

## Запуск
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # впишите BOT_TOKEN и MANAGER_CHAT_ID
python bot.py
```
Товары правятся в `products.json`. Токен никогда не коммитьте — `.env` в `.gitignore`.
