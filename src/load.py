import psycopg2
from psycopg2.extras import execute_values
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def load_genres(conn, genres):
    cur = conn.cursor()
    registros = [(g["id"], g["name"]) for g in genres]

    execute_values(cur, """
        INSERT INTO genres (id, name)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """, registros)

    conn.commit()
    cur.close()

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