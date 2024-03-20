import json
from math import ceil
import requests
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, Sum, Max, F, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncDay, TruncYear, TruncQuarter, Coalesce, Cast
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, CreateView, TemplateView, UpdateView, DeleteView
import xlwt
from .forms import ClientForm, LoginForm, OrderForm, AbonementForm
from .models import *
import datetime


def order_exist(orders, product, order_start: datetime, order_end: datetime) -> str:
    order = orders.filter(product=product)
    for i in order:
        orders_start, orders_end = i['order_start'], i['order_end']
        if order_end > orders_start and order_start < orders_end:
            return f"{i['client']}"
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
        rooms = Rooms.objects.all().exclude(category__title='office')
        orders = Order.objects.filter(order_start__month=datetime.date.today().month,
                                      order_start__day=datetime.date.today().day, payment_status=1).order_by(
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

                html += f"<tr><td style='padding:0'>{left_soat_start.strftime('%H:%M')} - {left_soat_end.strftime('%H:%M')}</td>"
                for room in filtered:
                    ord = orders.values('filial__title', 'product__title', 'product', 'client', 'order_start',
                                        'order_end')
                    is_booked = order_exist(ord, room.id, left_soat_start, left_soat_end)
                    if is_booked:
                        html += f"<td style='padding:0;background-color:#ff0000a6'>{is_booked}</td>"
                    else:
                        html += f"<td style='padding:0;'></td>"
            html += "</table>"
            tablitsa.append(html)
        # Save the HTML document to a file or render it in a Django view

        context['html'] = tablitsa
        context['title'] = 'Главная'
        context['filials'] = filials
        context['CurrentDay'] = datetime.date.today()
        context['rooms'] = rooms
        context['orders'] = orders
        return context


class ClientsView(ListView):
    model = Client
    template_name = 'crm/clients.html'
    extra_context = {'title': 'Клиенты'}
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
    extra_context = {'title': 'Заказы'}
    context_object_name = 'orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = Order.objects.filter().order_by('-created_at')

        context["orders"] = orders
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


def order_delete(request, pk):
    try:
        Order.objects.filter(pk=pk).update(is_deleted=not Order.objects.get(pk=pk).is_deleted)
        return redirect('orders')
    except Order.DoesNotExist:
        return redirect('orders')


def profile_view(request, telegram_id):
    res = Rooms.objects.all().values('filial_id', 'filial__title', 'id', 'title').exclude(category__title='office')
    json_data = json.dumps(list(res))
    pricelist_not_json = Pricelists.objects.all().values('product', 'hour', 'price')
    pricelist = json.dumps(list(pricelist_not_json))
    if request.method == 'POST':
        client = Client.objects.get(telegram_id=telegram_id)
        form = ClientForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client', client.telegram_id)
    else:
        orders = Order.objects.filter(client_id=telegram_id).order_by('-created_at')
        client = Client.objects.get(telegram_id=telegram_id)
        try:
            abonement = AbonementBuyList.objects.filter(client_id=telegram_id).order_by('-subscription_start')
        except AbonementBuyList.DoesNotExist:
            abonement = None
        context = {
            'client': client,
            'title': 'Страница пользователя',
            'orders': orders,
            'abonement': abonement
        }
        initial_data = {
            'client': client,
            'discount': client.discount,
            # 'filial': request.user.groups.all()[1]
        }
        form = ClientForm(instance=client)
        form2 = AbonementForm(initial=initial_data)
        form3 = OrderForm(initial=initial_data)
        context['form'] = form
        context['form2'] = form2
        context['pricelist'] = pricelist
        context['json_data'] = json_data
        context['form3'] = form3
        context['products'] = Category.objects.all()
        return render(request, 'crm/client_detail.html', context)


def documentation(request):
    pricelist = Pricelists.objects.all()
    context = {'title': 'Документация', 'pricelist': pricelist}
    return render(request, 'crm/documentation.html', context)


def order_from_profile(request):
    if request.method == 'POST':
        current_date = request.POST.get('order_start')
        Order.objects.annotate(date=TruncDate("order_start")).filter(product=request.POST.get('product'),
                                                                     date=current_date.split('T')[0]).values(
            'order_start', 'order_end')
        form = OrderForm(data=request.POST)
        form.instance.added_user = request.user
        if request.POST.get('payment_status'):
            form.instance.pay_accept_user = f"{request.user}\n{datetime.datetime.now()}"
        else:
            form.instance.pay_accept_user = ''
        hour = int(request.POST.get('hour'))
        product_id = int(request.POST.get('product'))
        price = Pricelists.objects.get(product=product_id, hour=hour).price
        try:
            subs = AbonementBuyList.objects.get(is_active=True, client_id=request.POST.get('client'))
            if subs.free_time >= hour:
                subs.free_time -= hour
                subs.save()
                comment = "-50%"
                form.instance.comment = comment
                price = price / 2
        except:
            price = int(price - (price / 100 * int(request.POST.get('discount'))))
        form.instance.comment = ''
        form.instance.summa = price
        if form.is_valid():
            form.save()
            messages.success(request, 'Бронирования прошла успешно')
            return redirect('client', request.POST.get('client'))
        else:
            messages.error(request, f'Произошла ошибка попробуйте ещё раз ,Это времья уже занято')
            return redirect('orders')


def sale_abon(request):
    tg = request.POST.get('client')
    if request.method == 'POST':
        form = AbonementForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Абонемент подключён')
            return redirect('client', tg)
        else:
            messages.error(request, 'Подключёния не удалось \n' + request.error_message)
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
            client.loyalty = (datetime.datetime.now() - client.created_at).days
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
                                      'payment',
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
            elif col_num == 2:
                if row['payment']:
                    ws.write(row_num, col_num, "Карта", font_style)
                else:
                    ws.write(row_num, col_num, "Наличные", font_style)
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
                ws.write(row_num, col_num, row['telegram_id'], font_style)
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


class AddOrder(CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'crm/add_order.html'
    extra_context = {'title': 'Добавить заказ'}

    def form_valid(self, form):
        form.instance.added_user = self.request.user
        messages.success(self.request, 'Бронирования прошла успешно')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Произошла ошибка попробуйте ещё раз')
        return super().form_invalid(form)


def payment_report(request):
    orders = Order.objects.all()
    data_day = orders.annotate(month=TruncDay('created_at')).values('month').annotate(
        f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
        f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
        f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
        terminal=Sum(Case(When(payment_status=True, payment=True, then='summa')), default=0),
        nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa')), default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')), default=0)).order_by('-month')

    data_month = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
        f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
        f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
        f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
        terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
        nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
        itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')

    data_kvartl = orders.annotate(month=TruncQuarter('created_at')).values('month').annotate(
        f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
        f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
        f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
        terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
        nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
        itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')

    data_year = orders.annotate(month=TruncYear('created_at')).values('month').annotate(
        f1=Sum(Case(When(filial=1, payment_status=True, then='summa')), default=0),
        f2=Sum(Case(When(filial=2, payment_status=True, then='summa')), default=0),
        f3=Sum(Case(When(filial=3, payment_status=True, then='summa')), default=0),
        terminal=Sum(Case(When(payment_status=True, payment=True, then='summa'))),
        nalichka=Sum(Case(When(payment_status=True, payment=False, then='summa'))),
        itogo=Sum(Case(When(payment_status=True, then='summa')))).order_by('-month')
    context = {
        'title': 'Оплаты',
        'data_month': data_month,
        'data_kvartl': data_kvartl,
        'data_day': data_day,
        'data_year': data_year
    }
    return render(request, 'crm/rep_payments.html', context=context)


def product_report(request):
    orders = Order.objects.all()
    data_day = orders.annotate(month=TruncDay('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')),default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')),default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')),default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')),default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')),default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')),default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')),default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')),default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')),default=0)).order_by('-month')
    data_month = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')),default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')),default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')),default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')),default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')),default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')),default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')),default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')),default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')),default=0)).order_by('-month')
    data_kvartl = orders.annotate(month=TruncQuarter('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')),default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')),default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')),default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')),default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')),default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')),default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')),default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')),default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')),default=0)).order_by('-month')
    data_year = orders.annotate(month=TruncYear('created_at')).values('month').annotate(
        work=Sum(Case(When(payment_status=True, product__title='Open Space', then='summa')),default=0),
        miting6=Sum(Case(When(payment_status=True, product__title='Miting room 6', then='summa')),default=0),
        miting8=Sum(Case(When(payment_status=True, product__title='Miting room 8', then='summa')),default=0),
        miting10=Sum(Case(When(payment_status=True, product__title='Miting room 10', then='summa')),default=0),
        miting12=Sum(Case(When(payment_status=True, product__title='Miting room 12', then='summa')),default=0),
        miting16=Sum(Case(When(payment_status=True, product__title='Miting room 16', then='summa')),default=0),
        ivent=Sum(Case(When(payment_status=True, product__title='Event-Zone', then='summa')),default=0),
        zoom=Sum(Case(When(payment_status=True, product__title='Zoom room', then='summa')),default=0),
        itogo=Sum(Case(When(payment_status=True, then='summa')),default=0)).order_by('-month')

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


