from django.http import JsonResponse
from django.template.defaultfilters import first
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


from .models import Product
from .models import Order
from .models import OrderProduct
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


@api_view(['POST'])
def register_order(request):
    order_from_front = request.data

    for product in order_from_front['products']:
        if not Product.objects.filter(id=product['product']).exists():
            return Response({'error':'products: Недопустимый первичный ключ "9999"'})
    if 'products' not in order_from_front :
        return Response({'error': 'products: Обязательное поле.'}, status=status.HTTP_400_BAD_REQUEST)
    elif order_from_front['products'] is None:
        return Response({'error': 'products: Это поле не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(order_from_front['products'], list):
        return Response({'error': 'products: Ожидался list со значениями, но был получен "str".'}, status=status.HTTP_400_BAD_REQUEST)
    elif not order_from_front['products']:
        return Response({'error': 'products: Этот список не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)
    elif order_from_front['phonenumber'] == '':
        return Response({'error': 'phonenumber: Это поле не может быть пустым.'})
    elif ('firstname' not in order_from_front) or ('lastname' not in order_from_front) or ('phonenumber' not in order_from_front) or ('address' not in order_from_front):
        return Response({'error': 'firstname, lastname, phonenumber, address: Обязательное поле.'})
    elif (order_from_front['firstname'] is None) or (order_from_front['lastname'] is None) or (order_from_front['phonenumber'] is None) or (order_from_front['address'] is None):
        return Response({'error': 'firstname, lastname, phonenumber, address: Это поле не может быть пустым.'})
    elif not isinstance(order_from_front['firstname'], str):
        return Response({'error': 'firstname: Not a valid string.'})
    elif 'firstname' not in order_from_front:
        return Response({'error': 'firstname: Это поле не может быть пустым.'})


    else:
        order, _ =Order.objects.get_or_create(
                first_name=order_from_front['firstname'],
                last_name=order_from_front['lastname'],
                phone_number=order_from_front['phonenumber'],
                address=order_from_front['address']
            )
        for product in order_from_front['products']:
            ordered_product = Product.objects.get(id=product['product'])
            OrderProduct.objects.get_or_create(
                order = order,
                product = ordered_product,
                quantity = product['quantity']
                )
    return Response()

