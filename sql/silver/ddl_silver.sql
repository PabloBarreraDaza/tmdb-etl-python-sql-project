-- Schemas
CREATE SCHEMA IF NOT EXISTS silver;


-- SILVER: datos limpios, tipados y normalizados
CREATE TABLE IF NOT EXISTS silver.genres (
    id      INT PRIMARY KEY,
    name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS silver.movies (
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

CREATE TABLE IF NOT EXISTS silver.movie_genres (
    movie_id    INT REFERENCES silver.movies(id),
    genre_id    INT REFERENCES silver.genres(id),
    PRIMARY KEY (movie_id, genre_id)
);

-- añadimos las columnas de budget, revenue y runtime a la tabla silver.movies
ALTER TABLE silver.movies ADD COLUMN budget BIGINT;
ALTER TABLE silver.movies ADD COLUMN revenue BIGINT;
ALTER TABLE silver.movies ADD COLUMN runtime INT;

-- añadimos las columnas de bayesian_score, category y flags a la tabla silver.movies
ALTER TABLE silver.movies ADD COLUMN bayesian_score NUMERIC(4,2);
ALTER TABLE silver.movies ADD COLUMN category TEXT;
ALTER TABLE silver.movies ADD COLUMN flag_low_votes BOOLEAN;
ALTER TABLE silver.movies ADD COLUMN flag_no_financials BOOLEAN;
ALTER TABLE silver.movies ADD COLUMN flag_future_release BOOLEAN;
ALTER TABLE silver.movies ADD COLUMN flag_empty_overview BOOLEAN;



