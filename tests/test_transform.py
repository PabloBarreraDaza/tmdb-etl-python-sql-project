import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
from transform import (
    transform_movies,
    add_bayesian_score,
    add_movie_category,
    add_quality_flags,
    build_movie_genres,
)

def sample_raw_movies():
    return [
        {
            "id": 1, "title": "Película A", "original_title": "Movie A",
            "original_language": "en", "overview": "Una historia interesante",
            "popularity": 500.0, "vote_average": 8.5, "vote_count": 2000,
            "release_date": "2024-01-15", "adult": False,
            "backdrop_path": "/a.jpg", "poster_path": "/a2.jpg",
            "genre_ids": [28, 12]
        },
        {
            "id": 2, "title": "Película B", "original_title": "Movie B",
            "original_language": "es", "overview": "",
            "popularity": 10.0, "vote_average": 9.0, "vote_count": 3,
            "release_date": "", "adult": False,
            "backdrop_path": None, "poster_path": None,
            "genre_ids": [18]
        },
    ]

def sample_details():
    return [
        {"id": 1, "budget": 100_000_000, "revenue": 500_000_000, "runtime": 120},
        {"id": 2, "budget": 0, "revenue": 0, "runtime": 90},
    ]

def test_transform_movies_selecciona_columnas_correctas():
    df = transform_movies(sample_raw_movies(), sample_details())
    assert "id" in df.columns
    assert "genre_ids" in df.columns
    assert "video" not in df.columns

def test_transform_movies_convierte_fechas():
    df = transform_movies(sample_raw_movies(), sample_details())
    assert pd.api.types.is_datetime64_any_dtype(df["release_date"])

def test_transform_movies_maneja_fecha_vacia():
    df = transform_movies(sample_raw_movies(), sample_details())
    fila_b = df[df["id"] == 2].iloc[0]
    assert pd.isna(fila_b["release_date"])

def test_transform_movies_sin_duplicados():
    raw = sample_raw_movies() + [sample_raw_movies()[0]]  # id=1 repetido
    details = sample_details()
    df = transform_movies(raw, details)
    assert df["id"].is_unique

def test_bayesian_score_favorece_mas_votos():
    df = pd.DataFrame({
        "vote_average": [8.5, 9.0],
        "vote_count": [2000, 3],
    })
    df = add_bayesian_score(df)
    # la película con 3 votos debe acercarse más a la media global que su propia nota
    C = df["vote_average"].mean()
    assert abs(df.loc[1, "bayesian_score"] - C) < abs(df.loc[1, "vote_average"] - C)

def test_movie_category_asigna_blockbuster_y_nicho():
    df = pd.DataFrame({"popularity": [10, 20, 30, 100]})
    df = add_movie_category(df)
    assert set(df["category"].unique()).issubset({"blockbuster", "nicho"})
    assert df.loc[df["popularity"] == 100, "category"].iloc[0] == "blockbuster"

def test_quality_flags_detecta_pocos_votos():
    df = pd.DataFrame({
        "vote_count": [5, 500],
        "budget": [100, 100],
        "revenue": [100, 100],
        "release_date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "overview": ["texto", "texto"],
    })
    df = add_quality_flags(df)
    assert df.loc[0, "flag_low_votes"] == True
    assert df.loc[1, "flag_low_votes"] == False

def test_quality_flags_detecta_overview_vacio():
    df = pd.DataFrame({
        "vote_count": [500, 500],
        "budget": [100, 100],
        "revenue": [100, 100],
        "release_date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
        "overview": ["", "algo"],
    })
    df = add_quality_flags(df)
    assert df.loc[0, "flag_empty_overview"] == True
    assert df.loc[1, "flag_empty_overview"] == False

def test_build_movie_genres_explota_correctamente():
    df = pd.DataFrame({
        "id": [1, 2],
        "genre_ids": [[28, 12], [18]]
    })
    result = build_movie_genres(df)
    assert len(result) == 3  # 2 géneros de la peli 1 + 1 de la peli 2
    assert set(result.columns) == {"movie_id", "genre_id"}