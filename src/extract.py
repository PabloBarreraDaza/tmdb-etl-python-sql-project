import requests
from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"

def get_popular_movies(pages=1):
    results = []
    for page in range(1, pages + 1):
        response = requests.get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": TMDB_API_KEY, "language": "es-ES", "page": page}
        )
        response.raise_for_status()
        results.extend(response.json()["results"])
    return results

def get_genres():
    response = requests.get(
        f"{BASE_URL}/genre/movie/list",
        params={"api_key": TMDB_API_KEY, "language": "es-ES"}
    )
    response.raise_for_status()
    return response.json()["genres"]