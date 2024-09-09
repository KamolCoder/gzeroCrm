import calendar
import json
from math import ceil

from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Sum, Max, F, Count, Prefetch
from django.db.models.functions import TruncMonth, TruncDay, TruncYear, TruncQuarter, Coalesce, Cast
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, CreateView, TemplateView, UpdateView
import xlwt
from rest_framework import status
from .forms import ClientForm, LoginForm, OrderForm, AbonementForm, EventForm, PaymentFormBooking, OfficeRentForm, \
    PaymentFormOffice, ClientEditForm
from .models import *
import datetime
from django.db import transaction
import random
import string
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from .helpers import send_otp_to_phone

from .serializers import AbonementSerializer, ClientSerializer, OrderSerializer


def for_workspace(order_start, order_end):
    dannie = Order.objects.annotate(date=TruncDate("order_start")).filter(is_deleted=False, product__category=4).values(
        'order_start', 'order_end')
    t1 = order_start
    t2 = order_end
    lst2 = []

    for i in dannie:
        s1, s2 = i['order_start'], i['order_end']
        if t1 > s1 and t1 >= s2 and t2 >= s1 and t2 > s2:
            pass
        elif t1 < s1 and s2 >= t1 and s1 >= t2 and t2 < s2:
            pass
        else:
            lst2.append(False)
    return len(lst2)


def order_exist(orders, product, order_start: datetime, order_end: datetime) -> str:
    order = orders.filter(product=product)
    category = Rooms.objects.get(pk=product).category.pk
    for i in order:
        orders_start, orders_end = i['order_start'], i['order_end']
        if order_end > orders_start and order_start < orders_end:
            if category == 4:  # If category is open-space
                return f" {for_workspace(order_start, order_end)} person"
            return f"{i['client__name']} {i['client__surname']}"
    return ''


class IndexView(ListView):
    model = Order
    template_name = 'crm/index.html'
    context_object_name = 'orders'

    def get_group(self):
        user_groups = self.request.user.groups.all()
        return user_groups[0].id

    @method_decorator(login_required(login_url='login'))
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filials = Filial.objects.filter(company=self.get_group())
        rooms = Rooms.objects.filter(is_working=True).exclude(category__title='office')
        orders = Order.objects.filter(order_start__month=datetime.date.today().month,
                                      order_start__day=datetime.date.today().day, payment_status="PAID").order_by(
            '-order_start')
        # Generate the HTML table
        tablitsa = []
        for filial in filials:
            filtered = rooms.filter(filial=filial)
            html = "<table class='table table-striped-columns table-hover bg-light'>"
            html += f"<td style='background-color:#fcb900;color:white'>{filial}</td>"
            for room in filtered:
                html += f"<td>{room}</td>"
            for sutka in range(23):
                soat = f'{sutka}:00'
                left_start = datetime.datetime.strptime(soat, '%H:%M').time()
                left_end = (datetime.datetime.combine(datetime.datetime.min, left_start) + datetime.timedelta(
                    hours=1)).time()
                left_soat_start = datetime.datetime.combine(datetime.datetime.now().date(), left_start)
                left_soat_end = datetime.datetime.combine(datetime.datetime.now().date(), left_end)

                # from 00:00 to 23:00

                html += f"<tr><td style='padding:0;'>{left_soat_start.strftime('%H:%M')} - {left_soat_end.strftime('%H:%M')}</td>"
                for room in filtered:
                    ord = orders.values('filial__title', 'product__title', 'product', 'client__surname', 'client__name',
                                        'order_start',
                                        'order_end')
                    is_booked = order_exist(ord, room.id, left_soat_start, left_soat_end)
                    if is_booked:
                        html += f"<td style='padding:0;background-color: #36bf14c7;border: 2px springgreen solid;'>{is_booked}</td>"
                    else:
                        html += f"<td style='padding:0;'></td>"
            html += "</table>"
            tablitsa.append(html)
        # Save the HTML document to a file or render it in a Django view

        context['html'] = tablitsa
        context['title'] = 'Главная'
        context['selectMenu'] = 'index'
        context['filials'] = filials
        context['CurrentDay'] = datetime.date.today()
        context['rooms'] = rooms
        context['orders'] = orders
        return context


class ClientsView(ListView):
    model = Client
    template_name = 'crm/clients.html'
    extra_context = {'title': 'Клиенты', "selectMenu": "clients"}

    context_object_name = 'clients'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = Client.objects.order_by('-created_at')
        for client in clients:
            order = Order.objects.filter(client=client).order_by('-order_start').values('order_start').first()
            date = datetime.datetime.now()
            if order is not None:
                days_from_last_order = (date - order['order_start']).days
                if 0 <= days_from_last_order <= 7:
                    client.activity = 4
                elif 8 <= days_from_last_order <= 14:
                    client.activity = 3
                elif 15 <= days_from_last_order <= 30:
                    client.activity = 2
                elif 31 <= days_from_last_order:
                    client.activity = 1
                else:
                    client.activity = 4
            else:
                client.activity = 1
        return context


