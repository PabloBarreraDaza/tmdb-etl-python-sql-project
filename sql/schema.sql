CREATE TABLE IF NOT EXISTS genres (
    id      INT PRIMARY KEY,
    name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS movies (
    id                  INT PRIMARY KEY,
    title               TEXT NOT NULL,
    original_title      TEXT,
    original_language   VARCHAR(5),
    overview            TEXT,
    popularity          NUMERIC,
    vote_average        NUMERIC(4,2),
    vote_count          INT,
    release_date        DATE,
    adult               BOOLEAN,
    backdrop_path       TEXT,
    poster_path         TEXT,
    loaded_at           TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id    INT REFERENCES movies(id),
    genre_id    INT REFERENCES genres(id),
    PRIMARY KEY (movie_id, genre_id)
);