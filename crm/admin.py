from django.contrib import admin
from .models import *


class GalleryAdmin(admin.TabularInline):
    model = Gallery
    extra = 1


class PriceAdmin(admin.TabularInline):
    model = Pricelists
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'telegram_id', 'added_user', 'loyalty']
    list_display_links = ['name', 'surname']


@admin.register(Events)
class EventAdmin(admin.ModelAdmin):
    list_display = ['created_at','title','event_start_date']


@admin.register(Category)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']


@admin.register(Rooms)
class Rooms_in_branchesAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'filial', 'persons','is_working']
    list_display_links = ['pk','title', 'filial', 'persons']
    inlines = [PriceAdmin]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'is_deleted', 'client', 'filial', 'product', 'order_start', 'order_end',
                    'status', 'created_at', 'added_user']
    list_editable = ['filial', 'status']
    list_display_links = ['client']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']


@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']
    inlines = [GalleryAdmin]


@admin.register(Abonement)
class AbonementAdmin(admin.ModelAdmin):
    list_display = ['title', 'price']


@admin.register(AbonementBuyList)
class AbonementBuyListAdmin(admin.ModelAdmin):
    list_display = ['abonement', 'client', 'subscription_start', 'subscription_end', 'is_active']
    list_editable = ['is_active']


@admin.register(ManagersBonus)
class ManagersBonusAdmin(admin.ModelAdmin):
    list_display = ['order', 'bonus', 'user', 'added_at']


@admin.register(NotifyDate)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'last_send', 'sent_time']


@admin.register(OfficeRent)
class OfficeRentAdmin(admin.ModelAdmin):
    list_display = ['id', 'office', 'rent_start', 'rent_end', 'is_active']


@admin.register(OfficePersons)
class OfficePersonsAdmin(admin.ModelAdmin):
    list_display = ['id', 'office']
