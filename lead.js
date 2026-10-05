// Netlify Function: принимает заявку с сайта и отправляет её в Telegram-бот.
// В настройках сайта на Netlify (Site configuration → Environment variables) добавьте:
//   TELEGRAM_BOT_TOKEN  — токен бота от @BotFather
//   TELEGRAM_CHAT_ID    — ID чата, куда слать заявки
// Токен нельзя вставлять в index.html и нельзя присылать в чат.

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ ok: false }) };
  }

  let body = {};
  try { body = JSON.parse(event.body || '{}'); } catch (e) { /* пустое тело */ }

  const clean = (v, max) => String(v || '').replace(/[\u0000-\u001f]/g, ' ').trim().slice(0, max);
  const name = clean(body.name, 60);
  const phone = clean(body.phone, 20);
  const salon = clean(body.salon, 80);
  const page = clean(body.page, 200);

  if (name.length < 2 || !/^\+7\d{10}$/.test(phone)) {
    return { statusCode: 400, body: JSON.stringify({ ok: false, error: 'invalid' }) };
  }

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!token || !chatId) {
    return { statusCode: 500, body: JSON.stringify({ ok: false, error: 'not configured' }) };
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
    const r = await fetch('https://api.telegram.org/bot' + token + '/sendMessage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text, disable_web_page_preview: true }),
    });
    if (!r.ok) throw new Error('telegram error');
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  } catch (e) {
    return { statusCode: 502, body: JSON.stringify({ ok: false }) };
  }
};