class OrdersView(ListView):
    model = Order
    template_name = 'crm/orders.html'
    extra_context = {'title': 'Заказы', 'selectMenu': 'orders'}
    context_object_name = 'orders'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     orders = Order.objects.filter().order_by('-created_at')
    #
    #     context["orders"] = orders
    #     return context
    def get_queryset(self):
        orders = Order.objects.all().order_by('-created_at')
        orders = orders.prefetch_related('payments')
        return orders

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for order in context['orders']:
            order.payment_info = order.payments.latest('created_at') if order.payments.exists() else None

        return context

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class OrderUpdate(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'crm/components/todo_form.html'
    extra_context = {'title': 'Изменение заказа'}
    success_url = reverse_lazy('orders')


def profile_view(request, tg_id):
    payments = Payments.objects.filter(order__client=tg_id).order_by('-created_at')
    res = Rooms.objects.filter(is_working=True).values('filial_id', 'filial__title', 'id', 'title').exclude(
        category__title='office')
    abonements = Abonement.objects.all().values("title", 'days', 'price')
    json_abonements = json.dumps(list(abonements), ensure_ascii=False, default=str)
    json_data = json.dumps(list(res))
    pricelist_not_json = Pricelists.objects.all().values('product', 'hour', 'price')
    pricelist = json.dumps(list(pricelist_not_json))

    client = Client.objects.get(telegram_id=tg_id)
    if request.method == 'POST':
        form = ClientEditForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client', tg_id)
    else:
        orders = Order.objects.filter(client=tg_id).order_by('-created_at').exclude(is_deleted=True)
        try:
            office = OfficeRent.objects.get(booked_user=client, is_active=True)
        except:
            office = None
        try:
            abonement = AbonementBuyList.objects.filter(client=tg_id, is_active=True).order_by(
                '-subscription_start')
        except AbonementBuyList.DoesNotExist:
            abonement = None
        context = {
            'client': client,
            'title': 'Страница пользователя',
            'orders': orders,
            'abonement': abonement,
        }
        initial_data = {
            'client': client,
            'discount': client.discount
        }
        form = ClientEditForm(instance=client)
        form2 = AbonementForm(initial=initial_data)
        form3 = OrderForm(initial=initial_data)
        context['payments'] = payments
        context['form'] = form
        context['form2'] = form2
        context['form3'] = form3
        context['office'] = office
        context['pricelist'] = pricelist
        context['json_data'] = json_data
        context['json_abonements'] = json_abonements
        context['products'] = Category.objects.all()
        return render(request, 'crm/client_detail.html', context)


def order_details(request, order_id):
    if request.method == 'POST':
        form = PaymentFormBooking(data=request.POST)
        order = Order.objects.get(pk=order_id)
        client = order.client.telegram_id

        if form.is_valid():
            with transaction.atomic():
                order.payment_status = "PAID"
                order.save()
                form.save()  # Assuming PaymentFormBooking saves related data
                return redirect('client', client)
        else:
            return render(request, 'crm/error.html', context={'error': 'Transaction failed'})

    else:
        order = Order.objects.get(pk=order_id)
        initial_data = {"summa": order.summa_with_discount,
                        "order": order}
        form = PaymentFormBooking(initial=initial_data)
        return render(request, 'crm/components/ordersDetail.html', context={"order": order, 'form': form})


def documentation(request):
    pricelist = Pricelists.objects.all()
    context = {'title': 'Документация', 'pricelist': pricelist, 'selectMenu': 'documentation'}
    return render(request, 'crm/documentation.html', context)


def discount_exists(product_id: int) -> bool:
    room = Rooms.objects.get(pk=product_id)
    category = room.category
    return category.discount


def discounted_price(form, request, hour: int, is_room_discount: bool, price: int):
    discount = request.POST.get('discount')
    try:
        subscribe = AbonementBuyList.objects.get(is_active=True, client_id=request.POST.get('client'))
    except AbonementBuyList.DoesNotExist:
        subscribe = False
    if subscribe and is_room_discount:
        if subscribe.free_time >= hour:
            subscribe.free_time -= hour
            subscribe.save()
            comment = "-50% скидка от подписки"
            form.instance.comment = comment
            form.instance.summa = price
            form.instance.summa_with_discount = price / 2
            return form
        else:
            comment = f"{discount}% скидка"
            form.instance.comment = comment
            form.instance.summa = int(price)
            form.instance.summa_with_discount = int(price - (price / 100 * int(discount)))
            return form
    else:
        comment = f"{discount}% скидка"
        form.instance.comment = comment
        form.instance.summa = int(price)
        form.instance.summa_with_discount = int(price - (price / 100 * int(discount)))
        return form


def order_from_profile(request):
    if request.method == 'POST':
        form = OrderForm(data=request.POST)
        form.instance.added_user = request.user
        hour = int(request.POST.get('hour'))
        product_id = int(request.POST.get('product'))
        price = Pricelists.objects.get(product=product_id, hour=hour).price
        is_room_discount = discount_exists(product_id)  # -> True or False
        form = discounted_price(form=form,
                                request=request,
                                hour=hour,
                                is_room_discount=is_room_discount,
                                price=price)
        client = Client.objects.get(telegram_id=request.POST.get('client'))
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирования прошла успешно')
            return redirect('client', client.telegram_id)
        messages.error(request, f'Произошла ошибка попробуйте ещё раз ,Это времья уже занято')
        return redirect('client', client.telegram_id)


def sale_subscribtion(request):
    tg = request.POST.get('client')
    if request.method == 'POST':
        form = AbonementForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Абонемент подключён')
            return redirect('client', tg)
        else:
            messages.error(request, 'Подключёния не удалось' + f"{request}")
            return redirect('client', tg)


class AddClient(CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'crm/add_client.html'
    extra_context = {'title': 'Создать анкету'}

    def form_valid(self, form):
        form.instance.added_user = self.request.user
        messages.success(self.request, 'Клиент создан')
        return super().form_valid(form)

    def form_invalid(self, form):
        form.instance.added_user = self.request.user
        messages.error(self.request, form.errors)
        return super().form_valid(form)


class AddressView(TemplateView):
    template_name = 'crm/rep_abonements.html'
    extra_context = {'title': 'Отчеты по абонементам'}


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы успешно вошли в аккаунт')
            return redirect('index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
            return redirect('login')
    else:
        form = LoginForm()
        for client in Client.objects.all():
            if client.auto_loyalty:
                client.loyalty = (datetime.datetime.now() - client.created_at).days
            else:
                client.loyalty = client.loyalty

            if client.loyalty < 365:
                client.discount = 0
            elif 365 <= client.loyalty < 730:
                client.discount = 5
            elif 730 <= client.loyalty < 1095:
                client.discount = 10
            elif 1095 <= client.loyalty < 1825:
                client.discount = 15
            else:
                client.discount = 20
            client.save()
    context = {
        'form': form,
        'title': "Авторизация"
    }
    return render(request, 'crm/login.html', context)


def user_logout(request):
    logout(request)
    return redirect('login')


def export_orders_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Orders.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users Data')  # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Клиент', 'Продукт', 'Тип оплаты', 'Статус оплаты',
               'Длительность/Час', 'Cумма', 'Бронирование ОТ', 'Бронирование ДО',
               'Дата заказа']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)  # at 0 row 0 column
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yyyy hh:mm'
    rows = Order.objects.all().values('client',
                                      'product',
                                      'payment_status',
                                      'hour',
                                      'summa',
                                      'created_at',
                                      'order_start',
                                      'order_end')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 0:
                client = str(Client.objects.get(telegram_id=row['client']))
                ws.write(row_num, col_num, client, font_style)
            elif col_num == 1:
                ws.write(row_num, col_num, row['product'], font_style)
            elif col_num == 3:
                if row['payment_status']:
                    ws.write(row_num, col_num, 'Оплачен', date_format)
                else:
                    ws.write(row_num, col_num, 'Не оплачен', date_format)
            elif col_num == 4:
                hour = str(row['hour'])
                ws.write(row_num, col_num, hour, font_style)
            elif col_num == 5:
                ws.write(row_num, col_num, row['summa'], font_style)
            elif col_num == 6:
                ws.write(row_num, col_num, str(row['created_at']), date_format)
            elif col_num == 7:
                ws.write(row_num, col_num, str(row['order_start']), date_format)
            elif col_num == 8:
                ws.write(row_num, col_num, str(row['order_end']), date_format)
            else:
                pass
    wb.save(response)
    return response


def export_clients_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Clients.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Users Data')  # this will make a sheet named Users Data

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Имя', 'Фамилия', 'ТГ-ИД клиента', 'Username',
               'Контакты', 'Комментария', 'Автор', 'Дата создания',
               'Скидка %']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)  # at 0 row 0 column
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yyyy hh:mm'
    rows = Client.objects.all().values('name',
                                       'surname',
                                       'telegram_id',
                                       'username',
                                       'phone',
                                       'comment',
                                       'added_user',
                                       'created_at',
                                       'discount')
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            if col_num == 0:
                ws.write(row_num, col_num, row['name'], font_style)
            elif col_num == 1:
                ws.write(row_num, col_num, row['surname'], font_style)
            elif col_num == 2:
                ws.write(row_num, col_num, row['token'], font_style)
            elif col_num == 3:
                ws.write(row_num, col_num, row['username'], date_format)
            elif col_num == 4:
                ws.write(row_num, col_num, row['phone'], font_style)
            elif col_num == 5:
                ws.write(row_num, col_num, row['comment'], font_style)
            elif col_num == 6:
                ws.write(row_num, col_num, row['added_user'], font_style)
            elif col_num == 7:
                ws.write(row_num, col_num, str(row['created_at']), date_format)
            elif col_num == 8:
                ws.write(row_num, col_num, row['discount'], font_style)
            else:
                pass
    wb.save(response)
    return response


