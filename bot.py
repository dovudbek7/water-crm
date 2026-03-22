import json
import logging
import os
import time
from urllib import error, parse, request

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
BOT_SECRET = os.getenv('TELEGRAM_BOT_SECRET', '').strip()
MINI_APP_URL = os.getenv('TELEGRAM_MINI_APP_URL', '').strip()

API_BASE = f'https://api.telegram.org/bot{BOT_TOKEN}'


def _site_base_url():
    base = MINI_APP_URL.rstrip('/')
    if base.endswith('/telegram-mini-app'):
        base = base[: -len('/telegram-mini-app')]
    return base


def telegram_api(method, payload=None, request_timeout=40):
    url = f'{API_BASE}/{method}'
    data = None
    if payload is not None:
        data = parse.urlencode(payload).encode()
    req = request.Request(url, data=data, method='POST' if data is not None else 'GET')
    with request.urlopen(req, timeout=request_timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def send_message(chat_id, text, reply_markup=None):
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true',
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    return telegram_api('sendMessage', payload, request_timeout=20)


def _confirm_connect(token, chat_id, username):
    base_url = _site_base_url()
    if not base_url:
        return False, "TELEGRAM_MINI_APP_URL sozlanmagan."

    url = f"{base_url}/telegram/connect/{token}/confirm/"
    payload = parse.urlencode({'chat_id': chat_id, 'username': username or ''}).encode()
    headers = {}
    if BOT_SECRET:
        headers['X-Telegram-Secret'] = BOT_SECRET
    req = request.Request(url, data=payload, headers=headers, method='POST')
    try:
        with request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return bool(data.get('ok')), data.get('message', 'Akkaunt ulandi.')
    except error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode('utf-8'))
            return False, body.get('message', "Ulashda xatolik yuz berdi.")
        except Exception:
            return False, f"Backend xatoligi: {exc.code}"
    except (error.URLError, TimeoutError, ValueError):
        return False, "Backend bilan aloqa qilib bo'lmadi."


def _main_keyboard():
    if not MINI_APP_URL:
        return None
    return {
        'inline_keyboard': [
            [
                {
                    'text': 'Mini Appni ochish',
                    'web_app': {'url': MINI_APP_URL},
                }
            ]
        ]
    }


def _extract_text(message):
    return (message.get('text') or '').strip()


def _handle_start(message):
    chat_id = message['chat']['id']
    user = message.get('from', {})
    text = _extract_text(message)
    parts = text.split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ''

    if payload.startswith('connect_'):
        token = payload.replace('connect_', '', 1).strip()
        ok, msg = _confirm_connect(token, str(chat_id), user.get('username', ''))
        if ok:
            send_message(
                chat_id,
                "Akkaunt muvaffaqiyatli ulandi.\nEndi Telegram orqali tizimdan foydalanishingiz mumkin.",
                reply_markup=_main_keyboard(),
            )
        else:
            send_message(chat_id, msg)
        return

    send_message(
        chat_id,
        "Suv Savdo Tizimi botiga xush kelibsiz.\n"
        "Akkauntni ulash uchun saytdagi `Telegram ulash` tugmasini bosing.\n"
        "Akkaunt ulangan bo'lsa, quyidagi tugma orqali Mini Appni ochishingiz mumkin.",
        reply_markup=_main_keyboard(),
    )


def _handle_miniapp(message):
    chat_id = message['chat']['id']
    markup = _main_keyboard()
    if not markup:
        send_message(chat_id, "Mini App havolasi sozlanmagan.")
        return
    send_message(chat_id, "Mini Appni ochish uchun tugmani bosing.", reply_markup=markup)


def handle_update(update):
    message = update.get('message')
    if not message:
        return

    text = _extract_text(message)
    if text.startswith('/start'):
        _handle_start(message)
    elif text.startswith('/miniapp'):
        _handle_miniapp(message)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN .env faylida sozlanmagan.")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    try:
        telegram_api('deleteWebhook', request_timeout=15)
    except Exception:
        logging.warning('Webhook o‘chirilmadi, davom etyapman.')

    offset = None
    logging.info('Bot polling boshlandi.')

    while True:
        try:
            params = {'timeout': 25}
            if offset is not None:
                params['offset'] = offset
            response = telegram_api('getUpdates', params, request_timeout=35)
            for update in response.get('result', []):
                offset = update['update_id'] + 1
                handle_update(update)
        except KeyboardInterrupt:
            logging.info('Bot to‘xtatildi.')
            break
        except Exception as exc:
            logging.exception('Bot xatoligi: %s', exc)
            time.sleep(3)


if __name__ == '__main__':
    main()
