import calendar
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LogoutView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView

from core.export_utils import (
    export_analytics_excel,
    export_analytics_pdf,
    export_order_excel,
    export_order_pdf,
    export_orders_excel,
    export_orders_pdf,
    export_shops_excel,
    export_shops_pdf,
    export_transactions_excel,
    export_transactions_pdf,
)
from core.forms import LoginForm, OrderForm, OrderItemFormSet, ProductForm, ShopDepositForm, ShopForm
from core.models import Order, OrderItem, Product, Shop, ShopDeposit


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class LoginPageView(FormView):
    template_name = 'auth/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.cleaned_data['user'])
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    pass


class DashboardView(StaffRequiredMixin, TemplateView):
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
        return context


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'core/products/product_list.html'
    context_object_name = 'products'


class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        messages.success(self.request, 'Mahsulot muvaffaqiyatli qo\'shildi.')
        return super().form_valid(form)


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'core/products/product_form.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        messages.success(self.request, 'Mahsulot yangilandi.')
        return super().form_valid(form)


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    template_name = 'core/products/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')

    def form_valid(self, form):
        messages.success(self.request, 'Mahsulot o\'chirildi.')
        return super().form_valid(form)


class ShopListView(StaffRequiredMixin, ListView):
    model = Shop
    template_name = 'core/shops/shop_list.html'
    context_object_name = 'shops'


class ShopCreateView(StaffRequiredMixin, CreateView):
    model = Shop
    form_class = ShopForm
    template_name = 'core/shops/shop_form.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        messages.success(self.request, "Do'kon muvaffaqiyatli qo'shildi.")
        return super().form_valid(form)


class ShopUpdateView(StaffRequiredMixin, UpdateView):
    model = Shop
    form_class = ShopForm
    template_name = 'core/shops/shop_form.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        messages.success(self.request, "Do'kon ma'lumotlari yangilandi.")
        return super().form_valid(form)


class ShopDeleteView(StaffRequiredMixin, DeleteView):
    model = Shop
    template_name = 'core/shops/shop_confirm_delete.html'
    success_url = reverse_lazy('shop-list')

    def form_valid(self, form):
        messages.success(self.request, "Do'kon o'chirildi.")
        return super().form_valid(form)


class ShopDetailView(StaffRequiredMixin, TemplateView):
    template_name = 'core/shops/shop_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = get_object_or_404(Shop, pk=self.kwargs['pk'])
        transactions = build_shop_transactions(shop)
        context.update(
            {
                'shop': shop,
                'deposit_form': ShopDepositForm(),
                'transactions': transactions,
            }
        )
        return context


class ShopDepositCreateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        form = ShopDepositForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.shop = shop
            deposit.save()
            messages.success(request, "Depozit qo'shildi.")
        else:
            messages.error(request, 'Depozit ma\'lumotlari noto\'g\'ri.')
        return redirect('shop-detail', pk=shop.pk)


class ShopDepositUpdateView(StaffRequiredMixin, UpdateView):
    model = ShopDeposit
    form_class = ShopDepositForm
    template_name = 'core/shops/deposit_form.html'

    def get_success_url(self):
        return reverse('shop-detail', kwargs={'pk': self.object.shop_id})

    def form_valid(self, form):
        messages.success(self.request, 'Depozit yangilandi.')
        return super().form_valid(form)


class ShopDepositDeleteView(StaffRequiredMixin, DeleteView):
    model = ShopDeposit
    template_name = 'core/shops/deposit_confirm_delete.html'

    def get_success_url(self):
        return reverse('shop-detail', kwargs={'pk': self.object.shop_id})

    def form_valid(self, form):
        messages.success(self.request, "Depozit o'chirildi.")
        return super().form_valid(form)


class ShopTransactionExportExcelView(StaffRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        transactions = build_shop_transactions(shop)
        return export_transactions_excel(shop, transactions)


class ShopTransactionExportPDFView(StaffRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        transactions = build_shop_transactions(shop)
        return export_transactions_pdf(shop, transactions)


class ShopListExportExcelView(StaffRequiredMixin, View):
    def get(self, request):
        return export_shops_excel(Shop.objects.all())


class ShopListExportPDFView(StaffRequiredMixin, View):
    def get(self, request):
        return export_shops_pdf(Shop.objects.all())


class OrderListView(StaffRequiredMixin, TemplateView):
    template_name = 'core/orders/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('q', '').strip()
        qs = Order.objects.select_related('shop').all()
        if search:
            qs = qs.filter(shop__name__icontains=search)

        paginator = Paginator(qs, 12)
        page_obj = paginator.get_page(self.request.GET.get('page'))

        context.update({'page_obj': page_obj, 'search': search})
        return context


class OrderCreateView(StaffRequiredMixin, View):
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


class OrderUpdateView(StaffRequiredMixin, View):
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


class OrderDeleteView(StaffRequiredMixin, DeleteView):
    model = Order
    template_name = 'core/orders/order_confirm_delete.html'
    success_url = reverse_lazy('order-list')

    def form_valid(self, form):
        messages.success(self.request, "Buyurtma o'chirildi.")
        return super().form_valid(form)


class OrderDetailJsonView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order.objects.select_related('shop'), pk=pk)
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
                'items': items,
                'total_amount': float(order.total_amount),
                'paid_amount': float(order.paid_amount),
                'remaining_balance': float(order.remaining_balance),
                'export_pdf_url': reverse('order-export-pdf', kwargs={'pk': order.pk}),
                'export_excel_url': reverse('order-export-excel', kwargs={'pk': order.pk}),
            }
        )


class OrderExportPDFView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return export_order_pdf(order)


class OrderExportExcelView(StaffRequiredMixin, View):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return export_order_excel(order)


class OrderListExportPDFView(StaffRequiredMixin, View):
    def get(self, request):
        return export_orders_pdf(Order.objects.select_related('shop').all())


class OrderListExportExcelView(StaffRequiredMixin, View):
    def get(self, request):
        return export_orders_excel(Order.objects.select_related('shop').all())


class AnalyticsView(StaffRequiredMixin, TemplateView):
    template_name = 'core/analytics/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month = self.request.GET.get('month')
        stats = build_analytics_payload(month)
        context.update(stats)
        return context


class AnalyticsDataView(StaffRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        return JsonResponse(build_analytics_payload(month))


class AnalyticsExportPDFView(StaffRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        payload = build_analytics_payload(month)
        return export_analytics_pdf(payload)


class AnalyticsExportExcelView(StaffRequiredMixin, View):
    def get(self, request):
        month = request.GET.get('month')
        payload = build_analytics_payload(month)
        return export_analytics_excel(payload)


def save_order_with_items(order_form, formset, user):
    with transaction.atomic():
        order = order_form.save(commit=False)
        order.created_by = user
        if not order.pk:
            order.order_date = timezone.localdate()
        order.total_amount = Decimal('0')
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
