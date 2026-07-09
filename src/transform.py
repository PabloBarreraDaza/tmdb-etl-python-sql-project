import pandas as pd

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