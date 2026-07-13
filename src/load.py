import psycopg2
from psycopg2.extras import execute_values, Json
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def load_bronze_movies(conn, raw_movies):
    cur = conn.cursor()
    registros = [(m["id"], Json(m)) for m in raw_movies]

    execute_values(cur, """
        INSERT INTO bronze.movies_raw (tmdb_id, raw_data)
        VALUES %s
    """, registros)

    conn.commit()
    cur.close()

def load_genres(conn, genres):
    cur = conn.cursor()
    registros = [(g["id"], g["name"]) for g in genres]

    execute_values(cur, """
        INSERT INTO silver.genres (id, name)
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
        "release_date", "adult", "backdrop_path", "poster_path",
        "budget", "revenue", "runtime",
        "bayesian_score", "category",
        "flag_low_votes", "flag_no_financials", "flag_future_release", "flag_empty_overview"
    ]
    registros = df[columnas_bd].values.tolist()

    execute_values(cur, """
        INSERT INTO silver.movies (
            id, title, original_title, original_language,
            overview, popularity, vote_average, vote_count,
            release_date, adult, backdrop_path, poster_path,
            budget, revenue, runtime,
            bayesian_score, category,
            flag_low_votes, flag_no_financials, flag_future_release, flag_empty_overview
        )
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            popularity = EXCLUDED.popularity,
            vote_average = EXCLUDED.vote_average,
            vote_count = EXCLUDED.vote_count,
            budget = EXCLUDED.budget,
            revenue = EXCLUDED.revenue,
            runtime = EXCLUDED.runtime,
            bayesian_score = EXCLUDED.bayesian_score,
            category = EXCLUDED.category,
            flag_low_votes = EXCLUDED.flag_low_votes,
            flag_no_financials = EXCLUDED.flag_no_financials,
            flag_future_release = EXCLUDED.flag_future_release,
            flag_empty_overview = EXCLUDED.flag_empty_overview
    """, registros)

    conn.commit()
    cur.close()

def load_movie_genres(conn, df):
    cur = conn.cursor()
    registros = df[["movie_id", "genre_id"]].values.tolist()

    execute_values(cur, """
        INSERT INTO silver.movie_genres (movie_id, genre_id)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, registros)

    conn.commit()
    cur.close()

def load_movies_history(conn, df):
    cur = conn.cursor()
    columnas = ["id", "popularity", "vote_average", "vote_count", "bayesian_score", "category"]
    registros = df[columnas].values.tolist()

    execute_values(cur, """
        INSERT INTO silver.movies_history (movie_id, popularity, vote_average, vote_count, bayesian_score, category)
        VALUES %s
    """, registros)

    conn.commit()
    cur.close()