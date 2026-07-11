import requests
import time
from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"

def get_popular_movies(pages=1):
    results = []
    for page in range(1, pages + 1):
        response = requests.get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": TMDB_API_KEY, "language": "es-ES", "page": page},
            timeout=10
        )
        response.raise_for_status()
        results.extend(response.json()["results"])
    return results

def get_genres():
    response = requests.get(
        f"{BASE_URL}/genre/movie/list",
        params={"api_key": TMDB_API_KEY, "language": "es-ES"},
        timeout=10
    )
    response.raise_for_status()
    return response.json()["genres"]

def get_movie_details(movie_id):
    response = requests.get(
        f"{BASE_URL}/movie/{movie_id}",
        params={"api_key": TMDB_API_KEY, "language": "es-ES"},
        timeout=10
    )
    response.raise_for_status()
    return response.json()

def get_movies_details_batch(movie_ids):
    details = []
    for movie_id in movie_ids:
        detail = get_movie_details(movie_id)
        details.append(detail)
        time.sleep(0.05)  # pequeña pausa para no saturar la API
    return details