class ExportExcel(View):
    def get(self, request):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Payments-{}.xls"'.format(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        wb = xlwt.Workbook(encoding='utf-8')
        ws_day = wb.add_sheet('Day')
        ws_month = wb.add_sheet('Month')
        ws_quarter = wb.add_sheet('Quarter')
        ws_year = wb.add_sheet('Year')

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Kitoblar', 'Minor', 'Sharq', 'Терминал', 'Наличные', 'Общая сумма']

        for col_num in range(len(columns)):
            ws_day.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncDay('created_at')).values('month').annotate(
            f1=Sum(Case(When(filial=4, payment_status=True, then='summa')), default=0),
            f2=Sum(Case(When(filial=5, payment_status=True, then='summa')), default=0),
            f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
            terminal=Sum(Case(When(payment_status=True, payment=True, then='summa')), default=0),
            nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa')), default=0),
            itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['f1'], row['f2'], row['f3'], row['terminal'], row['nalichka'],
                   row['itogo']]
            for col_num in range(len(row)):
                ws_day.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Kitoblar', 'Minor', 'Sharq', 'Терминал', 'Наличные', 'Общая сумма']

        for col_num in range(len(columns)):
            ws_month.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
            f1=Sum(Case(When(filial=4, payment_status=True, then='summa')), default=0),
            f2=Sum(Case(When(filial=5, payment_status=True, then='summa')), default=0),
            f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
            terminal=Sum(Case(When(payment_status=True, payment=True, then='summa')), default=0),
            nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa')), default=0),
            itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['f1'], row['f2'], row['f3'], row['terminal'], row['nalichka'],
                   row['itogo']]
            for col_num in range(len(row)):
                ws_month.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Kitoblar', 'Minor', 'Sharq', 'Терминал', 'Наличные', 'Общая сумма']

        for col_num in range(len(columns)):
            ws_quarter.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncQuarter('created_at')).values('month').annotate(
            f1=Sum(Case(When(filial=4, payment_status=True, then='summa')), default=0),
            f2=Sum(Case(When(filial=5, payment_status=True, then='summa')), default=0),
            f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
            terminal=Sum(Case(When(payment_status=True, payment=True, then='summa')), default=0),
            nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa')), default=0),
            itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['f1'], row['f2'], row['f3'], row['terminal'], row['nalichka'],
                   row['itogo']]
            for col_num in range(len(row)):
                ws_quarter.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Kitoblar', 'Minor', 'Sharq', 'Терминал', 'Наличные', 'Общая сумма']

        for col_num in range(len(columns)):
            ws_year.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncYear('created_at')).values('month').annotate(
            f1=Sum(Case(When(filial=4, payment_status=True, then='summa')), default=0),
            f2=Sum(Case(When(filial=5, payment_status=True, then='summa')), default=0),
            f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
            terminal=Sum(Case(When(payment_status=True, payment=True, then='summa')), default=0),
            nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa')), default=0),
            itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['f1'], row['f2'], row['f3'], row['terminal'], row['nalichka'],
                   row['itogo']]
            for col_num in range(len(row)):
                ws_year.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response


