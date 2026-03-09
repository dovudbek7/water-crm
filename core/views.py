import calendar
from datetime import date, datetime, time
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LogoutView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView

from core.export_utils import (
    export_analytics_excel,
    export_analytics_pdf,
    export_employee_detail_excel,
    export_employee_detail_pdf,
    export_employees_excel,
    export_employees_pdf,
    export_order_excel,
    export_order_pdf,
    export_orders_excel,
    export_orders_pdf,
    export_shops_excel,
    export_shops_pdf,
    export_transactions_excel,
    export_transactions_pdf,
)
from core.forms import (
    AdminLoginForm,
    DeliveryCompleteForm,
    EmployeeCreateForm,
    EmployeeAdminProfileForm,
    LoginForm,
    OrderForm,
    OrderItemFormSet,
    ProductForm,
    ShopDepositForm,
    ShopForm,
    UserProfileForm,
)
from core.models import ActionLog, Employee, Order, OrderItem, Product, Shop, ShopDeposit, UserProfile


class AuthRequiredMixin(LoginRequiredMixin):
    pass


class SuperAdminRequiredMixin(AuthRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return permission_denied_view(self.request)


class LoginPageView(FormView):
    template_name = 'auth/login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard' if request.user.is_superuser else 'order-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('admin_form', AdminLoginForm(prefix='admin'))
        ctx.setdefault('open_admin_box', False)
        return ctx

    def post(self, request, *args, **kwargs):
        login_type = request.POST.get('login_type', 'employee')
        if login_type == 'admin':
            emp_form = LoginForm()
            admin_form = AdminLoginForm(request.POST, prefix='admin')
            if admin_form.is_valid():
                login(request, admin_form.cleaned_data['user'])
                return redirect('dashboard')
            return self.render_to_response(
                self.get_context_data(form=emp_form, admin_form=admin_form, open_admin_box=True)
            )

        form = LoginForm(request.POST)
        admin_form = AdminLoginForm(prefix='admin')
        if form.is_valid():
            login(request, form.cleaned_data['user'])
            return redirect('dashboard' if request.user.is_superuser else 'order-list')
        return self.render_to_response(
            self.get_context_data(form=form, admin_form=admin_form, open_admin_box=False)
        )


class UserLogoutView(LogoutView):
    pass


def permission_denied_view(request, exception=None):
    if request.user.is_authenticated and request.user.is_superuser:
        home_url = reverse('dashboard')
    elif request.user.is_authenticated:
        home_url = reverse('order-list')
    else:
        home_url = reverse('login')
    return render(request, '403.html', {'home_url': home_url}, status=403)


def log_action(user, action_type, object_label, message):
    employee = user.employee_profile if hasattr(user, 'employee_profile') else None
    ActionLog.objects.create(
        employee=employee,
        actor_name=user.get_full_name() or user.username,
        action_type=action_type,
        object_label=object_label,
        message=message,
    )


def _map_urls_from_shop(shop):
    if not shop:
        return '', ''
    google = (shop.google_map_link or '').strip()
    yandex = (shop.yandex_map_link or '').strip()
    if google or yandex:
        return google, yandex
    # Eski ma'lumotlar bo'lsa, orqaga moslik uchun fallback.
    if shop.latitude is not None and shop.longitude is not None:
        lat = str(shop.latitude)
        lng = str(shop.longitude)
        return (
            f'https://www.google.com/maps/dir/?api=1&destination={lat},{lng}&travelmode=driving',
            f'https://yandex.com/maps/?rtext=~{lat},{lng}&rtt=auto&ll={lng}%2C{lat}&z=16&pt={lng},{lat},pm2rdm',
        )
    if shop.map_link:
        return shop.map_link, ''
    return '', ''


def _val(v):
    if v is None or v == '':
        return '-'
    return str(v)


def _json_safe(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return value


def _log_create(user, obj, fields):
    data = {f: _val(getattr(obj, f, '')) for f in fields}
    label = str(obj)
    ActionLog.objects.create(
        employee=user.employee_profile if hasattr(user, 'employee_profile') else None,
        actor_name=user.get_full_name() or user.username,
        action_type=ActionLog.ACTION_CREATED,
        object_label=label,
        message=f"{user.get_full_name() or user.username} yaratdi: {label}",
        target_model=obj.__class__.__name__,
        target_id=str(getattr(obj, 'pk', '')),
        details={'created': data},
    )


def _log_update(user, obj, before_data, after_data):
    changed = {}
    for key, old in before_data.items():
        new = after_data.get(key)
        if _val(old) != _val(new):
            changed[key] = {'old': _val(old), 'new': _val(new)}
    if not changed:
        return
    label = str(obj)
    ActionLog.objects.create(
        employee=user.employee_profile if hasattr(user, 'employee_profile') else None,
        actor_name=user.get_full_name() or user.username,
        action_type=ActionLog.ACTION_UPDATED,
        object_label=label,
        message=f"{user.get_full_name() or user.username} tahrirladi: {label}",
        target_model=obj.__class__.__name__,
        target_id=str(getattr(obj, 'pk', '')),
        details={'updated_fields': changed},
    )


def _log_delete(user, model_name, object_label, snapshot):
    ActionLog.objects.create(
        employee=user.employee_profile if hasattr(user, 'employee_profile') else None,
        actor_name=user.get_full_name() or user.username,
        action_type=ActionLog.ACTION_DELETED,
        object_label=object_label,
        message=f"{user.get_full_name() or user.username} o'chirdi: {object_label}",
        target_model=model_name,
        target_id='',
        details={'deleted': _json_safe(snapshot)},
    )


def company_context():
    return {
        'company_name': 'Aqua Blue Zam-Zam',
        'company_phone_1': '+998 95 200 07 06',
        'company_phone_2': '+998 94 073 07 06',
    }


class DashboardView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1)
        else:
            month_end = date(today.year, today.month + 1, 1)

        month_sales = Order.objects.filter(order_date__gte=month_start, order_date__lt=month_end).aggregate(
            total=Coalesce(Sum('total_amount'), Decimal('0'))
        )['total']

        debt_shops = 0
        total_debt_amount = Decimal('0')
        total_deposit_amount = Decimal('0')
        for shop in Shop.objects.all():
            if shop.balance < 0:
                debt_shops += 1
                total_debt_amount += abs(shop.balance)
            elif shop.balance > 0:
                total_deposit_amount += shop.balance

        last_6 = []
        for i in range(5, -1, -1):
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            start = date(y, m, 1)
            end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
            total = (
                Order.objects.filter(order_date__gte=start, order_date__lt=end).aggregate(
                    total=Coalesce(Sum('total_amount'), Decimal('0'))
                )['total']
            )
            last_6.append({'label': f"{calendar.month_abbr[m]} {y}", 'total': float(total)})

        top_products = (
            OrderItem.objects.values(name=F('product__name'))
            .annotate(total_qty=Coalesce(Sum('quantity'), 0))
            .order_by('-total_qty')[:6]
        )

        context.update(
            {
                'shops_count': Shop.objects.count(),
                'products_count': Product.objects.count(),
                'month_sales': month_sales,
                'debt_shops_count': debt_shops,
                'total_debt_amount': total_debt_amount,
                'total_deposit_amount': total_deposit_amount,
                'monthly_labels': [row['label'] for row in last_6],
                'monthly_values': [row['total'] for row in last_6],
                'top_product_labels': [row['name'] for row in top_products],
                'top_product_values': [row['total_qty'] for row in top_products],
                'recent_orders': Order.objects.select_related('shop')[:8],
            }
        )
        top_order_taker = (
            Employee.objects.select_related('user')
            .annotate(c=Count('user__created_orders'))
            .order_by('-c')
            .first()
        )
        top_courier = (
            Employee.objects.select_related('user')
            .filter(role=Employee.ROLE_COURIER)
            .annotate(c=Count('user__delivered_orders'))
            .order_by('-c')
            .first()
        )
        context['top_order_taker'] = top_order_taker
        context['top_courier'] = top_courier
        context.update(company_context())
        return context


class ProductListView(SuperAdminRequiredMixin, ListView):
    model = Product
    template_name = 'core/products/product_list.html'
    context_object_name = 'products'


class ProductCreateView(SuperAdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        _log_create(self.request.user, self.object, ['name', 'price'])
        messages.success(self.request, 'Mahsulot muvaffaqiyatli qo\'shildi.')
        return response


class ProductUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        before = model_to_dict(self.get_object(), fields=['name', 'price'])
        response = super().form_valid(form)
        after = model_to_dict(self.object, fields=['name', 'price'])
        _log_update(self.request.user, self.object, before, after)
        messages.success(self.request, 'Mahsulot yangilandi.')
        return response


class ProductDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'core/products/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        obj = self.get_object()
        snapshot = model_to_dict(obj, fields=['name', 'price'])
        _log_delete(self.request.user, 'Product', str(obj), snapshot)
        messages.success(self.request, 'Mahsulot o\'chirildi.')
        return super().form_valid(form)


class ShopListView(AuthRequiredMixin, ListView):
    model = Shop
    template_name = 'core/shops/shop_list.html'
    context_object_name = 'shops'

    def get_queryset(self):
        qs = Shop.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(phone_primary__icontains=q)
                | Q(phone_secondary__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search'] = self.request.GET.get('q', '').strip()
        return ctx


class ShopMapView(AuthRequiredMixin, TemplateView):
    template_name = 'core/shops/shop_map.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        shops = Shop.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        ctx['shops_data'] = [
            {
                'id': s.id,
                'name': s.name,
                'latitude': float(s.latitude),
                'longitude': float(s.longitude),
            }
            for s in shops
        ]
        return ctx


class ShopCreateView(AuthRequiredMixin, CreateView):
    model = Shop
    form_class = ShopForm
    template_name = 'core/shops/shop_form.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        messages.success(self.request, "Do'kon muvaffaqiyatli qo'shildi.")
        response = super().form_valid(form)
        _log_create(self.request.user, self.object, ['name', 'address', 'phone_primary', 'phone_secondary', 'note', 'google_map_link', 'yandex_map_link'])
        return response


class ShopUpdateView(AuthRequiredMixin, UpdateView):
    model = Shop
    form_class = ShopForm
    template_name = 'core/shops/shop_form.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        before = model_to_dict(self.get_object(), fields=['name', 'address', 'phone_primary', 'phone_secondary', 'note', 'google_map_link', 'yandex_map_link'])
        response = super().form_valid(form)
        after = model_to_dict(self.object, fields=['name', 'address', 'phone_primary', 'phone_secondary', 'note', 'google_map_link', 'yandex_map_link'])
        _log_update(self.request.user, self.object, before, after)
        messages.success(self.request, "Do'kon ma'lumotlari yangilandi.")
        return response


class ShopDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Shop
    template_name = 'core/shops/shop_confirm_delete.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        obj = self.get_object()
        snapshot = model_to_dict(obj, fields=['name', 'address', 'phone_primary', 'phone_secondary', 'note', 'google_map_link', 'yandex_map_link'])
        _log_delete(self.request.user, 'Shop', str(obj), snapshot)
        messages.success(self.request, "Do'kon o'chirildi.")
        return super().form_valid(form)


class ShopDetailView(AuthRequiredMixin, TemplateView):
    template_name = 'core/shops/shop_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = get_object_or_404(Shop, pk=self.kwargs['pk'])
        transactions = build_shop_transactions(shop)
        google_url, yandex_url = _map_urls_from_shop(shop)
        context.update(
            {
                'shop': shop,
                'deposit_form': ShopDepositForm(),
                'transactions': transactions,
                'google_maps_url': google_url,
                'yandex_maps_url': yandex_url,
            }
        )
        context.update(company_context())
        return context


class ShopDepositCreateView(AuthRequiredMixin, View):
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        form = ShopDepositForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.shop = shop
            deposit.save()
            _log_create(request.user, deposit, ['shop_id', 'date', 'amount', 'note'])
            messages.success(request, "Depozit qo'shildi.")
        else:
            messages.error(request, 'Depozit ma\'lumotlari noto\'g\'ri.')
        return redirect('shop-detail', pk=shop.pk)


class ShopDepositUpdateView(AuthRequiredMixin, UpdateView):
    model = ShopDeposit
    form_class = ShopDepositForm
    template_name = 'core/shops/deposit_form.html'

    def get_success_url(self):
        return reverse('shop-detail', kwargs={'pk': self.object.shop_id})

    def form_valid(self, form):
        before = model_to_dict(self.get_object(), fields=['shop_id', 'date', 'amount', 'note'])
        response = super().form_valid(form)
        after = model_to_dict(self.object, fields=['shop_id', 'date', 'amount', 'note'])
        _log_update(self.request.user, self.object, before, after)
        messages.success(self.request, 'Depozit yangilandi.')
        return response


class ShopDepositDeleteView(AuthRequiredMixin, DeleteView):
    model = ShopDeposit
    template_name = 'core/shops/deposit_confirm_delete.html'

    def get_success_url(self):
        return reverse('shop-detail', kwargs={'pk': self.object.shop_id})

    def form_valid(self, form):
        obj = self.get_object()
        snapshot = model_to_dict(obj, fields=['shop_id', 'date', 'amount', 'note'])
        _log_delete(self.request.user, 'ShopDeposit', f"Depozit #{obj.pk}", snapshot)
        messages.success(self.request, "Depozit o'chirildi.")
        return super().form_valid(form)


class ShopTransactionExportExcelView(AuthRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        transactions = build_shop_transactions(shop)
        return export_transactions_excel(shop, transactions)


class ShopTransactionExportPDFView(AuthRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        transactions = build_shop_transactions(shop)
        return export_transactions_pdf(shop, transactions)


class ShopListExportExcelView(AuthRequiredMixin, View):
    def get(self, request):
        return export_shops_excel(Shop.objects.all())


class ShopListExportPDFView(AuthRequiredMixin, View):
    def get(self, request):
        return export_shops_pdf(Shop.objects.all())


class OrderListView(AuthRequiredMixin, TemplateView):
    template_name = 'core/orders/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('q', '').strip()
        sort = self.request.GET.get('sort', '-id')

        sort_map = {
            'id': 'id',
            '-id': '-id',
            'date': 'order_date',
            '-date': '-order_date',
            'paid': 'paid_amount',
            '-paid': '-paid_amount',
            'remaining': 'remaining_amount',
            '-remaining': '-remaining_amount',
        }
        order_by = sort_map.get(sort, '-id')

        qs = Order.objects.select_related('shop').annotate(
            remaining_amount=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=DecimalField())
        )
        if search:
            qs = qs.filter(
                Q(shop__name__icontains=search)
                | Q(shop__phone_primary__icontains=search)
                | Q(shop__phone_secondary__icontains=search)
                | Q(id__icontains=search)
            )

        qs = qs.order_by(order_by)
        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(self.request.GET.get('page'))

        context.update({'page_obj': page_obj, 'search': search, 'sort': sort})
        context.update(company_context())
        return context


class OrderCreateView(AuthRequiredMixin, View):
    template_name = 'core/orders/order_create.html'

    def get(self, request):
        context = self._build_context(OrderForm(), OrderItemFormSet(), None)
        return render(request, self.template_name, context)

    def post(self, request):
        order_form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)

        if order_form.is_valid() and formset.is_valid():
            order = save_order_with_items(order_form, formset, request.user)
            messages.success(request, f'Buyurtma #{order.id} muvaffaqiyatli saqlandi.')
            _log_create(request.user, order, ['shop_id', 'order_date', 'order_type', 'total_amount', 'paid_amount', 'note'])
            return redirect('order-list')

        context = self._build_context(order_form, formset, None)
        return render(request, self.template_name, context)

    def _build_context(self, order_form, formset, order):
        return {
            'order_form': order_form,
            'formset': formset,
            'today': timezone.localdate(),
            'product_prices': {str(p.id): float(p.price) for p in Product.objects.all()},
            'order_obj': order,
        }


class OrderUpdateView(AuthRequiredMixin, View):
    template_name = 'core/orders/order_create.html'

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order_form = OrderForm(instance=order)
        initial = [{'product': item.product, 'quantity': item.quantity} for item in order.items.select_related('product')]
        formset = OrderItemFormSet(initial=initial)
        context = {
            'order_form': order_form,
            'formset': formset,
            'today': order.order_date,
            'product_prices': {str(p.id): float(p.price) for p in Product.objects.all()},
            'order_obj': order,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order_form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST)

        if order_form.is_valid() and formset.is_valid():
            before = model_to_dict(order, fields=['shop_id', 'order_date', 'order_type', 'total_amount', 'paid_amount', 'note', 'delivery_status'])
            with transaction.atomic():
                order = order_form.save()
                order.items.all().delete()
                for form in formset:
                    if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                        continue
                    product = form.cleaned_data['product']
                    quantity = form.cleaned_data['quantity']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price_at_sale=product.price,
                    )
                order.recalculate_total()
            after = model_to_dict(order, fields=['shop_id', 'order_date', 'order_type', 'total_amount', 'paid_amount', 'note', 'delivery_status'])
            _log_update(request.user, order, before, after)

            messages.success(request, f'Buyurtma #{order.id} yangilandi.')
            return redirect('order-list')

        context = {
            'order_form': order_form,
            'formset': formset,
            'today': order.order_date,
            'product_prices': {str(p.id): float(p.price) for p in Product.objects.all()},
            'order_obj': order,
        }
        return render(request, self.template_name, context)


class OrderDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Order
    template_name = 'core/orders/order_confirm_delete.html'
    success_url = reverse_lazy('order-list')

    def form_valid(self, form):
        obj = self.get_object()
        snapshot = {
            'order_id': obj.pk,
            'shop_id': obj.shop_id,
            'shop_name': obj.shop.name if obj.shop_id else '-',
            'order_date': obj.order_date,
            'order_type': obj.get_order_type_display(),
            'delivery_status': obj.get_delivery_status_display(),
            'total_amount': obj.total_amount,
            'paid_amount': obj.paid_amount,
            'remaining_balance': obj.remaining_balance,
            'note': obj.note or '-',
        }
        try:
            _log_delete(self.request.user, 'Order', f"Buyurtma #{obj.pk}", snapshot)
        except Exception:
            messages.warning(self.request, "Buyurtma o'chirildi, lekin log yozishda kichik xatolik bo'ldi.")
        messages.success(self.request, "Buyurtma o'chirildi.")
        return super().form_valid(form)


class OrderDetailJsonView(AuthRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order.objects.select_related('shop'), pk=pk)
        google_url, yandex_url = _map_urls_from_shop(order.shop)
        items = [
            {
                'product': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price_at_sale),
                'subtotal': float(item.total_amount),
            }
            for item in order.items.select_related('product')
        ]

        return JsonResponse(
            {
                'id': order.id,
                'shop_name': order.shop.name,
                'order_date': order.order_date.strftime('%d.%m.%Y'),
                'delivery_status': order.delivery_status,
                'delivery_status_label': order.get_delivery_status_display(),
                'items': items,
                'total_amount': float(order.total_amount),
                'paid_amount': float(order.paid_amount),
                'remaining_balance': float(order.remaining_balance),
                'export_pdf_url': reverse('order-export-pdf', kwargs={'pk': order.pk}),
                'export_excel_url': reverse('order-export-excel', kwargs={'pk': order.pk}),
                'google_maps_url': google_url,
                'yandex_maps_url': yandex_url,
            }
        )


