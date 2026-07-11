import pandas as pd

def transform_movies(raw_movies, details_list):
    df = pd.DataFrame(raw_movies)

    columnas = [
        "id", "title", "original_title", "original_language",
        "overview", "popularity", "vote_average", "vote_count",
        "release_date", "adult", "backdrop_path", "poster_path", "genre_ids"
    ]
    df = df[columnas]

    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df = df.drop_duplicates(subset="id")

    df_details = pd.DataFrame(details_list)[["id", "budget", "revenue", "runtime"]]
    df = df.merge(df_details, on="id", how="left")

    df = add_bayesian_score(df)
    df = add_movie_category(df)
    df = add_quality_flags(df)

    return df

def add_bayesian_score(df):
    C = df["vote_average"].mean()
    m = df["vote_count"].mean()

    df["bayesian_score"] = (
        (df["vote_count"] / (df["vote_count"] + m)) * df["vote_average"]
        + (m / (df["vote_count"] + m)) * C
    )
    df["bayesian_score"] = df["bayesian_score"].round(2)

    return df

def add_movie_category(df):
    threshold = df["popularity"].quantile(0.75)
    df["category"] = df["popularity"].apply(
        lambda x: "blockbuster" if x >= threshold else "nicho"
    )
    return df

def add_quality_flags(df):
    df["flag_low_votes"] = df["vote_count"] < 10
    df["flag_no_financials"] = (df["budget"] == 0) | (df["revenue"] == 0)
    df["flag_future_release"] = df["release_date"] > pd.Timestamp.now()
    df["flag_empty_overview"] = df["overview"].isna() | (df["overview"].str.strip() == "")

    return df

def build_movie_genres(df):
    filas = []
    for _, row in df.iterrows():
        for genre_id in row["genre_ids"]:
            filas.append({"movie_id": row["id"], "genre_id": genre_id})
    return pd.DataFrame(filas)