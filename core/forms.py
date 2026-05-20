import re

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.forms import formset_factory

from core.models import Employee, Order, Product, Shop, ShopDeposit, UserProfile


PHONE_RE = re.compile(r'\D')


def normalize_uz_phone(value):
    if not value:
        return ''

    digits = PHONE_RE.sub('', value)

    if digits.startswith('998'):
        digits = digits[3:]
    if len(digits) == 9:
        pass
    elif len(digits) > 9:
        digits = digits[-9:]
    else:
        return value

    return f'+998 {digits[0:2]}-{digits[2:5]}-{digits[5:7]}-{digits[7:9]}'


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Telefon raqam',
        max_length=25,
        widget=forms.TextInput(attrs={'placeholder': '+998 90-123-45-67', 'class': 'phone-input'}),
    )
    password = forms.CharField(label='Parol', widget=forms.PasswordInput(attrs={'placeholder': 'Parol'}))

    def clean(self):
        cleaned_data = super().clean()
        username = normalize_uz_phone(cleaned_data.get('username'))
        password = cleaned_data.get('password')
        cleaned_data['username'] = username

        if username and password:
            emp = Employee.objects.filter(Q(phone_primary=username) | Q(phone_secondary=username)).select_related('user').first()
            user = authenticate(username=emp.user.username, password=password) if emp else None
            if not user:
                raise forms.ValidationError("Telefon yoki parol noto'g'ri.")
            if not user.is_active:
                raise forms.ValidationError('Foydalanuvchi faol emas.')
            cleaned_data['user'] = user

        return cleaned_data


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        label='Foydalanuvchi nomi',
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Foydalanuvchi nomi'}),
    )
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={'placeholder': 'Parol'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = (cleaned_data.get('username') or '').strip()
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Foydalanuvchi nomi yoki parol noto'g'ri.")
            if not user.is_active:
                raise forms.ValidationError('Foydalanuvchi faol emas.')
            if not (user.is_staff or user.is_superuser):
                raise forms.ValidationError("Siz admin sifatida kirish huquqiga ega emassiz.")
            cleaned_data['user'] = user

        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'price')


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = (
            'name',
            'address',
            'phone_primary',
            'phone_secondary',
            'note',
            'photo',
            'latitude',
            'longitude',
        )
        widgets = {
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('shop', 'order_type', 'paid_amount', 'note')
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class DeliveryCompleteForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('delivery_received_amount', 'delivery_note')
        widgets = {
            'delivery_note': forms.Textarea(attrs={'rows': 3}),
        }


class OrderItemForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), label='Mahsulot')
    quantity = forms.IntegerField(min_value=1, label='Soni')


class BaseOrderItemFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()

        valid_rows = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_rows += 1

        if valid_rows == 0:
            raise forms.ValidationError("Kamida bitta mahsulot qo'shing.")


OrderItemFormSet = formset_factory(
    OrderItemForm,
    formset=BaseOrderItemFormSet,
    extra=1,
    can_delete=True,
)


class ShopDepositForm(forms.ModelForm):
    class Meta:
        model = ShopDeposit
        fields = ('date', 'amount', 'note')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class EmployeeCreateForm(forms.Form):
    photo = forms.FileField(required=False)
    first_name = forms.CharField(max_length=150, label='Ism')
    last_name = forms.CharField(max_length=150, label='Familiya')
    phone_primary = forms.CharField(max_length=25, label='Telefon 1')
    phone_secondary = forms.CharField(max_length=25, required=False, label='Telefon 2')
    role = forms.ChoiceField(choices=Employee.ROLE_CHOICES, label='Lavozim')
    password = forms.CharField(label='Parol', widget=forms.PasswordInput)

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))

    def save(self):
        User = get_user_model()
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        username_base = f"{first_name}.{last_name}".lower().replace(' ', '')
        username = username_base
        idx = 1
        while User.objects.filter(username=username).exists():
            idx += 1
            username = f'{username_base}{idx}'

        user = User.objects.create_user(
            username=username,
            password=self.cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
        )

        employee = Employee.objects.create(
            user=user,
            photo=self.cleaned_data.get('photo'),
            phone_primary=self.cleaned_data['phone_primary'],
            phone_secondary=self.cleaned_data.get('phone_secondary', ''),
            role=self.cleaned_data['role'],
        )
        return employee


class EmployeeUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label='Ism')
    last_name = forms.CharField(max_length=150, label='Familiya')

    class Meta:
        model = Employee
        fields = ('photo', 'phone_primary', 'phone_secondary', 'role')
        labels = {
            'photo': 'Rasm',
            'phone_primary': 'Telefon 1',
            'phone_secondary': 'Telefon 2',
            'role': 'Lavozim',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.user.first_name = self.cleaned_data['first_name']
        employee.user.last_name = self.cleaned_data['last_name']
        if commit:
            employee.user.save(update_fields=['first_name', 'last_name'])
            employee.save()
        return employee


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label='Ism')
    last_name = forms.CharField(max_length=150, label='Familiya')
    new_password = forms.CharField(
        required=False,
        label='Yangi parol',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    new_password_confirm = forms.CharField(
        required=False,
        label='Yangi parol (takror)',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    class Meta:
        model = UserProfile
        fields = ('photo', 'phone_primary', 'phone_secondary')
        labels = {
            'photo': 'Profil rasmi',
            'phone_primary': 'Telefon 1',
            'phone_secondary': 'Telefon 2',
        }

    def __init__(self, *args, user=None, allow_password=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.allow_password = allow_password
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
        if not allow_password:
            self.fields.pop('new_password', None)
            self.fields.pop('new_password_confirm', None)

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))


    def clean(self):
        cleaned = super().clean()
        if self.allow_password:
            p1 = cleaned.get('new_password') or ''
            p2 = cleaned.get('new_password_confirm') or ''
            if p1 or p2:
                if p1 != p2:
                    raise forms.ValidationError('Yangi parollar mos emas.')
                if len(p1) < 6:
                    raise forms.ValidationError("Parol kamida 6 belgidan iborat bo'lishi kerak.")
        return cleaned

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', self.user.first_name)
            self.user.last_name = self.cleaned_data.get('last_name', self.user.last_name)
        if commit:
            if self.user:
                self.user.save(update_fields=['first_name', 'last_name'])
                new_password = self.cleaned_data.get('new_password') if self.allow_password else ''
                if new_password:
                    self.user.set_password(new_password)
                    self.user.save(update_fields=['password'])
            profile.save()
        return profile


class EmployeeAdminProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label='Ism')
    last_name = forms.CharField(max_length=150, label='Familiya')
    new_password = forms.CharField(required=False, label='Yangi parol', widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(required=False, label='Yangi parol (takror)', widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ('photo', 'phone_primary', 'phone_secondary', 'role')
        labels = {
            'photo': 'Profil rasmi',
            'phone_primary': 'Telefon 1',
            'phone_secondary': 'Telefon 2',
            'role': 'Lavozim',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password') or ''
        p2 = cleaned.get('new_password_confirm') or ''
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError('Yangi parollar mos emas.')
            if len(p1) < 6:
                raise forms.ValidationError("Parol kamida 6 belgidan iborat bo'lishi kerak.")
        return cleaned

    def save(self, commit=True):
        employee = super().save(commit=False)
        user = employee.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save(update_fields=['first_name', 'last_name'])
            new_password = self.cleaned_data.get('new_password') or ''
            if new_password:
                user.set_password(new_password)
                user.save(update_fields=['password'])
            employee.save()
        return employee
