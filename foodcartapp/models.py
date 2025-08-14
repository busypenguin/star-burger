from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import Sum, F, Count
from django.utils import timezone
from collections import defaultdict


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def order_cost(self):
        return self.annotate(
            order_cost=Sum(
                F('order_products__product__price') * F('order_products__quantity')
                )
            )

    def get_available_restaurants(self):
        rest_items = RestaurantMenuItem.objects.filter(availability=True)
        rests_with_products = defaultdict(set)

        for item in rest_items:
            rests_with_products[item.restaurant].add(item.product)

        for order in self:
            products = {order_product.product for order_product in order.order_products.all()}
            available_restaurants = []

            for restaurant, restaurant_products in rests_with_products.items():
                if products.issubset(restaurant_products):
                    available_restaurants.append(restaurant)

            order.available_restaurants = available_restaurants
        return self


class Order(models.Model):
    ORDER_STATUSES = [
        ('NEW', 'Необработанный'),
        ('PROCESSING', 'Готовится'),
        ('IN_TRANSIT', 'Доставляется'),
        ('DONE', 'Выполнен')
        ]
    PAYMENT_STATUSES = [
        ('NOT_PAID', 'Не оплачено'),
        ('ONLINE', 'Электронно'),
        ('CASH', 'Наличностью')
    ]
    status = models.CharField(
        verbose_name='статус',
        max_length=50,
        default='NEW',
        choices=ORDER_STATUSES,
        db_index=True
    )
    payment_method = models.CharField(
        verbose_name='способ оплаты',
        max_length=50,
        default='NOT_PAID',
        choices=PAYMENT_STATUSES,
        db_index=True
    )
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='restaurant_orders',
        verbose_name="ресторан",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    firstname = models.CharField(
        verbose_name='имя',
        max_length=50
    )
    lastname = models.CharField(
        verbose_name='фамилия',
        max_length=50
    )
    phonenumber = PhoneNumberField(
        region="RU",
        verbose_name='телефон',
        max_length=50
    )
    address = models.CharField(
        verbose_name='адрес',
        max_length=100
    )
    comment = models.TextField(
        verbose_name='Комментарий',
        blank=True,
        max_length=200
    )
    registrated_at = models.DateTimeField(
        verbose_name='зарегестрировано',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        verbose_name='согласовано',
        null=True,
        blank=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        verbose_name='доставлено',
        null=True,
        blank=True,
        db_index=True
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}"

    def set_restaurant(self, restaurant):
        self.restaurant = restaurant
        if restaurant and self.status == 'NEW':
            self.status = 'PROCESSING'
            self.save()
        return self


class OrderProduct(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='заказ',
        on_delete=models.CASCADE,
        related_name='order_products'
    )
    product = models.ForeignKey(
        Product,
        verbose_name='продукт',
        on_delete=models.CASCADE,
        related_name='order_products'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='количество',
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'стоимость',
        max_digits=8,
        decimal_places=2
    )

    class Meta:
        verbose_name = 'продукт заказа'
        verbose_name_plural = 'продукты заказа'

    def __str__(self):
        return f"{self.product.name} - {self.quantity} шт."