class ExportExcelProducts(View):
    def get(self, request):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Products-{}.xls"'.format(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        wb = xlwt.Workbook(encoding='utf-8')
        ws_day = wb.add_sheet('Day')
        ws_month = wb.add_sheet('Month')
        ws_quarter = wb.add_sheet('Quarter')
        ws_year = wb.add_sheet('Year')

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Большой митинг рум', 'Малый митинг рум', 'Ивент Зона', 'Рабочая зона', 'Итого']

        for col_num in range(len(columns)):
            ws_day.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncDay('created_at')).values('month').annotate(
            big=Coalesce(Sum(Case(When(payment_status=True, product_id='Большой митинг рум', then='summa'))),
                         0),
            small=Coalesce(Sum(Case(When(payment_status=True, product_id='Малый митинг рум', then='summa'))),
                           0),
            ivent=Coalesce(Sum(Case(When(payment_status=True, product_id='Ивент Зона', then='summa'))), 0),
            work=Coalesce(Sum(Case(When(payment_status=True, product_id='Рабочая зона', then='summa'))), 0),
            itogo=Coalesce(Sum(Case(When(payment_status=True, then='summa'))), 0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['big'], row['small'],
                   row['ivent'], row['work'], row['itogo']]
            for col_num in range(len(row)):
                ws_day.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Большой митинг рум', 'Малый митинг рум', 'Ивент Зона', 'Рабочая зона', 'Итого']

        for col_num in range(len(columns)):
            ws_month.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
            big=Coalesce(Sum(Case(When(payment_status=True, product_id='Большой митинг рум', then='summa'))),
                         0),
            small=Coalesce(Sum(Case(When(payment_status=True, product_id='Малый митинг рум', then='summa'))),
                           0),
            ivent=Coalesce(Sum(Case(When(payment_status=True, product_id='Ивент Зона', then='summa'))), 0),
            work=Coalesce(Sum(Case(When(payment_status=True, product_id='Рабочая зона', then='summa'))), 0),
            itogo=Coalesce(Sum(Case(When(payment_status=True, then='summa'))), 0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['big'], row['small'],
                   row['ivent'], row['work'], row['itogo']]
            for col_num in range(len(row)):
                ws_month.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Большой митинг рум', 'Малый митинг рум', 'Ивент Зона', 'Рабочая зона', 'Итого']

        for col_num in range(len(columns)):
            ws_quarter.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncQuarter('created_at')).values('month').annotate(
            big=Coalesce(Sum(Case(When(payment_status=True, product_id='Большой митинг рум', then='summa'))),
                         0),
            small=Coalesce(Sum(Case(When(payment_status=True, product_id='Малый митинг рум', then='summa'))),
                           0),
            ivent=Coalesce(Sum(Case(When(payment_status=True, product_id='Ивент Зона', then='summa'))), 0),
            work=Coalesce(Sum(Case(When(payment_status=True, product_id='Рабочая зона', then='summa'))), 0),
            itogo=Coalesce(Sum(Case(When(payment_status=True, then='summa'))), 0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['big'], row['small'],
                   row['ivent'], row['work'], row['itogo']]
            for col_num in range(len(row)):
                ws_quarter.write(row_num, col_num, row[col_num], font_style)

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Период', 'Большой митинг рум', 'Малый митинг рум', 'Ивент Зона', 'Рабочая зона', 'Итого']

        for col_num in range(len(columns)):
            ws_year.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        rows = Order.objects.annotate(month=TruncYear('created_at')).values('month').annotate(
            big=Coalesce(Sum(Case(When(payment_status=True, product_id='Большой митинг рум', then='summa'))),
                         0),
            small=Coalesce(Sum(Case(When(payment_status=True, product_id='Малый митинг рум', then='summa'))),
                           0),
            ivent=Coalesce(Sum(Case(When(payment_status=True, product_id='Ивент Зона', then='summa'))), 0),
            work=Coalesce(Sum(Case(When(payment_status=True, product_id='Рабочая зона', then='summa'))), 0),
            itogo=Coalesce(Sum(Case(When(payment_status=True, then='summa'))), 0)).order_by('-month')

        for row in rows:
            row_num += 1
            row = [row['month'].strftime('%d/%m/%Y'), row['big'], row['small'],
                   row['ivent'], row['work'], row['itogo']]
            for col_num in range(len(row)):
                ws_year.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response


# class AddOrder(CreateView):
#     model = Order
#     form_class = OrderForm
#
#     template_name = 'crm/add_order.html'
#     extra_context = {
#         'title': 'Добавить заказ',
#         'json_data': json.dumps(
#             list(Rooms.objects.filter(is_working=True).values('filial_id', 'filial__title', 'id', 'title').exclude(
#                 category__title='office'))),
#         "pricelist": json.dumps(list(Pricelists.objects.all().values('product', 'hour', 'price')))}
#
#     def form_valid(self, form):
#         form.instance.added_user = self.request.user
#         messages.success(self.request, 'Бронирования прошла успешно')
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         messages.error(self.request, 'Произошла ошибка попробуйте ещё раз')
#         return super().form_invalid(form)


# def payment_report(request):
#     orders = Order.objects.all()
#     data_day = orders.annotate(month=TruncDay('created_at')).values('month').annotate(
#         f1=Sum(Case(When(filial=1, payment_status="PAID", then='summa')), default=0),
#         f2=Sum(Case(When(filial=2, payment_status="PAID", then='summa')), default=0),
#         f3=Sum(Case(When(filial=3, payment_status="PAID", then='summa')), default=0),
#         CASH=Sum(Case(When(payment_status="PAID", payment="CASH", then='summa')), default=0),
#         CLICK=Sum(Case(When(payment_status="PAID", payment="CLICK", then='summa')), default=0),
#         UZUM=Sum(Case(When(payment_status="PAID", payment="UZUM", then='summa')), default=0),
#         PAYME=Sum(Case(When(payment_status="PAID", payment="PAYME", then='summa')), default=0),
#         itogo=Sum(Case(When(payment_status="PAID", then='summa')), default=0)).order_by('-month')
#
#     data_month = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
#         f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
#         f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
#         f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
#         terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
#         nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
#         itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')
#
#     data_kvartl = orders.annotate(month=TruncQuarter('created_at')).values('month').annotate(
#         f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
#         f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
#         f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
#         terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
#         nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
#         itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')
#
#     data_year = orders.annotate(month=TruncYear('created_at')).values('month').annotate(
#         f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
#         f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
#         f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
#         terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
#         nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
#         itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')
#     context = {
#         'title': 'Отчёты',
#         'data_month': data_month,
#         'data_kvartl': data_kvartl,
#         'data_day': data_day,
#         'data_year': data_year,
#         'selectMenu': 'reports'
#     }
#     return render(request, 'crm/rep_payments.html', context=context)


def product_report(request):
    orders = Order.objects.all()
    data_day = orders.annotate(month=TruncDay('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')), default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')), default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')), default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')), default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')), default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')), default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')), default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')), default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')
    data_month = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')), default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')), default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')), default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')), default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')), default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')), default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')), default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')), default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')
    data_kvartl = orders.annotate(month=TruncQuarter('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')), default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')), default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')), default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')), default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')), default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')), default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')), default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')), default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')
    data_year = orders.annotate(month=TruncYear('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')), default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')), default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')), default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')), default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')), default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')), default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')), default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')), default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

    context = {
        'title': 'Продукты',
        'data_day': data_day,
        'data_month': data_month,
        'data_kvartl': data_kvartl,
        'data_year': data_year,
    }
    return render(request, 'crm/rep_products.html', context=context)


