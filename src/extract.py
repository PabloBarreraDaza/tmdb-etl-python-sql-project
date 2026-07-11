import requests
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import TMDB_API_KEY
from logger_config import logger
from schemas import MovieRaw


BASE_URL = "https://api.themoviedb.org/3"

RETRY_CONFIG = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    reraise=True
)

@retry(**RETRY_CONFIG)
def _get(url, params):
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response


def get_popular_movies(pages=1):
    results = []
    for page in range(1, pages + 1):
        response = _get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": TMDB_API_KEY, "language": "es-ES", "page": page}
        )
        raw_results = response.json()["results"]

        validated = []
        for movie in raw_results:
            try:
                MovieRaw(**movie)
                validated.append(movie)
            except Exception as e:
                logger.warning(f"Película inválida descartada (id={movie.get('id')}): {e}")

        results.extend(validated)
    return results

def get_genres():
    response = _get(
        f"{BASE_URL}/genre/movie/list",
        params={"api_key": TMDB_API_KEY, "language": "es-ES"}
    )
    return response.json()["genres"]

def get_movie_details(movie_id):
    response = _get(
        f"{BASE_URL}/movie/{movie_id}",
        params={"api_key": TMDB_API_KEY, "language": "es-ES"}
    )
    return response.json()

def get_movies_details_batch(movie_ids):
    details = []
    for movie_id in movie_ids:
        detail = get_movie_details(movie_id)
        details.append(detail)
        time.sleep(0.05)
    return details