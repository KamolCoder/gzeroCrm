import datetime
from .models import AbonementBuyList, Client, NotifyDate, Order, OfficeRent, Events


def add_my_forms(request):
    try:
        noti = AbonementBuyList.objects.filter(is_active=True,
                                               subscription_end__lt=datetime.date.today() + datetime.timedelta(days=3))
        abonement_counts = noti.count()
    except AbonementBuyList.DoesNotExist:
        noti = []
        abonement_counts = 0
    try:
        office_noti = OfficeRent.objects.filter(is_active=True,
                                                rent_end__lt=datetime.date.today() + datetime.timedelta(days=3))
        off_noti_counts = office_noti.count()
    except OfficeRent.DoesNotExist:
        office_noti = []
        off_noti_counts = 0

    counts = abonement_counts + off_noti_counts
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
        'office_notifies': office_noti,
        'current_date': current_date,
        'counts': counts,
        'is_send': is_send,
        'last_notify': last_notify
    }


def deactivete_subscribtion(request):
    eski_abonents = AbonementBuyList.objects.filter(subscription_end__lt=datetime.date.today()).update(is_active=False)
    OfficeRent.objects.filter(rent_end__lt=datetime.date.today()).update(is_active=False)
    Events.objects.filter(event_start_date__lt=datetime.date.today()).update(status='COMPLETED')
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
