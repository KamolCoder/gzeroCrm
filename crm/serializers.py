from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.forms import model_to_dict
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Client, Category, Order, AbonementBuyList, Filial, Gallery, Company, Rooms, GalleryRooms
from django.conf import settings


class Clientapiview(APIView):
    def get(self, request, id):
        lst = Client.objects.filter(telegram_id=id).values()
        return Response(list(lst))

    def post(self, request):
        post_new = Client.objects.create(
            name=request.data['name'],
            username=request.data['username'],
            telegram_id=request.data['telegram_id'],
            phone=request.data['phone']
        )
        return Response(model_to_dict(post_new))


class CompanyView(APIView):
    def get(self, request):
        companies = Company.objects.all().values('title', 'image', 'is_active')
        return Response(list(companies))


class Roomsapiview(APIView):
    def get(self, request, company_id):
        lst = Filial.objects.filter(company=company_id).values("id", "company__title", "title", "images", 'address',
                                                               'is_active')
        fotki = Gallery.objects.all().values('filial', 'image')
        data = [
            {
                'title': item['title'],
                'company': item['company__title'],
                'address': item['address'],
                'is_active': item['is_active'],
                'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                           fotki if image['filial'] == item['id']]
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

        room = Rooms.objects.filter(pk=room_id).values('pk', 'filial__title', 'title')
        result = {}
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
            zakaz_start = datetime.strptime(order_start, format_string)
            zakaz_end = datetime.strptime(order_end, format_string)

            for i in orders:
                orders_start, orders_end = i['order_start'], i['order_end']

                # Optimized overlap check:
                if zakaz_end > orders_start and zakaz_start < orders_end:
                    return False  # Overlap found, return immediately

            # No overlap found in any order
            return True

        # Create the main dictionary with a key for each day of the week
        for i in range(7):
            day_date = (datetime.today().date() + timedelta(days=i))
            day_hour = datetime.today() + timedelta(days=i)
            hourly_data = {}
            for hour in range(24):
                # Calculate start and end times for the current hour range
                start_time = day_hour.replace(hour=hour, minute=0, second=0)
                end_time = start_time + timedelta(hours=1)
                # Format times to your preferrestart_timert_time.strd format (e.g., "01:00 - 02:00")
                time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

                # Add time range and placeholder data to hourly_data
                hourly_data[time_range] = order_exist(start_time.strftime('%Y-%m-%d %H:%M:%S'),
                                                      end_time.strftime('%Y-%m-%d %H:%M:%S'))
            result[f"{day_names[day_date.weekday()]} {day_date.day}" if i != 0 else 'Today'] = hourly_data

        data = [
            {'room_pk': item['pk'],
             'filial': item['filial__title'],
             'title': item['title'],
             'images': [f"http://{settings.MAIN_HOST}/media/{image['image']}" for image in
                        fotki if image['room'] == item['pk']],
             'orders': result}
            for item in room
        ]
        return Response(data)
