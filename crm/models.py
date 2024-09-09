import random
import string

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
import django.utils.timezone
from pyclick.models import ClickTransaction


class Company(models.Model):
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=20)
    image = models.ImageField(upload_to='images/companies/', null=True, blank=True, verbose_name='Фото компании')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = '1 Компании'


class Filial(models.Model):
    objects = None
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=20)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, verbose_name='Компания', blank=True, null=True)
    images = models.ImageField(upload_to='images/branches/', null=True, blank=True, verbose_name='Фото филиала')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адрес центра")
    lat = models.FloatField(max_length=255, blank=True, null=True)
    lang = models.FloatField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = '2 Филиалы'


class Category(models.Model):
    objects = None
    title = models.CharField(max_length=255, verbose_name='Название', unique=True)
    limit = models.PositiveSmallIntegerField(default=1, verbose_name='Максимальная длительность брони')
    discount = models.BooleanField(default=False, verbose_name='Free часы для подписчиков')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория комнаты'
        verbose_name_plural = '3 Категории комнат'


class Rooms(models.Model):
    objects = None
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    persons = models.PositiveIntegerField()
    area = models.PositiveIntegerField(verbose_name='Площадь kv/m', blank=True, null=True)
    is_working = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Помещения в филиалах'
        verbose_name_plural = '4 Помещении в филиалах'

    def get_absolute_url(self):
        return reverse('office_detail', kwargs={'pk': self.pk})


class Pricelists(models.Model):
    product = models.ForeignKey(Rooms, on_delete=models.CASCADE, related_name='pricelists')
    hour = models.PositiveSmallIntegerField(verbose_name='Час')
    price = models.PositiveIntegerField(verbose_name='Цена')

    def __str__(self):
        return f"For {self.hour} hours"

    class Meta:
        verbose_name = 'Прайслист'
        verbose_name_plural = 'Прайслисты'


class Abonement(models.Model):
    title = models.CharField(max_length=50, verbose_name='Абонемент')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    days = models.PositiveSmallIntegerField(verbose_name='Срок абонемента/дней')
    work_hour_from = models.TimeField(blank=True, null=True, verbose_name='Рабочая времья от')
    work_hour_to = models.TimeField(blank=True, null=True, verbose_name='Рабочая времья до')
    free_time = models.SmallIntegerField(default=12, validators=[MinValueValidator(0), MaxValueValidator(12)],
                                         verbose_name='-50% на Митинг рум')
    other_loc_work_time = models.PositiveSmallIntegerField(blank=True, null=True, default=3,
                                                           verbose_name="Возможность работать в других локацих")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'


