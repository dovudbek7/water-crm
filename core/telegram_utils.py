import json
import secrets
from urllib import error, parse, request

from django.conf import settings
from django.utils import timezone


def generate_telegram_token():
    return secrets.token_urlsafe(24)


def build_telegram_connect_link(token):
    if not settings.TELEGRAM_BOT_USERNAME:
        return ''
    return f'https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=connect_{token}'


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
    return (
        '<b>#buyurtma</b>\n'
        f"<b>Do'kon:</b> {order.shop.name}\n"
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