def change_status(request, order_id, action):
    """Функция изменение статуса заказа"""
    order = Order.objects.get(pk=order_id)
    if action == 'Activate':
        order.status = 'Active'
    elif action == 'Close':
        order.status = 'Closed'
    elif action == 'Waiting':
        order.status = 'Waiting'
    else:
        order.status = 'Cancelled'
        order.payment_status = False
        if order.product.title == 'Ивент Зона':
            try:
                subs = AbonementBuyList.objects.get(client=order.client_id, is_active=True)
                if subs:
                    subs.free_time += int(order.hour)
                subs.save()
            except Exception as e:
                pass
        else:
            pass
    order.save()
    return redirect('index')


def confirm_payment(request, order_id, action):
    order = Order.objects.get(pk=order_id)
    if action == 'Confirm':
        order.payment_status = True
        order.pay_accept_user = f"{request.user}\n{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    order.save()
    return redirect('orders')


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
    context = {'abonements': abonements, 'title': 'Абонементы'}
    return render(request, 'crm/abonements_list.html', context=context)


def send_to_client(request):
    # bot_token = ""
    users = AbonementBuyList.objects.filter(subscription_end__lt=datetime.date.today() + datetime.timedelta(days=5),
                                            is_active=True)
    for i in users:
        chat_id = i.client.telegram_id
        message = f"""Добрый день, {i.client}!
Как ваши дела ? 

Спешу напомнить Вам о том, что до окончания действия вашего абонемента {i} осталось меньше 5 дней.

По желанию можете приобрести новый абонемент у нас на кассе.

Оплатить можно наличными либо картой Uzcard или Humo😊"""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
        requests.get(url)
    current_date = datetime.date.today()
    NotifyDate.objects.create(user=request.user, last_send=current_date)
    messages.success(request, "📨 Отправлено")

    return redirect('index')


def offices_view(request):
    rents = OfficeRent.objects.filter(is_active=True)
    offices = Rooms.objects.filter(category__title='Office')
    context = {'title': 'Офисы', 'offices': offices, 'rents': rents}
    return render(request, 'crm/offices.html', context=context)


def office_detail(request, pk):
    office = Rooms.objects.filter(pk=pk)
    rents = OfficeRent.objects.filter(office=pk)
    persons = OfficePersons.objects.filter(pk=1)
    try:
        title = office[0].desc
    except:
        title = 'Детали офиса'
    context = {'title': title, 'office': office, 'rents': rents, 'persons': persons}
    return render(request, 'crm/office_details.html', context=context)
