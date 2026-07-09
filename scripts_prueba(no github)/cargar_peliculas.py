import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

API_KEY = "660e85a76dfda5c0ca1cc05896bb4c4c"
BASE_URL = "https://api.themoviedb.org/3"

def get_popular_movies(pages=1):
    results = []
    for page in range(1, pages + 1):
        response = requests.get(
            f"{BASE_URL}/movie/popular",
            params={"api_key": API_KEY, "language": "es-ES", "page": page}
        )
        response.raise_for_status()
        results.extend(response.json()["results"])
    return results


# 2. TRANSFORM
def transform_movies(raw_movies):
    df = pd.DataFrame(raw_movies)

    columnas = [
        "id", "title", "original_title", "original_language",
        "overview", "popularity", "vote_average", "vote_count",
        "release_date", "adult", "backdrop_path", "poster_path", "genre_ids"
    ]
    df = df[columnas]

    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df = df.drop_duplicates(subset="id")

    return df

def build_movie_genres(df):
    filas = []
    for _, row in df.iterrows():
        for genre_id in row["genre_ids"]:
            filas.append({"movie_id": row["id"], "genre_id": genre_id})
    return pd.DataFrame(filas)

# 3. LOAD
def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="TMDBetl",
        user="postgres",
        password="PBdz0505",
        port=5432
    )

def load_movies(conn, df):
    cur = conn.cursor()
    columnas_bd = [
        "id", "title", "original_title", "original_language",
        "overview", "popularity", "vote_average", "vote_count",
        "release_date", "adult", "backdrop_path", "poster_path"
    ]
    registros = df[columnas_bd].values.tolist()

    execute_values(cur, """
        INSERT INTO movies (
            id, title, original_title, original_language,
            overview, popularity, vote_average, vote_count,
            release_date, adult, backdrop_path, poster_path
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            popularity = EXCLUDED.popularity,
            vote_average = EXCLUDED.vote_average,
            vote_count = EXCLUDED.vote_count
    """, registros)

    conn.commit()
    cur.close()

def load_movie_genres(conn, df):
    cur = conn.cursor()
    registros = df[["movie_id", "genre_id"]].values.tolist()

    execute_values(cur, """
        INSERT INTO movie_genres (movie_id, genre_id)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, registros)

    conn.commit()
    cur.close()

# EJECUCIÓN
movies_raw = get_popular_movies(pages=1)
print(f"Películas recibidas: {len(movies_raw)}")

df_movies = transform_movies(movies_raw)
df_movie_genres = build_movie_genres(df_movies)

print(df_movies.head())
print(f"Relaciones película-género: {len(df_movie_genres)}")

conn = get_connection()
load_movies(conn, df_movies)
load_movie_genres(conn, df_movie_genres)
conn.close()

print("Películas y géneros cargados correctamente")