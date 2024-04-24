import datetime
from .models import AbonementBuyList, Client, NotifyDate, Order


def add_my_forms(request):
    try:
        noti = AbonementBuyList.objects.filter(is_active=True,
                                               subscription_end__lt=datetime.date.today() + datetime.timedelta(days=5))
    except AbonementBuyList.DoesNotExist:
        noti = []
    counts = AbonementBuyList.objects.filter(is_active=True,
                                             subscription_end__lt=datetime.date.today() + datetime.timedelta(
                                                 days=5)).count()
    current_date = datetime.date.today()
    try:
        last_notify = NotifyDate.objects.filter().order_by('-pk')[0]
        if current_date == last_notify.last_send:
            is_send = False
        else:
            is_send = True
    except:
        last_notify = 1
        is_send = False
    return {
        'notifies': noti,
        'current_date': current_date,
        'counts': counts,
        'is_send': is_send,
        'last_notify': last_notify
    }


def deactivete_subscribtion(request):
    eski_abonents = AbonementBuyList.objects.filter(subscription_end__lt=datetime.date.today())
    eski_abonents.update(is_active=False)
    return {
        'eski_abonents': eski_abonents
    }

# def order_remover(request):
#     orders = Order.objects.filter(created_at__lte=datetime.datetime.now() - datetime.timedelta(minutes=30),
#                                   payment_status=False)
#     for order in orders:
#         order.is_deleted = True
#         order.save()
#     print('--- ВСЕ НЕ оплаченные заказы УДАЛЕНЫ (waiting > 30 minute)--- ')
#     return {
#         'orderi': orders
#     }
