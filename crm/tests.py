from .models import Category, Order

def filter_orders():
    meeting_rooms = Category.objects.filter(title__contains='Miting')
    zoom_rooms = Category.objects.filter(title__contains='Zoom')
    print(meeting_rooms)
    print(zoom_rooms)
    orders = Order.objects.all()

    for order in orders:
        if order.product in meeting_rooms:
            bookings = Order.objects.filter(
                product=order.product,
                order_start__lte=order.order_start,
                order_end__gte=order.order_end
            )
            if len(bookings) < 3:
                print('ORDER SAVED----------------------------------------------------------------')
            else:
                print(f"{order.room} is booked more than three times.----------------------------------------------")
        elif order.product in zoom_rooms:
            bookings = Order.objects.filter(
                room=order.product,
                order_start__lte=order.order_end,
                order_end__gte=order.order_start
            )
            if len(bookings) < 3:
                print('ZOOM ROOM SAVED-----------------------------------------------')
            else:
                print(f"{order.product} is booked more than three times.")
