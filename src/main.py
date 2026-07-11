from extract import get_popular_movies, get_genres, get_movies_details_batch
from transform import transform_movies, build_movie_genres
from load import get_connection, load_genres, load_movies, load_movie_genres, load_bronze_movies
from logger_config import logger

def run():
    logger.info("Iniciando pipeline ETL de TMDB")

    logger.info("Extrayendo géneros...")
    genres = get_genres()
    logger.info(f"Géneros recibidos: {len(genres)}")

    logger.info("Extrayendo películas populares...")
    movies_raw = get_popular_movies(pages=5)
    logger.info(f"Películas recibidas: {len(movies_raw)}")

    logger.info("Extrayendo detalles (budget, revenue, runtime)...")
    movie_ids = list(dict.fromkeys(m["id"] for m in movies_raw))
    details_list = get_movies_details_batch(movie_ids)

    logger.info("Transformando...")
    df_movies = transform_movies(movies_raw, details_list)
    df_movie_genres = build_movie_genres(df_movies)

    logger.info("Cargando en Postgres...")
    conn = get_connection()
    load_bronze_movies(conn, movies_raw)
    load_genres(conn, genres)
    load_movies(conn, df_movies)
    load_movie_genres(conn, df_movie_genres)
    conn.close()

    logger.info(f"Pipeline completado: {len(df_movies)} películas y {len(genres)} géneros cargados.")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error(f"El pipeline falló: {e}", exc_info=True)
        raise