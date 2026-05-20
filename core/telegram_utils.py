import json
import secrets
import hashlib
import hmac
from urllib import error, parse, request

from django.conf import settings
from django.utils import timezone


def generate_telegram_token():
    return secrets.token_urlsafe(24)


def build_telegram_connect_link(token):
    if not settings.TELEGRAM_BOT_USERNAME:
        return ''
    return f'https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=connect_{token}'


def validate_telegram_init_data(init_data):
    if not init_data or not settings.TELEGRAM_BOT_TOKEN:
        return False, {}

    parsed = dict(parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop('hash', '')
    if not received_hash:
        return False, {}

    data_check_string = '\n'.join(f'{key}={parsed[key]}' for key in sorted(parsed.keys()))
    secret_key = hmac.new(b'WebAppData', settings.TELEGRAM_BOT_TOKEN.encode('utf-8'), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        return False, {}
    return True, parsed


def send_telegram_channel_message(text):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHANNEL_ID:
        return False

    payload = parse.urlencode(
        {
            'chat_id': settings.TELEGRAM_CHANNEL_ID,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'true',
        }
    ).encode()
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage'
    req = request.Request(url, data=payload, method='POST')
    try:
        with request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode('utf-8'))
            return bool(data.get('ok'))
    except (error.URLError, TimeoutError, ValueError):
        return False


def format_order_created_message(order):
    items = ''.join(
        f'\n- {item.product.name}: {item.quantity} dona'
        for item in order.items.select_related('product')
    )
    phone = order.shop.phone_primary or order.shop.phone_secondary or '-'
    address = order.shop.address or '-'
    return (
        '<b>#buyurtma</b>\n'
        f"<b>Do'kon:</b> {order.shop.name}\n"
        f'<b>Telefon:</b> {phone}\n'
        f'<b>Manzil:</b> {address}\n'
        f'<b>Sana:</b> {order.order_date:%d.%m.%Y}\n'
        f"<b>Jami:</b> {order.total_amount:,.0f} so'm\n"
        f'<b>Mahsulotlar:</b>{items or "-"}'
    )


def format_order_delivered_message(order, courier_name):
    when = timezone.localtime(order.delivered_at).strftime('%d.%m.%Y %H:%M') if order.delivered_at else '-'
    received = order.delivery_received_amount or order.paid_amount
    return (
        '<b>#yetkazildi</b>\n'
        f"<b>Do'kon:</b> {order.shop.name}\n"
        f'<b>Kuryer:</b> {courier_name}\n'
        f'<b>Vaqt:</b> {when}\n'
        f"<b>Qabul qilingan summa:</b> {received:,.0f} so'm"
    )


def format_order_closed_message(order):
    return (
        '<b>#yopiq</b>\n'
        f"<b>Do'kon:</b> {order.shop.name}\n"
        f'<b>Vaqt:</b> {timezone.localtime(timezone.now()):%d.%m.%Y %H:%M}\n'
        f"<b>Buyurtma:</b> #{order.id}"
    )
