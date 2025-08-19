import requests
import logging


logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        }, timeout=10)
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка при запросе к геокодеру: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Ошибка соединения с геокодером: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Таймаут при запросе к геокодеру: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Общая ошибка запроса к геокодеру: {e}")
        return None
