import os
from pathlib import Path

from django.contrib import messages
from django.shortcuts import redirect

# from .forms import OrderForm
# from .models import Category, Order, Pricelists, Rooms, AbonementBuyList


# def filter_orders():
#     meeting_rooms = Category.objects.filter(title__contains='Miting')
#     zoom_rooms = Category.objects.filter(title__contains='Zoom')
#     print(meeting_rooms)
#     print(zoom_rooms)
#     orders = Order.objects.all()
#
#     for order in orders:
#         if order.product in meeting_rooms:
#             bookings = Order.objects.filter(
#                 product=order.product,
#                 order_start__lte=order.order_start,
#                 order_end__gte=order.order_end
#             )
#             if len(bookings) < 3:
#                 print('ORDER SAVED----------------------------------------------------------------')
#             else:
#                 print(f"{order.room} is booked more than three times.----------------------------------------------")
#         elif order.product in zoom_rooms:
#             bookings = Order.objects.filter(
#                 room=order.product,
#                 order_start__lte=order.order_end,
#                 order_end__gte=order.order_start
#             )
#             if len(bookings) < 3:
#                 print('ZOOM ROOM SAVED-----------------------------------------------')
#             else:
#                 print(f"{order.product} is booked more than three times.")
#
#
# def discount_exists(product_id: int) -> bool:
#     room = Rooms.objects.get(pk=product_id)
#     category = room.category
#     return category.discount if category else False
#
#
# def discounted_price(form, request, hour, is_room_discount, price):
#     discount = request.POST.get('discount')
#     subscribe = AbonementBuyList.objects.get(is_active=True, client_id=request.POST.get('client'))
#     if subscribe and is_room_discount:
#         if subscribe.free_time >= hour:
#             subscribe.free_time -= hour
#             subscribe.save()
#             comment = "-50% скидка от подписки"
#             form.instance.comment = comment
#             form.instance.summa = price
#             form.instance.summa_with_discount = price / 2
#         else:
#             comment = f"{discount}% скидка"
#             form.instance.comment = comment
#             form.instance.summa = int(price)
#             form.instance.summa_with_discount = int(price - (price / 100 * int(discount)))
#     elif not subscribe:
#         comment = f"{discount}% скидка"
#         form.instance.comment = comment
#         form.instance.summa = int(price)
#         form.instance.summa_with_discount = int(price - (price / 100 * int(discount)))
#
#
# def order_from_profile(request):
#     if request.method == 'POST':
#         form = OrderForm(data=request.POST)
#         form.instance.added_user = request.user
#         hour = int(request.POST.get('hour'))
#         product_id = int(request.POST.get('product'))
#         price = Pricelists.objects.get(product=product_id, hour=hour).price
#         is_room_discount = discount_exists(product_id)  # -> True or False
#         discounted_price(form=form,
#                          request=request,
#                          hour=hour,
#                          is_room_discount=is_room_discount,
#                          price=price)
#
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Бронирования прошла успешно')
#             return redirect('client', request.POST.get('client'))
#         messages.error(request, f'Произошла ошибка попробуйте ещё раз ,Это времья уже занято')
#         return redirect('client', request.POST.get('client'))


import requests

# url = "https://notify.eskiz.uz/api/auth/login"

# payload = {'email': 'myrazamoff@mail.ru',
#            'password': 'QwWvwdmNniNcRgBs3MzWUYEX9moNyx93wZHaKZB8'}
# files = [
#
# ]
# headers = {}
#
# response = requests.request("POST", url, headers=headers, data=payload, files=files)

# print(response.text)


# url = "https://notify.eskiz.uz/api/user/templates"
# payload={}
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjU3NzcwNzIsImlhdCI6MTcyMzE4NTA3Miwicm9sZSI6InRlc3QiLCJzaWduIjoiOTU4MzYzMjViOWQ2M2ExMzg2YzFkZjA2N2I5MThhNDdkODc1NThmYTIzODJmYTljNGM2NmYzMmRjZmQxM2NlZCIsInN1YiI6IjgwODAifQ.rbicPIVX1AiKW8qWTKLK0Gqx5MM60Z8pYu31BYREcfE"
headers = {
    'Authorization': f'Bearer {token}'
}
#
# response = requests.request("GET", url, headers=headers, data=payload)
#
# print(response.text)


# import requests
#
# url = "https://notify.eskiz.uz/api/message/sms/send"
#
# payload = {'mobile_phone': '+998901177094',
#            'message': 'Bu Eskiz dan test',
#            'from': '4546',
#            'callback_url': 'http://0000.uz/test.php'}
# files = [
#
# ]
#
# response = requests.request("POST", url, headers=headers, data=payload, files=files)
#
# print(response.text)


