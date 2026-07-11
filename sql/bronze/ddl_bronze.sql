
CREATE SCHEMA IF NOT EXISTS bronze;

-- BRONZE: datos crudos, sin procesar
CREATE TABLE IF NOT EXISTS bronze.movies_raw (
    id              SERIAL PRIMARY KEY,
    tmdb_id         INT NOT NULL,
    raw_data        JSONB NOT NULL,
    extracted_at    TIMESTAMP DEFAULT NOW()
);

/*
id SERIAL PRIMARY KEY: un id autoincremental propio de esta tabla, distinto de tmdb_id. ¿Por qué? Porque en Bronze queremos poder guardar la misma película varias veces si la extraemos en días distintos (así ves cómo cambió su popularidad a lo largo del tiempo) — si tmdb_id fuera la clave primaria, no podrías tener dos filas de la misma película.
tmdb_id INT NOT NULL: el id real de TMDB, pero sin ser PRIMARY KEY, por lo que acabo de explicar
raw_data JSONB: aquí va el diccionario completo de la película, sin filtrar ninguna columna — todo lo que venga de la API, incluso lo que hoy decidiste no usar (video, softcore...)
extracted_at: cuándo se guardó esa "foto" de los datos
*/