class Client(models.Model):
    objects = None
    profs = [
        ("Programmer", "Программист"),
        ("Web developer", "Веб - разработчик"),
        ("Graphic designer", "Графический дизайнер"),
        ("Web designer", "Веб дизайнер"),
        ("UX/UI designer", "UX / UI дизайнер"),
        ("Marketer", "Маркетолог"),
        ("Advertising specialist", "Специалист по рекламе"),
        ("Writer", "Писатель"),
        ("Copywriter", "Копирайтер"),
        ("Editor", "Редактор"),
        ("Journalist", "Журналист"),
        ("Photographer", "Фотограф"),
        ("Videographer", "Видеограф"),
        ("Business consultant", "Бизнес консультант"),
        ("HR consultant", "HR консультант"),
        ("IT consultant", "IT консультант"),
        ("Startupper", "Стартапер"),
        ("Project manager", "Менеджер проекта"),
        ("Financial analyst", "Финансовые аналитик"),
        ("Accountant", "Бухгалтер"),
        ("SMM specialist", "Специалист по SMM"),
        ("Architect", "Архитектор"),
        ("Engineer", "Инженер"),
        ("Lawyer", "Юрист"),
        ("Legal consultant", "Консультант по праву"),
        ("Researcher", "Исследователь"),
        ("Analyst", "Аналитик"),
        ("Online teacher training", "Учитель онлайн обучение"),
        ("Coaching trainer", "Коучинг тренер"),
        ("Recruiter", "Рекрутер"),
        ("HR specialist", "HR специалист"),
        ("DJ", "Диджей"),
        ("Music producer", "Музыкальные продюсер"),
        ("Event manager", "Эвент - менеджер"),
        ("Event organizer", "Организатор мероприятий"),
        ("Other", 'Другое')]
    name = models.CharField(max_length=50, verbose_name='Имя')
    surname = models.CharField(max_length=50, verbose_name='Фамилия')
    telegram_id = models.TextField(max_length=100, verbose_name='ИД клиента', unique=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True, verbose_name='Фото клиента')
    phone = models.CharField(max_length=20, verbose_name='Контакты', null=True, blank=True)
    comment = models.TextField(verbose_name='Комментария', null=True, blank=True)
    docs = models.FileField(upload_to='docs/users', null=True, blank=True, verbose_name='Документы')
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    discount = models.SmallIntegerField(default=0, verbose_name='Скидка %')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    auto_loyalty = models.BooleanField(default=True)
    loyalty = models.PositiveSmallIntegerField(default=1, verbose_name='Стаж клиента/день')
    activity = models.PositiveSmallIntegerField(default=4, verbose_name='Индекс активности')
    is_banned = models.BooleanField(blank=True, null=True, default=False, verbose_name='Забанен-ли?')
    otp = models.IntegerField(null=True, blank=True)
    profession = models.CharField(choices=profs, max_length=40, null=True, blank=True, verbose_name='Профессия')

    def get_absolute_url(self):
        return reverse('client', kwargs={'tg_id': self.telegram_id})


    def get_contact(self):
        if self.phone:
            return self.phone
        else:
            return '-'

    def file_link(self):
        if self.docs:
            return self.docs.url
        #     return format_html("<a href='%s' class='text-danger'>Скачать</a>" % (self.docs.url,))
        # if self.docs:

    file_link.allow_tags = True

    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return '/static/user.png'

    def __str__(self):
        return f"{self.name} {self.surname}"

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def save(self, *args, **kwargs):
        if not self.telegram_id:
            base_telegram_id = slugify(self.name + " " + self.surname)
            self.telegram_id = base_telegram_id + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
        return super().save(*args, **kwargs)


class AbonementBuyList(models.Model):
    abonement = models.ForeignKey(Abonement, on_delete=models.CASCADE, verbose_name='Абонемент')
    client = models.ForeignKey(Client, to_field='telegram_id', on_delete=models.CASCADE, verbose_name='ID клиента')
    subscription_start = models.DateField(verbose_name='Начало подписки', blank=True)
    subscription_end = models.DateField(verbose_name='Конец подписки', blank=True)
    free_time = models.SmallIntegerField(default=12, validators=[MinValueValidator(0), MaxValueValidator(15)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.abonement.title}'

    class Meta:
        verbose_name = 'Данные покупки абонемента'
        verbose_name_plural = 'Журнал покупок абонементов'


class GalleryRooms(models.Model):
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Room',
                             related_name='room_image')
    image = models.ImageField(upload_to='images/rooms', blank=True, null=True, verbose_name='Image')

    def __str__(self):
        return f"{self.pk}"

    class Meta:
        verbose_name = 'Rooms image'
        verbose_name_plural = 'Rooms images'


class Gallery(models.Model):
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Filial',
                               related_name='documents')
    image = models.ImageField(upload_to='images/branch', blank=True, null=True, verbose_name='Image')

    def __str__(self):
        return 'Photo'

    class Meta:
        verbose_name = 'Filials image'
        verbose_name_plural = 'Filials images'


