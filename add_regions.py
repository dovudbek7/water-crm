"""
Barcha mavjud regionlarni o'chirib, faqat Andijon viloyati
tumanlarini qo'shadi.
Ishlatish: python add_regions.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Region

ANDIJON_REGIONS = [
    "Андижон шаҳри",
    "Андижон тумани",
    "Асака тумани",
    "Балиқчи тумани",
    "Бўз тумани",
    "Жалолқудуқ тумани",
    "Избоскан тумани",
    "Қўрғонтепа тумани",
    "Марҳамат тумани",
    "Олтинкўл тумани",
    "Пахтаобод тумани",
    "Шаҳрихон тумани",
    "Улуғнор тумани",
    "Хўжаобод тумани",
]


def run():
    before = Region.objects.count()
    Region.objects.all().delete()
    print(f"  Ўчирилди: {before} та эски регион")

    for name in ANDIJON_REGIONS:
        Region.objects.create(name=name)
        print(f"  + {name}")

    print(f"\n✓ Жами қўшилди: {Region.objects.count()} та регион (Андижон вилояти)")


if __name__ == '__main__':
    run()
