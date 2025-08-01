from django.http import JsonResponse
from django.template.defaultfilters import first
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from django.db import transaction

from .models import Product, Order, OrderProduct
import json




def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderProductSerializer(many=True, allow_empty=False, write_only=True)
    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    order_from_front = OrderSerializer(data=request.data) # serializer
    order_from_front.is_valid(raise_exception=True)

    order, _ = Order.objects.get_or_create(
            firstname=order_from_front.validated_data['firstname'],
            lastname=order_from_front.validated_data['lastname'],
            phonenumber=order_from_front.validated_data['phonenumber'],
            address=order_from_front.validated_data['address']
        )
    
    products__fields = order_from_front.validated_data['products']
    for product in products__fields:
        ordered_product = Product.objects.get(name=product['product'])
        OrderProduct.objects.get_or_create(
            order = order,
            product = ordered_product,
            quantity = product['quantity'],
            price=ordered_product.price * product['quantity']
            )
        
    serializer = OrderSerializer(order)
    
    if order and ordered_product:
        return  JsonResponse(serializer.data, status=201)

    return Response()

