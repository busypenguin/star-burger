from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.conf import settings 
from django.db.models import Count
from django.db import IntegrityError

from foodcartapp.models import Product, Restaurant, Order, OrderProduct, RestaurantMenuItem
from distance.models import Place
import requests
from geopy import distance



yandex_api_key = settings.YANDEX_API_KEY


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    order_items = Order.objects.filter(~Q(status='DONE')).order_cost()
    rests = Restaurant.objects.all()
    
    for rest in rests:
            
        try:
            rest_address_coords = fetch_coordinates(yandex_api_key, rest.address)
            if rest_address_coords is None:
                raise requests.RequestException
            Place.objects.get_or_create(
                    address = rest.address,
                    defaults =  {
                    'longitude' : rest_address_coords[0],
                    'latitude' : rest_address_coords[1]
                    }
                )
        except requests.RequestException:
            rests_and_distance = available_restaurants
        except IntegrityError:
            continue
        
    orders_with_restaurants = []
    for order in order_items:
        
        try:
            available_restaurants = order.get_available_restaurants()
            rests_and_distance = []
            order_address_coords = fetch_coordinates(yandex_api_key, order.address)
            
            if order_address_coords is None:
                raise requests.RequestException
                    
            place, _ = Place.objects.get_or_create(
                address = order.address,
                defaults =  {
                    'longitude' : order_address_coords[0],
                    'latitude' : order_address_coords[1]
                    }
                )
               
            place_coords = (place.longitude, place.latitude)

            for rest in available_restaurants:
                rest_place = Place.objects.get(address=rest.address)
                rest_coords = (rest_place.longitude, rest_place.latitude)
                distance_between_order_and_rest = distance.distance(place_coords, rest_coords).km
                rests_and_distance.append((rest.name, round(distance_between_order_and_rest, 3)))

            sorted(rests_and_distance, key=lambda rest: rest[1])
                
            orders_with_restaurants.append({
                    'order': order,
                    'available_restaurants': rests_and_distance
                })    

        except requests.RequestException:
            rests_and_distance = available_restaurants
        except IntegrityError:
            continue
        
    return render(request, template_name='order_items.html', context={
        'order_items': orders_with_restaurants
    })