def abonement_report(request):
    data_day = AbonementBuyList.objects.annotate(month=TruncDay('subscription_start')).values('month').annotate(
        hot=Coalesce(Cast(Sum(Case(When(abonement_id=1, then='abonement__price'))), output_field=models.IntegerField()),
                     0),
        personal=Coalesce(
            Cast(Sum(Case(When(abonement_id=2, then='abonement__price'))), output_field=models.IntegerField()), 0),
        night=Coalesce(
            Cast(Sum(Case(When(abonement_id=3, then='abonement__price'))), output_field=models.IntegerField()), 0),
        itogo=Sum('abonement__price')).order_by('-month')

    data_month = AbonementBuyList.objects.annotate(month=TruncMonth('subscription_start')).values('month').annotate(
        hot=Coalesce(Cast(Sum(Case(When(abonement_id=1, then='abonement__price'))), output_field=models.IntegerField()),
                     0),
        personal=Coalesce(
            Cast(Sum(Case(When(abonement_id=2, then='abonement__price'))), output_field=models.IntegerField()), 0),
        night=Coalesce(
            Cast(Sum(Case(When(abonement_id=3, then='abonement__price'))), output_field=models.IntegerField()), 0),
        itogo=Sum('abonement__price')).order_by('-month')

    data_kvartl = AbonementBuyList.objects.annotate(month=TruncQuarter('subscription_start')).values('month').annotate(
        hot=Coalesce(Cast(Sum(Case(When(abonement_id=1, then='abonement__price'))), output_field=models.IntegerField()),
                     0),
        personal=Coalesce(
            Cast(Sum(Case(When(abonement_id=2, then='abonement__price'))), output_field=models.IntegerField()), 0),
        night=Coalesce(
            Cast(Sum(Case(When(abonement_id=3, then='abonement__price'))), output_field=models.IntegerField()), 0),
        itogo=Sum('abonement__price')).order_by('-month')

    data_year = AbonementBuyList.objects.annotate(month=TruncYear('subscription_start')).values('month').annotate(
        hot=Coalesce(Cast(Sum(Case(When(abonement_id=1, then='abonement__price'))), output_field=models.IntegerField()),
                     0),
        personal=Coalesce(
            Cast(Sum(Case(When(abonement_id=2, then='abonement__price'))), output_field=models.IntegerField()), 0),
        night=Coalesce(
            Cast(Sum(Case(When(abonement_id=3, then='abonement__price'))), output_field=models.IntegerField()), 0),
        itogo=Sum('abonement__price')).order_by('-month')

    context = {
        'data_day': data_day,
        'data_month': data_month,
        'data_kvartl': data_kvartl,
        'data_year': data_year,

    }
    return render(request, 'crm/rep_abonements.html', context=context)


def admins_profile(request):
    orders = Order.objects.filter(status="Closed", is_deleted=False, payment_status=True, added_user=request.user)
    if orders:
        for order in orders:
            try:
                ManagersBonus.objects.create(order_id=order.id,
                                             added_at=order.created_at,
                                             user=order.added_user,
                                             bonus=order.summa / 100 * 1)
            except:
                pass
        all_bonuses = ManagersBonus.objects.filter(user=request.user).aggregate(Sum('bonus'))
        bonus = ManagersBonus.objects.filter(user=request.user).annotate(month=TruncMonth('added_at')).values(
            'month').annotate(summa=Coalesce(Sum('bonus'), 0)).order_by('-month')
        month = datetime.date.today().strftime('%B')
        highest_value = bonus.aggregate(Max('summa'))['summa__max']
        bonus_with_percent = bonus.annotate(
            percent=Case(When(summa=highest_value, then=100), default=F('summa') * 100 / highest_value))
        rekord = 10000000
        way_to_rekord = ceil(all_bonuses["bonus__sum"] * 100 / rekord)
        closed = Order.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
            count=Coalesce(
                Count(Case(When(added_user=request.user, payment_status=True, status='Closed', then='summa'))),
                0)).order_by('-month')
        cancelled = Order.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(
            count=Coalesce(
                Count(Case(When(added_user=request.user, payment_status=True, status='Cancelled', then='summa'))),
                0)).order_by(
            '-month')

        context = {
            "title": "Профиль",
            "month": month,
            "bonus": bonus_with_percent,
            'rekord': rekord,
            'way_to_rekord': way_to_rekord,
            'closed': closed,
            'cancelled': cancelled,
        }
        return render(request, 'crm/admins_profile.html', context)
    else:
        return render(request, 'crm/admins_profile.html')


def abonements_list(request):
    abonements = AbonementBuyList.objects.all().order_by('-subscription_start')
    context = {'abonements': abonements, 'title': 'Абонементы', 'selectMenu': 'abonements'}
    return render(request, 'crm/abonements_list.html', context=context)