class Order(models.Model):
    objects = None
    PAYMENT_STATUS = [('PAID', 'ОПЛАЧЕН'), ('UNPAID', 'НЕОПЛАЧЕН')]
    client = models.ForeignKey(Client, to_field="telegram_id", on_delete=models.CASCADE, verbose_name='Клиент')
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE)
    product = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    hour = models.PositiveSmallIntegerField(verbose_name='Длительность')
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=30, verbose_name="Статус оплаты",default="UNPAID")
    summa = models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Сумма', blank=True, null=True)
    summa_with_discount = models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Сумма со скидкой',blank=True, null=True)
    order_start = models.DateTimeField(verbose_name='Бронировать от :')
    order_end = models.DateTimeField(verbose_name='Бронировать до :')
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    pay_accept_user = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True, verbose_name='Комментария')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')
    discount = models.PositiveSmallIntegerField(default=0)
    payment_detail = models.ForeignKey(ClickTransaction, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Заказ-№{self.pk}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def get_absolute_url(self):
        return reverse('ordersDetail', kwargs={'order_id': self.pk})


class ManagersBonus(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    bonus = models.PositiveIntegerField(default=0, verbose_name='Сумма бонуса')
    added_at = models.DateTimeField(verbose_name='Дата зачисления')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Бонус'
        verbose_name_plural = 'Бонусы'


class NotifyDate(models.Model):
    objects = None
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_send = models.DateField(verbose_name='Дата отправки')
    sent_time = models.DateTimeField(auto_now_add=True, verbose_name='Времья отправки')

    class Meta:
        verbose_name = 'Дата отправки уведом.'
        verbose_name_plural = 'Дата отправки уведом.'


def generate_bright_hex_color():
    """Generates a random bright hexadecimal color code."""

    def bright_value():
        return random.randint(150, 255)  # Adjust range as needed

    return '#{:02X}{:02X}{:02X}'.format(bright_value(), bright_value(), bright_value())


class OfficeRent(models.Model):
    objects = None
    office = models.ForeignKey(Rooms, on_delete=models.DO_NOTHING)
    rent_start = models.DateField(verbose_name='Начало бронирование')
    rent_end = models.DateField(verbose_name='Конец бронирование')
    booked_user = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Кто бронировал')
    is_active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=7, blank=True, null=True, unique=True)

    def __str__(self):
        return f"Аренда-№{self.pk}"

    def save(self, *args, **kwargs):
        if not self.color:
            while True:
                color = generate_bright_hex_color()
                if not OfficeRent.objects.filter(color=color).exists():
                    self.color = color
                    break
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('office_details_payment', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Аренда офиса'
        verbose_name_plural = 'Аренда офисов'


class OfficePersons(models.Model):
    objects = None
    created_at = models.DateTimeField(auto_now_add=True)
    office = models.ForeignKey(OfficeRent, on_delete=models.CASCADE)
    person = models.ForeignKey(Client, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Офисник'
        verbose_name_plural = 'Офисники'


class Events(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    event_start_date = models.DateTimeField(verbose_name='Дата ивента')
    event_locate = models.ForeignKey(Filial, on_delete=models.PROTECT, verbose_name='Адрес ивента')
    title = models.TextField(max_length=255, verbose_name='Заголовка')
    event_description = models.TextField(verbose_name='Описания')
    image = models.ImageField(upload_to='images/', verbose_name='Постер', blank=True, null=True)

    class Meta:
        verbose_name = 'Мероприятия'
        verbose_name_plural = 'Мероприятии'

    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return '/static/user.png'

    def get_absolute_url(self):
        return reverse('event_list')


class Payments(models.Model):
    CLICK = 'CLICK'
    PAYME = "PAYME"
    CASH = 'CASH'
    UZUM = 'UZUM'
    PAYMENTS = [(CLICK, CLICK), (PAYME, PAYME), (CASH, CASH), (UZUM, UZUM)]
    PAYMENT_STATUS = [('PAID', 'ОПЛАЧЕН'), ('UNPAID', 'НЕОПЛАЧЕН')]
    payment = models.CharField(choices=PAYMENTS, blank=True, max_length=30, null=True, verbose_name='Тип оплаты')
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=30, verbose_name="Статус оплаты",
                                      default="PAID")
    summa = models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Сумма', blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Комната',related_name="payments")
    abonement = models.ForeignKey(AbonementBuyList, on_delete=models.CASCADE, blank=True, null=True,
                                  verbose_name='абонемент')
    officeRent = models.ForeignKey(OfficeRent, on_delete=models.CASCADE, blank=True, null=True, verbose_name='аренда')
    created_at = models.DateTimeField(auto_now_add=True)
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
