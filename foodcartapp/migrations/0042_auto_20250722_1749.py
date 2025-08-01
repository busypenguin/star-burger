# Generated by Django 3.2.15 on 2025-07-22 17:49

from django.db import migrations


def add_price(apps, schema_editor):
    OrderProduct = apps.get_model('foodcartapp', 'OrderProduct')
    order_products_iterator = OrderProduct.objects.all().iterator()
    for order_product in order_products_iterator:
        OrderProduct.objects.filter(id = order_product.id).update(price=order_product.product.price*order_product.quantity)

class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_orderproduct_price'),
    ]

    operations = [
        migrations.RunPython(add_price),
    ]