def event_list(request):
    event_members_queryset = EventMembers.objects.prefetch_related('members')
    events = Events.objects.prefetch_related(
        Prefetch('eventmembers', queryset=event_members_queryset)
    ).order_by('-event_start_date')
    context = {'events': events, 'title': 'Ивенты', 'selectMenu': 'event_list'}
    return render(request, 'crm/events.html', context=context)


def eventDetail(request, pk):
    event = Events.objects.get(pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES,instance=event)
        if form.is_valid():
            form.save()
            return redirect('event_list')
    else:
        form = EventForm(instance=event)
        context = {'form': form}
        return render(request, 'crm/eventsDetail.html', context=context)


def offices_view(request):
    rents = OfficeRent.objects.filter(is_active=True)
    offices = Rooms.objects.filter(is_working=True, category=5)
    context = {'title': 'Офисы', 'offices': offices, 'rents': rents, 'selectMenu': 'offices'}
    return render(request, 'crm/offices.html', context=context)


def office_details_payment(request, pk):
    rent = OfficeRent.objects.get(pk=pk)
    price = Pricelists.objects.get(product=rent.office.pk).price

    if request.method == "POST":
        with transaction.atomic():
            form = PaymentFormOffice(request.POST)
            form.instance.payment_status = "PAID"

            if form.is_valid():
                rent.is_active = True
                rent.is_paid = True
                rent.save()  # Save rent data first

                payment = form.save(commit=False)  # Create payment object without saving
                payment.officeRent = rent  # Assign rent to the payment
                payment.save()  # Save payment data with rent association

                messages.success(request, "Оплата прошла успешна !")
            else:
                print(form.errors)
                messages.error(request, "Что-то пошло не так .")

        return redirect('office_detail', rent.office.pk)

    form = PaymentFormOffice(initial={'officeRent': rent.pk, 'summa': price})
    try:
        office = Payments.objects.get(officeRent=pk)
    except Payments.DoesNotExist:
        office = []  # Handle case where no existing payment is found

    return render(request, 'crm/office_details_payment.html',
                  context={"pk": pk, "rent": rent, 'title': rent.office, "form": form, 'office': office})


class AddEventView(CreateView):
    model = Events
    form_class = EventForm
    template_name = 'crm/add_event.html'
    extra_context = {'title': 'Новая мероприятия'}

    def form_valid(self, form):
        messages.success(self.request, 'Мероприятия создан')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return super().form_valid(form)


def paymentsView(request):
    payments = Payments.objects.all()
    context = {'payments': payments, 'title': 'Оплаты', 'selectMenu': 'payments'}
    return render(request, 'crm/payments.html', context=context)


def generate_rent_dates(start_date_str, end_date_str):
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    rent_dates = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    return rent_dates


def generate_calendar(year, pk):
    cal = calendar.HTMLCalendar()
    html = ""
    rents_starting_in_january = OfficeRent.objects.filter(office_id=pk)
    for month in range(1, 13):
        start_of_month = datetime.datetime(year, month, 1)
        end_of_month = datetime.datetime(year, month, calendar.monthrange(year, month)[1])
        rent1 = rents_starting_in_january.filter(rent_start__gte=start_of_month, rent_start__lte=end_of_month)
        rent2 = rents_starting_in_january.filter(rent_end__gte=start_of_month, rent_end__lte=end_of_month)
        events = rent1 | rent2
        month_name = calendar.month_name[month]
        month_html = cal.formatmonth(year, month)
        soup = BeautifulSoup(month_html, 'html.parser')
        table = soup.find('table')
        table['class'] = f"month-{month_name.lower()}"
        table['style'] = "width:12%;margin-left:25px;margin-right:25px;margin-bottom:25px"
        thu_cells = soup.find_all('td')
        for event in events:
            rent_dates = generate_rent_dates(str(event.rent_start), str(event.rent_end))
            for cell in thu_cells:
                try:
                    value = datetime.date(year, month, int(cell.text.strip()))
                except ValueError:
                    value = 0
                if value in rent_dates:
                    cell['style'] = f'text-align:center;background-color: {event.color}; font-weight: bold;'
                    cell['href'] = "{{ rent.get_absolute_url }}"
        html += str(soup)
    return html


def office_detail(request, pk):
    if request.method == 'POST':
        form = OfficeRentForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, 'Вы не можете забронировать в этот период')
        return redirect('office_detail', pk)
    office = Rooms.objects.filter(is_working=True, pk=pk).first()
    rents = OfficeRent.objects.filter(office=pk)
    persons = OfficePersons.objects.filter(pk=1)
    form = OfficeRentForm(initial={'office': office})
    title = f'Детали офиса: {office}'
    year = datetime.datetime.today().year
    calendar_html = generate_calendar(year, pk)
    context = {'title': title, 'office': office, 'rents': rents, 'persons': persons, 'form': form,
               'calendar': calendar_html, }
    return render(request, 'crm/office_details.html', context=context)


