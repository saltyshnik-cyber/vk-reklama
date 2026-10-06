// Netlify Function: принимает заявку с сайта и отправляет её в Telegram-бот.
// В настройках сайта на Netlify (Site configuration → Environment variables) добавьте:
//   TELEGRAM_BOT_TOKEN  — токен бота от @BotFather
//   TELEGRAM_CHAT_ID    — числовой ID вашего чата (узнать у @userinfobot)
// У переменных должна быть область действия Functions (по умолчанию включены все).
// Токен нельзя вставлять в index.html и нельзя присылать в чат.
//
// Диагностика: если открыть адрес функции в браузере (GET), она покажет только
// true/false, видит ли она переменные, сами значения не показываются.

exports.handler = async (event) => {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  const json = (code, obj) => ({
    statusCode: code,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
    body: JSON.stringify(obj),
  });

  if (event.httpMethod === 'GET') {
    return json(200, {
      ok: false,
      alive: true,
      tokenSet: !!token,
      chatIdSet: !!chatId,
      chatIdLooksLikeNumber: /^-?\d+$/.test(String(chatId || '').trim()),
    });
  }
  if (event.httpMethod !== 'POST') return json(405, { ok: false });

  let body = {};
  try { body = JSON.parse(event.body || '{}'); } catch (e) { /* пустое тело */ }

  const clean = (v, max) => String(v || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);
  const name = clean(body.name, 60);
  const phone = clean(body.phone, 20);
  const salon = clean(body.salon, 80);
  const page = clean(body.page, 200);

  if (name.length < 2 || !/^\+7\d{10}$/.test(phone)) {
    return json(400, { ok: false, error: 'invalid' });
  }
  if (!token || !chatId) {
    return json(500, { ok: false, error: 'not configured', tokenSet: !!token, chatIdSet: !!chatId });
  }

  const text = [
    'Новая заявка с сайта',
    'Имя: ' + name,
    'Телефон: ' + phone,
    salon ? 'Салон: ' + salon : null,
    body.promo === true ? 'Акция: да (запуск по акции)' : null,
    page ? 'Страница: ' + page : null,
  ].filter(Boolean).join('\n');

  try {
    const r = await fetch('https://api.telegram.org/bot' + String(token).trim() + '/sendMessage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: String(chatId).trim(), text, disable_web_page_preview: true }),
    });
    if (!r.ok) {
      let detail = '';
      try { const d = await r.json(); detail = String(d.description || '').slice(0, 120); } catch (e) { /* нет тела */ }
      return json(502, { ok: false, error: 'telegram', telegramStatus: r.status, detail });
    }
    return json(200, { ok: true });
  } catch (e) {
    return json(502, { ok: false, error: 'network' });
  }
};
