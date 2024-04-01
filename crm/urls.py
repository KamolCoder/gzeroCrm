from django.urls import path
from .serializers import Clientapiview, CompanyView, Roomsapiview, RoomDetailapiview
from .views import *

urlpatterns = [
    path('', user_login, name='login'),
    path('logout/', user_logout, name="logout"),
    path('index/', IndexView.as_view(), name='index'),
    path('clients/', ClientsView.as_view(), name='clientview'),
    path('offices/', offices_view, name='offices'),
    path('office/<int:pk>', office_detail, name='office_detail'),
    path('abonements_list/', abonements_list, name='abonements_list'),
    path('event_list/', event_list, name='event_list'),
    path('documentation/', documentation, name='documentation'),
    path('client/<telegram_id>/', profile_view, name='client'),
    path('add_client/', AddClient.as_view(), name='add_client'),
    path('orders/excel', export_orders_xls, name='export_excel'),
    path('clients/excel', export_clients_xls, name='export_client'),
    path('payments/download', ExportExcel.as_view(), name='download'),
    path('products/download', ExportExcelProducts.as_view(), name='download_products'),
    path('add_order/', AddOrder.as_view(), name='add_order'),
    path('order_from_profile/', order_from_profile, name='order_from_profile'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('orders/<int:pk>/update', OrderUpdate.as_view(), name='update'),
    path('orders/<int:pk>/delete', order_delete, name='delete'),

    path('reports/', payment_report, name='reports'),
    path('abonements/', abonement_report, name='abonements'),
    path('products/', product_report, name='products'),
    path('admins_profile/', admins_profile, name='admins_profile'),

    path('sale_abon/', sale_abon, name='sale_abon'),
    path('change_status/<int:order_id>/<str:action>/', change_status, name='change_status'),
    path('confirm_payment/<int:order_id>/<str:action>/', confirm_payment, name='confirm_payment'),

    path('apiclient/<str:id>/', Clientapiview.as_view()),
    path('api/companies/', CompanyView.as_view()),
    path('api/rooms/<int:company_id>', Roomsapiview.as_view()),
    path('api/room/<int:room_id>', RoomDetailapiview.as_view()),
]