class VerifyOtpView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to verify OTP.
        """
        data = request.data

        # Check if phone number is provided
        if not data.get('phone_number'):
            return Response({
                'message': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is provided
        if not data.get('otp'):
            return Response({
                'message': 'Key OTP is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Clean up phone number by removing spaces
        phone_number = data.get('phone_number').replace(' ', '')

        try:
            # Retrieve the client based on the phone number
            client = Client.objects.get(phone=phone_number)
        except Client.DoesNotExist:
            return Response({
                'message': 'Invalid phone'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP matches
        if client.otp == data.get('otp'):
            return Response({
                'message': 'OTP success matched',
                'token': client.telegram_id
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Invalid OTP'
        }, status=status.HTTP_400_BAD_REQUEST)

    # The GET method is not necessary here unless you need to handle it separately.
    # If you need GET requests, you can implement it similarly:
    def get(self, request, *args, **kwargs):
        return Response({
            'message': 'GET method not supported for this endpoint'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class Clientapiview(APIView):
    def get(self, request, id):
        lst = Client.objects.filter(telegram_id=id).values()
        return Response(list(lst))


class CompanyView(APIView):
    def get(self, request):
        companies = Company.objects.filter(is_active=True).values('title', 'image', 'is_active')
        data = [
            {
                'title': item['title'],
                'is_working': item['is_active'],
                'images': f"http://{settings.MAIN_HOST}/media/{item['image']}"
                          or f"http://{settings.MAIN_HOST}/media/noimage.jpg"
            }
            for item in companies
        ]
        return Response(list(data))


class CategoryView(APIView):
    def get(self, request):
        categories = Category.objects.filter().values('pk', 'title')
        data = [
            {
                'pk': item['pk'],
                'title': item['title'],
            }
            for item in categories
        ]
        return Response(list(data))


class RoomsByFilialView(APIView):
    def get(self, request, branch_pk):
        rooms = Rooms.objects.filter(filial=branch_pk).exclude(category=5).values('id', 'category', 'title',
                                                                                  'persons', 'is_working')
        fotki = GalleryRooms.objects.all().values('id', 'room', 'image')

        data = [
            {
                'pk': item['id'],
                'title': item['title'],
                'is_working': item['is_working'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki
                           if image['room'] == item['id']
                           ] or [f"http://{settings.MAIN_HOST}/media/noimage.jpg"]
            }
            for item in rooms
        ]

        return Response(list(data))


class Branchesapiview(APIView):
    def get(self, request, company_id):
        lst = Filial.objects.filter(company=company_id).values("id", "company__title", "title", "images", 'address',
                                                               'lat',
                                                               'lang',
                                                               'is_active')
        fotki = Gallery.objects.all().values('filial', 'image')
        data = [
            {
                'pk': item['id'],
                'title': item['title'],
                'company': item['company__title'],
                'address': item['address'],
                'latlang': [item['lat'], item['lang']],

                'is_active': item['is_active'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['filial'] == item['id']]
            }
            for item in lst
        ]
        return Response(data)


class BranchByIDview(APIView):
    def get(self, request, filial_id):
        lst = Filial.objects.filter(id=filial_id).values(
            'id',
            'title',
            'is_active',
            'created_at',
            'token',
            'company',
            'address',
            'lat',
            'lang',

        )
        fotki = Gallery.objects.all().values('filial', 'image')
        data = [
            {
                'pk': item['id'],
                'title': item['title'],
                'is_active': item['is_active'],
                'created_at': item['created_at'],
                'token': item['token'],
                'company': item['company'],
                'address': item['address'],
                'lat': item['lat'],
                'lang': item['lang'],

                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['filial'] == item['id']]
            }
            for item in lst
        ]
        return Response(data)


class Eventsapiview(APIView):
    def get(self, request):
        lst = Events.objects.filter(created_at__lte=datetime.datetime.now()).values(
            "created_at",
            "event_start_date",
            "event_locate__title",
            "title",
            "event_description",
            "image",
        )

        def convert_datetime_to_time_and_date(datetime_str):
            datetime_obj = datetime.datetime.fromisoformat(datetime_str)
            time_str = datetime_obj.strftime("%H:%M")
            date_str = datetime_obj.strftime("%d-%m-%Y")
            return f"{date_str} {time_str}"

        data = [
            {
                "created_at": item["created_at"],
                "event_start_date": convert_datetime_to_time_and_date(str(item["event_start_date"])),
                "event_locate": item["event_locate__title"],
                "title": item["title"],
                "event_description": item["event_description"],
                "image": f"http://{settings.MAIN_HOST}/media/{item['image']}",
            }
            for item in lst
        ]
        return Response(data)


class RoomDetailapiview(APIView):
    def get(self, request, room_id):
        fotki = GalleryRooms.objects.all().values('room', 'image')

        today = timezone.now().date()
        next_week = today + timezone.timedelta(days=6)
        orders = Order.objects.filter(product=room_id).filter(
            Q(order_start__gte=today, order_start__lte=next_week) | Q(order_end__gte=today,
                                                                      order_end__lte=next_week)).values('filial__title',
                                                                                                        'product__title',
                                                                                                        'product',
                                                                                                        'order_start',
                                                                                                        'order_end')

        room = Rooms.objects.filter(pk=room_id).values('pk', 'filial__title', 'title', 'persons', 'area', 'category')
        try:
            productprice = Pricelists.objects.filter(product=room_id).values()
        except:
            productprice = []
        result = []
        day_names = {
            0: "Пн",
            1: "Вт",
            2: "Ср",
            3: "Чт",
            4: "Пт",
            5: "Сб",
            6: "Вс",
        }

        def order_exist(order_start: str, order_end: str) -> bool:
            format_string = "%Y-%m-%d %H:%M:%S"
            zakaz_start = datetime.datetime.strptime(order_start, format_string)
            zakaz_end = datetime.datetime.strptime(order_end, format_string)
            if zakaz_start <= datetime.datetime.now():
                return False
            for i in orders:
                orders_start, orders_end = i['order_start'], i['order_end']
                # Optimized overlap check:
                if zakaz_end > orders_start and zakaz_start < orders_end:
                    return False  # Overlap found, return immediately
            # No overlap found in any order
            return True

        # Create the main dictionary with a key for each day of the week
        for i in range(7):
            day_hour = datetime.datetime.today() + datetime.timedelta(days=i)
            hourly_data = []
            for hour in range(24):
                # Calculate start and end times for the current hour range
                start_time = day_hour.replace(hour=hour, minute=0, second=0)
                end_time = start_time + datetime.timedelta(hours=1)
                # Format times to your preferrestart_timert_time.strd format (e.g., "01:00 - 02:00")
                time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

                # Add time range and placeholder data to hourly_data
                if room[0]['category'] == 4:  # Check for workspace
                    if room[0]['persons'] <= for_workspace(start_time, end_time):
                        status = False
                    else:
                        status = True
                else:
                    status = order_exist(start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                         end_time.strftime('%Y-%m-%d %H:%M:%S'))
                # hourly_data[time_range] = order_exist(start_time.strftime('%Y-%m-%d %H:%M:%S'),end_time.strftime('%Y-%m-%d %H:%M:%S'))
                hourly_data.append({"code": f"{start_time.strftime('%H')}{end_time.strftime('%H')}",
                                    'status': status,
                                    'content': time_range
                                    })
            # result[f"{day_names[day_date.weekday()]} {day_date.day}" if i != 0 else 'Today'] = hourly_data
            # result[f"{start_time.date()}"] = hourly_data
            result.append({
                'date': start_time.date(),
                'times': hourly_data
            })
            # [f'times{i}']=hourly_data

        data = [
            {
                'pk': item['pk'],
                'pricelist': [i for i in productprice],
                'area': item['area'],
                'filial': item['filial__title'],
                'title': item['title'],
                'persons': item['persons'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['room'] == item['pk']],
                'orders': result
            }

            #     'orders': {
            #     'date':"01.02.2024",
            #     'times': {
            #         'times'
            #     }
            # }
            for item in room
        ]
        return Response(data)


class RoomsByCatview(APIView):
    def get(self, request, category_id):
        fotki = GalleryRooms.objects.all().values('room', 'image')

        rooms = Rooms.objects.filter(category=category_id).values(
            'pk',
            'filial__title',
            'category',
            'title',
            'persons',
            'area',
            'is_working',
        )
        data = [
            {
                'pk': item['pk'],
                'filial': item['filial__title'],
                'category': item['category'],
                'title': item['title'],
                'persons': item['persons'],
                'area': item['area'],
                'is_working': item['is_working'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['room'] == item['pk']],

            }
            for item in rooms
        ]
        return Response(list(data))


class RoomsByBranchview(APIView):
    def get(self, request, branchPK):
        fotki = GalleryRooms.objects.all().values('room', 'image')

        rooms = Rooms.objects.filter(filial=branchPK).exclude(category=5).values(
            'pk',
            'filial__title',
            'category__title',
            'title',
            'persons',
            'area',
            'is_working',
        )
        data = [
            {
                'pk': item['pk'],
                'price': Pricelists.objects.filter(product=item['pk']).values("price", 'hour').first(),
                'filial': item['filial__title'],
                'category': item['category__title'],
                'title': item['title'],
                'persons': item['persons'],
                'area': item['area'],
                'is_working': item['is_working'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['room'] == item['pk']],

            }
            for item in rooms
        ]
        return Response(list(data))


class RoomByHourView(APIView):
    def get(self, request, room_id, hour2):
        fotki = GalleryRooms.objects.all().values('room', 'image')

        today = timezone.now().date()
        next_week = today + timezone.timedelta(days=6)
        orders = Order.objects.filter(product=room_id).filter(
            Q(order_start__gte=today, order_start__lte=next_week) | Q(order_end__gte=today,
                                                                      order_end__lte=next_week)).values('filial__title',
                                                                                                        'product__title',
                                                                                                        'product',
                                                                                                        'order_start',
                                                                                                        'order_end')

        room = Rooms.objects.filter(pk=room_id).exclude(category=5).values('pk', 'filial__title', 'filial', 'title',
                                                                           'persons',
                                                                           'area', 'category')
        result = []

        def order_exist(order_start: str, order_end: str) -> bool:
            format_string = "%Y-%m-%d %H:%M:%S"
            zakaz_start = datetime.datetime.strptime(order_start, format_string)
            zakaz_end = datetime.datetime.strptime(order_end, format_string)
            if zakaz_start <= datetime.datetime.now():
                return False
            for i in orders:
                orders_start, orders_end = i['order_start'], i['order_end']
                if zakaz_end > orders_start and zakaz_start < orders_end:
                    return False
            return True

        for i in range(7):
            day_hour = datetime.datetime.today() + datetime.timedelta(days=i)
            hourly_data = []
            for hour in range(24):
                start_time = day_hour.replace(hour=hour, minute=0, second=0)
                end_time = start_time + datetime.timedelta(hours=hour2)
                if end_time > day_hour.replace(hour=23):
                    break
                time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

                # if room[0]['category'] == 4:  # Check for workspace
                #     if room[0]['persons'] <= for_workspace(start_time.time(), end_time.time()):
                #         status = False
                #     else:
                #         status = True
                # else:
                hourly_data.append({"code": f"{start_time.strftime('%H')}{end_time.strftime('%H')}",
                                    'status': order_exist(start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                                          end_time.strftime('%Y-%m-%d %H:%M:%S')),
                                    'content': time_range
                                    })
            result.append({
                'date': start_time.date(),
                'times': hourly_data
            })

        data = [
            {
                'pk': item['pk'],
                'area': item['area'],
                'filial': item['filial__title'],
                'filialpk': item['filial'],
                'title': item['title'],
                'persons': item['persons'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['room'] == item['pk']],
                'orders': result
            }
            for item in room
        ]
        return Response(data)


class SendOTPView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number').replace(' ', '')
        if phone_number is None:
            return Response({
                'message': 'phone_number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        client, created = Client.objects.get_or_create(phone=phone_number)
        client.otp = send_otp_to_phone(phone_number)
        if created:
            client.telegram_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
        client.save()

        return Response({
            'status': status.HTTP_200_OK, 'message': 'OTP sent'})


class ClientChangesView(APIView):
    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        try:
            instance = Client.objects.get(telegram_id=pk)
        except Client.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, **kwargs):
        pk = kwargs.get('pk')
        try:
            instance = Client.objects.get(telegram_id=pk)
        except Client.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Use partial=True to allow partial updates
        serializer = ClientSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AbonementView(APIView):
    def get(self, request):
        abonements = Abonement.objects.all()
        serializer = AbonementSerializer(abonements, many=True)
        return Response(serializer.data)


class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Retrieve the 'telegram_id' from the query parameters
        telegram_id = request.query_params.get('telegram_id', None)
        # Filter orders based on 'telegram_id'
        print(telegram_id)
        if telegram_id:
            orders = Order.objects.filter(client=telegram_id)
        else:
            orders = []
        # Serialize the filtered orders
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
