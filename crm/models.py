from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
import django.utils.timezone


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

    class Meta:
        verbose_name = 'Прайслист'
        verbose_name_plural = 'Прайслисты'


class Abonement(models.Model):
    title = models.CharField(max_length=50, verbose_name='Абонемент')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    days = models.PositiveSmallIntegerField(verbose_name='days')

    def __str__(self):
        return f"{self.title} {self.price}"

    class Meta:
        verbose_name = 'Абонемент'
        verbose_name_plural = 'Абонементы'


class Client(models.Model):
    objects = None
    languages = [("en", 'English'), ("ru", 'Russian'), ("uz", 'Uzbek')]
    tg_lang = models.CharField(max_length=10, choices=languages, default='ru', blank=True, null=True)
    name = models.CharField(max_length=50, verbose_name='Имя')
    surname = models.CharField(max_length=50, verbose_name='Фамилия')
    telegram_id = models.TextField(max_length=100, verbose_name='ТГ-ИД клиента', unique=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True, verbose_name='Фото клиента')
    username = models.CharField(max_length=50, verbose_name='tg-username', null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name='Контакты', null=True, blank=True)
    comment = models.TextField(verbose_name='Комментария', null=True, blank=True)
    docs = models.FileField(upload_to='docs/users', null=True, blank=True, verbose_name='Документы')
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    discount = models.SmallIntegerField(default=0, verbose_name='Скидка %')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    loyalty = models.PositiveSmallIntegerField(default=1, verbose_name='Стаж клиента/день')
    activity = models.PositiveSmallIntegerField(default=4, verbose_name='Индекс активности')

    def get_absolute_url(self):
        return reverse('client', kwargs={'telegram_id': self.telegram_id})

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


class AbonementBuyList(models.Model):
    abonement = models.ForeignKey(Abonement, on_delete=models.CASCADE, verbose_name='Абонемент')
    client = models.ForeignKey(Client, to_field='telegram_id', on_delete=models.CASCADE, verbose_name='ID клиента')
    subscription_start = models.DateField(verbose_name='Начало подписки', blank=True)
    subscription_end = models.DateField(verbose_name='Конец подписки', blank=True)
    # subscription_end = models.DateField(default=subscription_start + datetime.timedelta(days=29),verbose_name='Конец подписки')
    free_time = models.SmallIntegerField(default=15, validators=[MinValueValidator(0), MaxValueValidator(15)])
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.abonement.title}'

    class Meta:
        verbose_name = 'Купленный абонемент'
        verbose_name_plural = 'Купленные абонементы'


class Gallery(models.Model):
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Filial',
                               related_name='documents')
    image = models.ImageField(upload_to='images/branch', blank=True, null=True, verbose_name='Image')

    class Meta:
        verbose_name = 'fotki'
        verbose_name_plural = 'Библиотека fotok'


class Order(models.Model):
    objects = None
    IS_PAID_CHOICES = [(False, 'Наличные'), (True, 'Карта')]
    IS_STATUS = [
        ('Waiting', 'Ожидание'),
        ('Cancelled', 'Отменено'),
        ('Active', 'В процессе'),
        ('Closed', 'Закрыто')
    ]
    client = models.ForeignKey(Client, to_field="telegram_id", on_delete=models.CASCADE, verbose_name='Клиент')
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE)
    product = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    hour = models.PositiveSmallIntegerField(verbose_name='Длительность')
    payment = models.BooleanField(choices=IS_PAID_CHOICES, default=False, verbose_name='Тип оплаты')
    payment_status = models.BooleanField(verbose_name="Оплачен", default=False)
    summa = models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Сумма', blank=True, null=True)
    order_start = models.DateTimeField(verbose_name='Бронировать от :')
    order_end = models.DateTimeField(verbose_name='Бронировать до :')
    added_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    pay_accept_user = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True, verbose_name='Комментария')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания')
    status = models.CharField(max_length=30, choices=IS_STATUS, default='Waiting')
    discount = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.pk} {self.product}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def get_absolute_url(self):
        return reverse('orders')


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


class OfficeRent(models.Model):
    office = models.ForeignKey(Rooms, on_delete=models.DO_NOTHING)
    rent_start = models.DateField(verbose_name='Начало бронирование')
    rent_end = models.DateField(verbose_name='Конец бронирование')
    booked_user = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name='Кто бронировал')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.office}"

    class Meta:
        verbose_name = 'Аренда офиса'
        verbose_name_plural = 'Аренда офисов'


class OfficePersons(models.Model):
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
    image = models.ImageField(verbose_name='Постер', blank=True, null=True)

    class Meta:
        verbose_name = 'Мероприятия'
        verbose_name_plural = 'Мероприятии'
