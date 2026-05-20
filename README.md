# Water CRM (Django)

Suv savdo boshqaruv tizimi.

## Ishga tushirish

1. Virtual muhit yarating:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. Migratsiyalarni qo'llang:
   ```bash
   python manage.py migrate
   ```
4. Super admin yarating:
   ```bash
   python manage.py createsuperuser
   ```
5. Serverni ishga tushiring:
   ```bash
   python manage.py runserver
   ```

## Auth qoidasi

- Ro'yxatdan o'tish yo'q.
- Foydalanuvchilar faqat Django Admin orqali yaratiladi.
- Tizimga kirish uchun foydalanuvchi `is_staff=True` bo'lishi kerak.
