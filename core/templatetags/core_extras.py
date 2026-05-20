from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def som(value):
    if value is None:
        value = Decimal('0')

    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return "0 so'm"

    rounded = amount.quantize(Decimal('0.01'))
    formatted = f'{rounded:,.2f}'
    if formatted.endswith('.00'):
        formatted = formatted[:-3]
    return f"{formatted} so'm"


@register.filter
def comma(value):
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value


def _to_decimal(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return Decimal('0')


def _currency_abs(amount: Decimal):
    rounded = abs(amount).quantize(Decimal('0.01'))
    formatted = f'{rounded:,.2f}'
    if formatted.endswith('.00'):
        formatted = formatted[:-3]
    return f"{formatted} so'm"


@register.filter
def signed_som(value):
    amount = _to_decimal(value)
    sign = '+' if amount > 0 else ''
    if amount < 0:
        sign = '-'
    if amount == 0:
        sign = ''
    return f"{sign}{_currency_abs(amount)}"


@register.filter
def order_balance_label(value):
    amount = _to_decimal(value)
    # remaining_balance > 0 => debt
    if amount > 0:
        return f"-{_currency_abs(amount)}"
    if amount < 0:
        return f"+{_currency_abs(amount)}"
    return "0 so'm"


@register.filter
def order_balance_class(value):
    amount = _to_decimal(value)
    if amount > 0:
        return 'balance-down'
    if amount < 0:
        return 'balance-up'
    return 'balance-neutral'


@register.filter
def order_balance_icon(value):
    amount = _to_decimal(value)
    if amount > 0:
        return '↓'
    if amount < 0:
        return '↑'
    return '•'


@register.filter
def shop_balance_label(value):
    amount = _to_decimal(value)
    # shop.balance < 0 => debt
    if amount < 0:
        return f"-{_currency_abs(amount)}"
    if amount > 0:
        return f"+{_currency_abs(amount)}"
    return "0 so'm"


@register.filter
def shop_balance_class(value):
    amount = _to_decimal(value)
    if amount < 0:
        return 'balance-down'
    if amount > 0:
        return 'balance-up'
    return 'balance-neutral'


@register.filter
def shop_balance_icon(value):
    amount = _to_decimal(value)
    if amount < 0:
        return '↓'
    if amount > 0:
        return '↑'
    return '•'
