"""
Har bir bo'limga 10 tadan sinov (mock) ma'lumot qo'shadi.
Ishlatish: python add_mock_data.py

Qo'shiladi:
  - 10 ta mahsulot
  - 10 ta do'kon (regionlar bo'yicha)
  - 10 ta xodim (user bilan birga)
  - 10 ta buyurtma (har biriga 2-3 ta element)
  - 10 ta depozit
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import (
    ActionLog, Employee, Order, OrderItem, Product, Region, Shop, ShopDeposit
)

User = get_user_model()


# ─── 1. Mahsulotlar ────────────────────────────────────────────────────────────
PRODUCTS = [
    ("19L Идиш (Замзам)", 8_000),
    ("19L Идиш (Aqua Blue)", 7_500),
    ("5L Шиша", 4_000),
    ("1.5L Шиша", 2_500),
    ("0.5L Шиша", 1_500),
    ("Помпа (электр)", 120_000),
    ("Помпа (механик)", 45_000),
    ("Идиш қопқоғи (10 та)", 5_000),
    ("Фильтр катриджи", 85_000),
    ("Диспенсер (иссиқ/совуқ)", 950_000),
]

# ─── 2. Do'konlar ──────────────────────────────────────────────────────────────
SHOPS = [
    ("Supermarket «Bahor»",     "Тошкент вил. — Янгийўл тумани",  "+998 90-123-45-67", "+998 91-234-56-78"),
    ("Magazin «Nur»",           "Тошкент ш. — Юнусобод тумани",   "+998 93-456-78-90", ""),
    ("Do'kon «Hamkor»",         "Андижон вил. — Андижон шаҳри",   "+998 94-567-89-01", "+998 90-678-90-12"),
    ("Supermarket «Savdo»",     "Фарғона вил. — Фарғона шаҳри",   "+998 97-789-01-23", ""),
    ("Magazin «Aziz»",          "Самарқанд вил. — Самарқанд шаҳри","+998 99-890-12-34", "+998 93-901-23-45"),
    ("Do'kon «Baraka»",         "Наманган вил. — Наманган шаҳри",  "+998 91-012-34-56", ""),
    ("Supermarket «Oltin»",     "Бухоро вил. — Бухоро шаҳри",     "+998 90-123-56-78", "+998 94-234-67-89"),
    ("Magazin «Mehr»",          "Қашқадарё вил. — Қарши шаҳри",   "+998 93-345-78-90", ""),
    ("Do'kon «Shifo»",          "Хоразм вил. — Урганч шаҳри",     "+998 97-456-89-01", "+998 99-567-90-12"),
    ("Supermarket «Farovon»",   "Сурхондарё вил. — Термиз шаҳри", "+998 91-678-01-23", ""),
]

# ─── 3. Xodimlar ───────────────────────────────────────────────────────────────
EMPLOYEES = [
    ("Алишер",   "Каримов",   "+998 90-111-22-33", Employee.ROLE_COURIER),
    ("Бобур",    "Тошматов",  "+998 91-222-33-44", Employee.ROLE_WORKER),
    ("Дилшод",   "Юсупов",    "+998 93-333-44-55", Employee.ROLE_FILLER),
    ("Фарруx",   "Рaҳимов",   "+998 94-444-55-66", Employee.ROLE_ORDER_TAKER),
    ("Жамшид",   "Холматов",  "+998 97-555-66-77", Employee.ROLE_COURIER),
    ("Шерзод",   "Норматов",  "+998 99-666-77-88", Employee.ROLE_WORKER),
    ("Одил",     "Ҳасанов",   "+998 90-777-88-99", Employee.ROLE_FILLER),
    ("Мирзоҳид", "Бобоев",    "+998 91-888-99-00", Employee.ROLE_COURIER),
    ("Санжар",   "Эргашев",   "+998 93-999-00-11", Employee.ROLE_ORDER_TAKER),
    ("Улуғбек",  "Мирзаев",   "+998 94-000-11-22", Employee.ROLE_WORKER),
]


def create_products():
    print("\n📦 Mahsulotlar qo'shilmoqda...")
    created = 0
    for name, price in PRODUCTS:
        obj, is_new = Product.objects.get_or_create(
            name=name, defaults={'price': Decimal(price)}
        )
        if is_new:
            created += 1
            print(f"  + {name}")
        else:
            print(f"  - mavjud: {name}")
    print(f"  Yaratildi: {created}")
    return list(Product.objects.all()[:10])


def create_shops(products):
    print("\n🏪 Do'konlar qo'shilmoqda...")
    created = 0
    for name, region_name, phone1, phone2 in SHOPS:
        region = Region.objects.filter(name=region_name).first()
        obj, is_new = Shop.objects.get_or_create(
            name=name,
            defaults={
                'region': region,
                'address': f"{region_name}dagi {name}",
                'phone_primary': phone1,
                'phone_secondary': phone2,
                'note': f"{name} — sinov ma'lumoti",
            }
        )
        if is_new:
            created += 1
            print(f"  + {name}")
        else:
            print(f"  - mavjud: {name}")
    print(f"  Yaratildi: {created}")
    return list(Shop.objects.all()[:10])


def create_employees():
    print("\n👷 Xodimlar qo'shilmoqda...")
    created = 0
    employee_list = []
    for first, last, phone, role in EMPLOYEES:
        username_base = f"{first.lower()}.{last.lower()}"
        username = username_base
        idx = 1
        while User.objects.filter(username=username).exists():
            idx += 1
            username = f"{username_base}{idx}"

        if Employee.objects.filter(phone_primary=phone).exists():
            emp = Employee.objects.get(phone_primary=phone)
            print(f"  - mavjud: {first} {last}")
            employee_list.append(emp)
            continue

        user = User.objects.create_user(
            username=username,
            password='test1234',
            first_name=first,
            last_name=last,
            is_staff=False,
        )
        emp = Employee.objects.create(
            user=user,
            phone_primary=phone,
            role=role,
        )
        created += 1
        employee_list.append(emp)
        print(f"  + {first} {last} ({role}), parol: test1234")
    print(f"  Yaratildi: {created}")
    return employee_list


def create_orders(shops, products, employees):
    print("\n🛒 Buyurtmalar qo'shilmoqda...")
    from django.utils import timezone
    import datetime

    created = 0
    couriers = [e for e in employees if e.role == Employee.ROLE_COURIER]
    order_takers = [e for e in employees if e.role == Employee.ROLE_ORDER_TAKER]

    ORDER_DATA = [
        (0, 'pickup',   25_000,  0,     'new'),
        (1, 'delivery', 48_000,  48_000,'delivered'),
        (2, 'pickup',   32_000,  20_000,'new'),
        (3, 'delivery', 56_000,  56_000,'closed'),
        (4, 'pickup',   18_000,  18_000,'new'),
        (5, 'delivery', 72_000,  50_000,'delivered'),
        (6, 'pickup',   41_000,  0,     'new'),
        (7, 'delivery', 29_000,  29_000,'new'),
        (8, 'pickup',   63_000,  40_000,'new'),
        (9, 'delivery', 38_000,  38_000,'closed'),
    ]

    order_list = []
    for idx, (shop_idx, otype, paid, received, dstatus) in enumerate(ORDER_DATA):
        shop = shops[shop_idx % len(shops)]
        days_ago = idx * 3
        order_date = timezone.localdate() - datetime.timedelta(days=days_ago)

        creator = order_takers[idx % len(order_takers)] if order_takers else None
        courier = couriers[idx % len(couriers)] if otype == 'delivery' and couriers else None

        order = Order.objects.create(
            shop=shop,
            order_type=otype,
            order_date=order_date,
            paid_amount=Decimal(paid),
            delivery_status=dstatus,
            note=f"Sinov buyurtma #{idx+1}",
            created_by=creator.user if creator else None,
            courier=courier.user if courier else None,
        )

        # 2 ta mahsulot qo'shamiz
        for i in range(2):
            prod = products[(idx + i) % len(products)]
            qty = (i + 1) * 2
            OrderItem.objects.create(
                order=order,
                product=prod,
                quantity=qty,
                price_at_sale=prod.price,
            )

        created += 1
        order_list.append(order)
        print(f"  + Buyurtma #{order.id} — {shop.name}")
    print(f"  Yaratildi: {created}")
    return order_list


def create_deposits(shops):
    print("\n💰 Depozitlar qo'shilmoqda...")
    import datetime
    from django.utils import timezone

    AMOUNTS = [50_000, 100_000, 75_000, 30_000, 120_000,
               45_000, 200_000, 60_000, 90_000, 150_000]

    created = 0
    for i, (shop, amount) in enumerate(zip(shops, AMOUNTS)):
        days_ago = i * 4
        dep_date = timezone.localdate() - datetime.timedelta(days=days_ago)
        ShopDeposit.objects.create(
            shop=shop,
            date=dep_date,
            amount=Decimal(amount),
            note=f"Sinov depozit #{i+1}",
        )
        created += 1
        print(f"  + {shop.name} — {amount:,} so'm")
    print(f"  Yaratildi: {created}")


def run():
    print("=" * 55)
    print("  Mock data qo'shish boshlandi")
    print("=" * 55)

    products = create_products()
    shops = create_shops(products)
    employees = create_employees()
    create_orders(shops, products, employees)
    create_deposits(shops)

    print("\n" + "=" * 55)
    print("  Yakuniy statistika:")
    print(f"  📦 Mahsulotlar:  {Product.objects.count()} ta")
    print(f"  🏪 Do'konlar:    {Shop.objects.count()} ta")
    print(f"  👷 Xodimlar:     {Employee.objects.count()} ta")
    print(f"  🛒 Buyurtmalar:  {Order.objects.count()} ta")
    print(f"  💰 Depozitlar:   {ShopDeposit.objects.count()} ta")
    print("=" * 55)
    print("  Barcha xodimlarning paroli: test1234")
    print("=" * 55)


if __name__ == '__main__':
    run()
