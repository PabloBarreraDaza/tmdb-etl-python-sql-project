from extract import get_popular_movies, get_genres, get_movies_details_batch
from transform import transform_movies, build_movie_genres
from load import get_connection, load_genres, load_movies, load_movie_genres, load_bronze_movies

def run():
    print("Extrayendo géneros...")
    genres = get_genres()

    print("Extrayendo películas populares...")
    movies_raw = get_popular_movies(pages=5)
    print(f"Películas recibidas: {len(movies_raw)}")

    print("Extrayendo detalles (budget, revenue, runtime)...")
    movie_ids = [m["id"] for m in movies_raw]
    details_list = get_movies_details_batch(movie_ids)

    print("Transformando...")
    df_movies = transform_movies(movies_raw, details_list)
    df_movie_genres = build_movie_genres(df_movies)

    print("Cargando en Postgres...")
    conn = get_connection()
    load_bronze_movies(conn, movies_raw)
    load_genres(conn, genres)
    load_movies(conn, df_movies)
    load_movie_genres(conn, df_movie_genres)
    conn.close()

    print(f"Listo: {len(df_movies)} películas y {len(genres)} géneros cargados.")

if __name__ == "__main__":
    run()