class OrderExportPDFView(AuthRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return export_order_pdf(order)


class OrderExportExcelView(AuthRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return export_order_excel(order)


class OrderListExportPDFView(AuthRequiredMixin, View):
    def get(self, request):
        return export_orders_pdf(Order.objects.select_related('shop').all())


class OrderListExportExcelView(AuthRequiredMixin, View):
    def get(self, request):
        return export_orders_excel(Order.objects.select_related('shop').all())


class DeliveryListView(AuthRequiredMixin, TemplateView):
    template_name = 'core/delivery/delivery_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('q', '').strip()
        sort = self.request.GET.get('sort', '-id')

        sort_map = {
            'id': 'id',
            '-id': '-id',
            'date': 'order_date',
            '-date': '-order_date',
            'paid': 'paid_amount',
            '-paid': '-paid_amount',
            'remaining': 'remaining_amount',
            '-remaining': '-remaining_amount',
        }
        order_by = sort_map.get(sort, '-id')

        qs = Order.objects.select_related('shop', 'courier').filter(order_type=Order.ORDER_TYPE_DELIVERY).annotate(
            remaining_amount=ExpressionWrapper(F('total_amount') - F('paid_amount'), output_field=DecimalField())
        )
        if search:
            qs = qs.filter(
                Q(shop__name__icontains=search)
                | Q(shop__phone_primary__icontains=search)
                | Q(shop__phone_secondary__icontains=search)
                | Q(id__icontains=search)
            )

        qs = qs.order_by(order_by)
        context.update({'orders': qs, 'search': search, 'sort': sort})
        return context


class DeliveryDetailView(AuthRequiredMixin, View):
    template_name = 'core/delivery/delivery_detail.html'

    def get(self, request, pk):
        order = get_object_or_404(Order.objects.select_related('shop', 'courier'), pk=pk, order_type=Order.ORDER_TYPE_DELIVERY)
        form = DeliveryCompleteForm(instance=order)
        google_url, yandex_url = _map_urls_from_shop(order.shop)
        return render(
            request,
            self.template_name,
            {
                'order': order,
                'form': form,
                'google_maps_url': google_url,
                'yandex_maps_url': yandex_url,
            },
        )

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, order_type=Order.ORDER_TYPE_DELIVERY)
        before = model_to_dict(order, fields=['delivery_status', 'delivery_received_amount', 'delivery_note', 'courier_id', 'delivered_at'])
        form = DeliveryCompleteForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.delivery_status = Order.DELIVERY_DONE
            order.courier = request.user
            order.delivered_at = timezone.now()
            order.save(update_fields=['delivery_received_amount', 'delivery_note', 'delivery_status', 'courier', 'delivered_at'])
            messages.success(request, f'Buyurtma #{order.id} yetkazilgan deb belgilandi.')
            after = model_to_dict(order, fields=['delivery_status', 'delivery_received_amount', 'delivery_note', 'courier_id', 'delivered_at'])
            _log_update(request.user, order, before, after)
            return redirect('delivery-list')
        google_url, yandex_url = _map_urls_from_shop(order.shop)
        return render(
            request,
            self.template_name,
            {
                'order': order,
                'form': form,
                'google_maps_url': google_url,
                'yandex_maps_url': yandex_url,
            },
        )


class AnalyticsView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'core/analytics/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month = self.request.GET.get('month')
        stats = build_analytics_payload(month)
        context.update(stats)
        return context


class AnalyticsDataView(SuperAdminRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        return JsonResponse(build_analytics_payload(month))


class AnalyticsExportPDFView(SuperAdminRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        payload = build_analytics_payload(month)
        return export_analytics_pdf(payload)


class AnalyticsExportExcelView(SuperAdminRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        payload = build_analytics_payload(month)
        return export_analytics_excel(payload)


class EmployeeListView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'core/employees/employee_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['employees'] = Employee.objects.select_related('user').all()
        return ctx


class EmployeeCreateView(SuperAdminRequiredMixin, FormView):
    template_name = 'core/employees/employee_form.html'
    form_class = EmployeeCreateForm
    success_url = reverse_lazy('employee-list')

    def form_valid(self, form):
        employee = form.save()
        _log_create(self.request.user, employee, ['user_id', 'role', 'phone_primary', 'phone_secondary'])
        messages.success(self.request, f"Xodim qo'shildi: {employee}")
        return super().form_valid(form)


class EmployeeUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeAdminProfileForm
    template_name = 'core/employees/employee_update.html'

    def form_valid(self, form):
        before = model_to_dict(self.get_object(), fields=['role', 'phone_primary', 'phone_secondary'])
        response = super().form_valid(form)
        after = model_to_dict(self.object, fields=['role', 'phone_primary', 'phone_secondary'])
        _log_update(self.request.user, self.object, before, after)
        if form.cleaned_data.get('new_password'):
            ActionLog.objects.create(
                employee=self.request.user.employee_profile if hasattr(self.request.user, 'employee_profile') else None,
                actor_name=self.request.user.get_full_name() or self.request.user.username,
                action_type=ActionLog.ACTION_UPDATED,
                object_label=str(self.object),
                message=f"{self.request.user.get_full_name() or self.request.user.username} parolni yangiladi: {self.object}",
                target_model='Employee',
                target_id=str(self.object.pk),
                details={'updated_fields': {'password': {'old': '***', 'new': '***'}}},
            )
        messages.success(self.request, "Xodim ma'lumotlari yangilandi.")
        return response

    def get_success_url(self):
        return reverse('employee-detail', kwargs={'pk': self.object.pk})


class EmployeeDetailView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'core/employees/employee_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=self.kwargs['pk'])
        now = timezone.localdate()
        month_labels = []
        created_values = []
        delivered_values = []
        for i in range(5, -1, -1):
            y = now.year
            m = now.month - i
            while m <= 0:
                m += 12
                y -= 1
            start = date(y, m, 1)
            end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
            month_labels.append(f"{calendar.month_abbr[m]} {y}")
            created_values.append(employee.user.created_orders.filter(order_date__gte=start, order_date__lt=end).count())
            delivered_values.append(employee.user.delivered_orders.filter(delivered_at__date__gte=start, delivered_at__date__lt=end).count())

        logs = employee.logs.all()[:50]
        ctx.update(
            {
                'employee': employee,
                'employee_name': employee.user.first_name,
                'employee_last_name': employee.user.last_name,
                'orders_created_count': employee.total_orders_taken,
                'orders_delivered_count': employee.total_deliveries,
                'month_labels': month_labels,
                'created_values': created_values,
                'delivered_values': delivered_values,
                'logs': logs,
            }
        )
        return ctx


class EmployeeListExportPDFView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return export_employees_pdf(Employee.objects.select_related('user').all())


class EmployeeListExportExcelView(SuperAdminRequiredMixin, View):
    def get(self, request):
        return export_employees_excel(Employee.objects.select_related('user').all())


class EmployeeDetailExportPDFView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
        return export_employee_detail_pdf(employee)


class EmployeeDetailExportExcelView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=pk)
        return export_employee_detail_excel(employee)


class ActivityLogListView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'core/employees/activity_logs.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        employee_id = self.request.GET.get('employee')
        logs = ActionLog.objects.select_related('employee', 'employee__user').all()
        if employee_id:
            logs = logs.filter(employee_id=employee_id)
        ctx['logs'] = logs[:200]
        ctx['employees'] = Employee.objects.select_related('user').all()
        ctx['selected_employee'] = employee_id
        return ctx


class ActivityLogDetailJsonView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        log = get_object_or_404(ActionLog, pk=pk)
        return JsonResponse(
            {
                'id': log.id,
                'actor': log.employee.user.get_full_name() if log.employee else (log.actor_name or 'Admin'),
                'action': log.get_action_type_display(),
                'object': log.object_label,
                'message': log.message,
                'created_at': timezone.localtime(log.created_at).strftime('%d.%m.%Y %H:%M'),
                'details': _json_safe(log.details or {}),
            }
        )


class ProfileView(AuthRequiredMixin, View):
    template_name = 'core/profile/profile.html'

    def get(self, request):
        form, is_employee = self._build_form(request.user)
        return render(request, self.template_name, {'form': form, 'is_employee': is_employee})

    def post(self, request):
        form, is_employee = self._build_form(request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            if is_employee:
                before = model_to_dict(request.user.employee_profile, fields=['phone_primary', 'phone_secondary', 'role'])
            else:
                profile = request.user.user_profile if hasattr(request.user, 'user_profile') else None
                before = model_to_dict(profile, fields=['phone_primary', 'phone_secondary']) if profile else {}
            form.save()
            if is_employee:
                after = model_to_dict(request.user.employee_profile, fields=['phone_primary', 'phone_secondary', 'role'])
                _log_update(request.user, request.user.employee_profile, before, after)
            else:
                profile = request.user.user_profile
                after = model_to_dict(profile, fields=['phone_primary', 'phone_secondary'])
                if before:
                    _log_update(request.user, profile, before, after)
                else:
                    _log_create(request.user, profile, ['phone_primary', 'phone_secondary'])
            if 'new_password' in form.cleaned_data and form.cleaned_data.get('new_password'):
                ActionLog.objects.create(
                    employee=request.user.employee_profile if hasattr(request.user, 'employee_profile') else None,
                    actor_name=request.user.get_full_name() or request.user.username,
                    action_type=ActionLog.ACTION_UPDATED,
                    object_label='Profil paroli',
                    message=f"{request.user.get_full_name() or request.user.username} profil parolini yangiladi",
                    target_model='User',
                    target_id=str(request.user.pk),
                    details={'updated_fields': {'password': {'old': '***', 'new': '***'}}},
                )
                update_session_auth_hash(request, request.user)
            messages.success(request, "Profil ma'lumotlari saqlandi.")
            return redirect('profile')
        return render(request, self.template_name, {'form': form, 'is_employee': is_employee})

    def _build_form(self, user, data=None, files=None):
        if hasattr(user, 'employee_profile'):
            form = EmployeeAdminProfileForm(data=data, files=files, instance=user.employee_profile)
            if not user.is_superuser and 'role' in form.fields:
                form.fields.pop('role')
            return form, True

        profile, _ = UserProfile.objects.get_or_create(user=user)
        form = UserProfileForm(data=data, files=files, instance=profile, user=user, allow_password=True)
        return form, False


def save_order_with_items(order_form, formset, user):
    with transaction.atomic():
        order = order_form.save(commit=False)
        order.created_by = user
        if not order.pk:
            order.order_date = timezone.localdate()
        order.total_amount = Decimal('0')
        if order.order_type != Order.ORDER_TYPE_DELIVERY:
            order.delivery_status = Order.DELIVERY_NEW
        order.save()

        for form in formset:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue

            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_sale=product.price,
            )

        order.recalculate_total()
    return order


def build_shop_transactions(shop):
    rows = []

    for order in shop.orders.all():
        rows.append(
            {
                'date': order.order_date,
                'type': 'Buyurtma',
                'amount': -order.total_amount,
                'order_id': order.id,
                'note': order.note,
                'is_deposit': False,
                'is_order_payment': False,
                'pk': None,
                'sort_index': 1,
            }
        )
        rows.append(
            {
                'date': order.order_date,
                'type': f"To'lov (Buyurtma #{order.id})",
                'amount': order.paid_amount,
                'order_id': order.id,
                'note': order.note,
                'is_deposit': False,
                'is_order_payment': True,
                'pk': None,
                'sort_index': 0,
            }
        )

    for dep in shop.deposits.all():
        rows.append(
            {
                'date': dep.date,
                'type': 'Depozit',
                'amount': dep.amount,
                'order_id': None,
                'note': dep.note,
                'is_deposit': True,
                'is_order_payment': False,
                'pk': dep.pk,
                'sort_index': 2,
            }
        )

    rows.sort(key=lambda x: (x['date'], x['sort_index'], x.get('pk') or 0), reverse=True)
    return rows


def build_analytics_payload(month_str=None):
    today = timezone.localdate()

    if month_str:
        try:
            year, month = month_str.split('-')
            year = int(year)
            month = int(month)
            selected_start = date(year, month, 1)
        except (ValueError, TypeError):
            selected_start = today.replace(day=1)
    else:
        selected_start = today.replace(day=1)

    selected_month = selected_start.month
    selected_year = selected_start.year
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    selected_end = date(selected_year, selected_month, days_in_month)

    orders = Order.objects.filter(order_date__gte=selected_start, order_date__lte=selected_end)

    month_sales = orders.aggregate(total=Coalesce(Sum('total_amount'), Decimal('0')))['total']

    product_rows_qs = (
        OrderItem.objects.filter(order__order_date__gte=selected_start, order__order_date__lte=selected_end)
        .values(name=F('product__name'))
        .annotate(
            quantity=Coalesce(Sum('quantity'), 0),
            revenue=Coalesce(Sum('total_amount'), Decimal('0')),
        )
        .order_by('-quantity')
    )
    product_rows = list(product_rows_qs)

    day_sales_map = {d: 0.0 for d in range(1, days_in_month + 1)}
    day_rows = (
        orders.values(day=F('order_date__day'))
        .annotate(total=Coalesce(Sum('total_amount'), Decimal('0')))
        .order_by('day')
    )
    for row in day_rows:
        day_sales_map[row['day']] = float(row['total'])

    return {
        'selected_month': f'{selected_year:04d}-{selected_month:02d}',
        'month_sales': float(month_sales),
        'product_labels': [row['name'] for row in product_rows],
        'product_quantities': [row['quantity'] for row in product_rows],
        'product_revenues': [float(row['revenue']) for row in product_rows],
        'line_labels': [str(day) for day in day_sales_map.keys()],
        'line_values': list(day_sales_map.values()),
        'product_rows': product_rows,
    }
