from django.http import JsonResponse
from django.templatetags.static import static


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


def register_order(request):
    # TODO это лишь заглушка
    order_from_front = json.loads(request.body.decode())
    print(order_from_front)
    order, _ =Order.objects.get_or_create(
        first_name=order_from_front['firstname'],
        last_name=order_from_front['lastname'],
        phone_number=order_from_front['phonenumber'],
        address=order_from_front['address']
    )
    print(order)
    for product in order_from_front['products']:
        ordered_product = Product.objects.get(id=product['product'])
        OrderProduct.objects.get_or_create(
            order = order,
            product = ordered_product,
            quantity = product['quantity']
        )
    return JsonResponse({})

