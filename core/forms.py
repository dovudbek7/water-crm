import re

from django import forms
from django.contrib.auth import authenticate
from django.forms import formset_factory

from core.models import Order, Product, Shop, ShopDeposit


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
    username = forms.CharField(label='Ism', max_length=150)
    password = forms.CharField(label='Parol', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Ism yoki parol noto'g'ri.")
            if not user.is_staff and not user.is_superuser:
                raise forms.ValidationError('Tizimga faqat admin foydalanuvchilar kirishi mumkin.')
            cleaned_data['user'] = user

        return cleaned_data


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'price')


class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'address', 'phone_primary', 'phone_secondary', 'note')

    def clean_phone_primary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_primary'))

    def clean_phone_secondary(self):
        return normalize_uz_phone(self.cleaned_data.get('phone_secondary'))


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('shop', 'paid_amount', 'note')
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
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
