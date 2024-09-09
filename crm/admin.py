from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *


class GalleryAdmin(admin.TabularInline):
    model = Gallery
    extra = 1
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" height="80" alt="Gallery Image" />')
        return "No image uploaded"

    image_preview.short_description = 'Image'  # Add a descriptive column header


class RoomGalleryAdmin(admin.TabularInline):
    model = GalleryRooms
    extra = 1
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" height="80" alt="Gallery Image" />')
        return "No image uploaded"

    image_preview.short_description = 'Preview'  # Add a descriptive column header


class PriceAdmin(admin.TabularInline):
    model = Pricelists
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'surname', 'telegram_id', 'added_user', 'loyalty','phone']
    list_display_links = ['name', 'surname','phone']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" height="80" alt="Gallery Image" />')
        return "No image uploaded"

    image_preview.short_description = 'Image'  # Add a descriptive column header


@admin.register(Events)
class EventAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'title', 'event_start_date']


@admin.register(Category)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']
    list_display_links = ['title']


@admin.register(Rooms)
class Rooms_in_branchesAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'filial', 'persons', 'is_working']
    list_display_links = ['pk', 'title', 'filial', 'persons']
    list_filter = ['filial']
    inlines = [PriceAdmin, RoomGalleryAdmin]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['pk', 'is_deleted', 'client', 'filial', 'product', 'order_start', 'order_end',
                    'payment_status', 'created_at', 'added_user']
    list_editable = ['filial', 'payment_status']
    list_display_links = ['client']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']
    list_display_links = ['title']


@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title']
    list_display_links = ['title']
    inlines = [GalleryAdmin]


@admin.register(Abonement)
class AbonementAdmin(admin.ModelAdmin):
    list_display = ['title', 'free_time', 'other_loc_work_time', 'price']


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
    list_display_links = ['office']


@admin.register(OfficePersons)
class OfficePersonsAdmin(admin.ModelAdmin):
    list_display = ['id', 'office']


@admin.register(Payments)
class PaymentPersonsAdmin(admin.ModelAdmin):
    list_display = ['created_at','payment',
                    'payment_status',
                    'summa',
                    'order',
                    'abonement',
                    'officeRent',
                    ]
