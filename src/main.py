from extract import get_popular_movies, get_genres
from transform import transform_movies, build_movie_genres
from load import get_connection, load_genres, load_movies, load_movie_genres

def run():
    print("Extrayendo géneros...")
    genres = get_genres()

    print("Extrayendo películas populares...")
    movies_raw = get_popular_movies(pages=5)
    print(f"Películas recibidas: {len(movies_raw)}")

    print("Transformando...")
    df_movies = transform_movies(movies_raw)
    df_movie_genres = build_movie_genres(df_movies)

    print("Cargando en Postgres...")
    conn = get_connection()
    load_genres(conn, genres)
    load_movies(conn, df_movies)
    load_movie_genres(conn, df_movie_genres)
    conn.close()

    print(f"Listo: {len(df_movies)} películas y {len(genres)} géneros cargados.")

if __name__ == "__main__":
    run()