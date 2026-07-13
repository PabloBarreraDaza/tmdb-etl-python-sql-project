
CREATE SCHEMA IF NOT EXISTS gold;

-- vista que muestra estadísticas de películas por género
CREATE VIEW gold.genre_stats AS
SELECT
    g.name AS genre_name,
    COUNT(*) AS num_movies,
    ROUND(AVG(m.popularity), 2) AS avg_popularity,
    ROUND(AVG(m.bayesian_score), 2) AS avg_bayesian_score,
    ROUND(AVG(m.budget), 0) AS avg_budget,
    ROUND(AVG(m.revenue), 0) AS avg_revenue,
    COUNT(*) FILTER (WHERE m.category = 'blockbuster') AS num_blockbusters
FROM silver.movies m
JOIN silver.movie_genres mg ON m.id = mg.movie_id
JOIN silver.genres g ON mg.genre_id = g.id
GROUP BY g.name
ORDER BY num_movies DESC;

-- vista que muestra la rentabilidad de las películas
CREATE VIEW gold.movie_profitability AS
SELECT
    id,
    title,
    budget,
    revenue,
    ROUND(revenue::NUMERIC / NULLIF(budget, 0), 2) AS roi_ratio,
    revenue - budget AS profit
FROM silver.movies
WHERE flag_no_financials = FALSE
ORDER BY roi_ratio DESC;

-- vista que muestra las 5 películas mejor calificadas por género
CREATE VIEW gold.top_movies_per_genre AS
SELECT genre_name, title, bayesian_score, rank_in_genre
FROM (
    SELECT
        g.name AS genre_name,
        m.title,
        m.bayesian_score,
        RANK() OVER (PARTITION BY g.name ORDER BY m.bayesian_score DESC) AS rank_in_genre
    FROM silver.movies m
    JOIN silver.movie_genres mg ON m.id = mg.movie_id
    JOIN silver.genres g ON mg.genre_id = g.id
) ranked
WHERE rank_in_genre <= 5;


-- vista que muestra un resumen del mercado
CREATE VIEW gold.language_market_overview AS
SELECT
    original_language,
    COUNT(*) AS num_movies,
    ROUND(AVG(popularity), 2) AS avg_popularity,
    ROUND(SUM(revenue), 0) AS total_revenue,
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2
    ) AS market_share_pct
FROM silver.movies
GROUP BY original_language
ORDER BY num_movies DESC;

-- vista que muestra el desempeño financiero por género
CREATE VIEW gold.genre_financial_performance AS
WITH genre_financials AS (
    SELECT
        g.name AS genre_name,
        SUM(m.budget) AS total_budget,
        SUM(m.revenue) AS total_revenue,
        COUNT(*) AS num_movies
    FROM silver.movies m
    JOIN silver.movie_genres mg ON m.id = mg.movie_id
    JOIN silver.genres g ON mg.genre_id = g.id
    WHERE m.flag_no_financials = FALSE
    GROUP BY g.name
)
SELECT
    genre_name,
    num_movies,
    total_budget,
    total_revenue,
    ROUND((total_revenue - total_budget)::NUMERIC / NULLIF(total_budget, 0) * 100, 2) AS roi_pct,
    RANK() OVER (ORDER BY (total_revenue - total_budget) DESC) AS profit_rank
FROM genre_financials
ORDER BY profit_rank;

-- vista que muestra un reporte de calidad de datos
CREATE VIEW gold.data_quality_report AS
SELECT
    COUNT(*) AS total_movies,
    COUNT(*) FILTER (WHERE flag_low_votes) AS movies_low_votes,
    ROUND(100.0 * COUNT(*) FILTER (WHERE flag_low_votes) / COUNT(*), 2) AS pct_low_votes,
    COUNT(*) FILTER (WHERE flag_no_financials) AS movies_no_financials,
    ROUND(100.0 * COUNT(*) FILTER (WHERE flag_no_financials) / COUNT(*), 2) AS pct_no_financials,
    COUNT(*) FILTER (WHERE flag_future_release) AS movies_future_release,
    COUNT(*) FILTER (WHERE flag_empty_overview) AS movies_empty_overview
FROM silver.movies;

-- vista que muestra un análisis de la relación entre popularidad y calificación bayesiana
CREATE VIEW gold.popularity_rating_analysis AS
WITH quartiles AS (
    SELECT
        id,
        title,
        popularity,
        bayesian_score,
        NTILE(4) OVER (ORDER BY popularity) AS popularity_quartile
    FROM silver.movies
    WHERE popularity IS NOT NULL AND bayesian_score IS NOT NULL
),
correlation AS (
    SELECT ROUND(CORR(popularity, bayesian_score)::NUMERIC, 4) AS correlation_coefficient
    FROM silver.movies
)
SELECT
    q.popularity_quartile,
    COUNT(*) AS num_movies,
    ROUND(AVG(q.popularity), 2) AS avg_popularity,
    ROUND(AVG(q.bayesian_score), 2) AS avg_bayesian_score,
    c.correlation_coefficient AS global_correlation
FROM quartiles q
CROSS JOIN correlation c
GROUP BY q.popularity_quartile, c.correlation_coefficient
ORDER BY q.popularity_quartile;


-- vista que muestra la evolución de la popularidad de las películas a lo largo del tiempo
CREATE VIEW gold.movie_popularity_evolution AS
WITH snapshots_ordenados AS (
    SELECT
        movie_id,
        popularity,
        vote_count,
        bayesian_score,
        snapshot_at,
        FIRST_VALUE(popularity) OVER (
            PARTITION BY movie_id ORDER BY snapshot_at
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS primera_popularity,
        FIRST_VALUE(popularity) OVER (
            PARTITION BY movie_id ORDER BY snapshot_at DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS ultima_popularity,
        FIRST_VALUE(snapshot_at) OVER (
            PARTITION BY movie_id ORDER BY snapshot_at
        ) AS primer_snapshot,
        FIRST_VALUE(snapshot_at) OVER (
            PARTITION BY movie_id ORDER BY snapshot_at DESC
        ) AS ultimo_snapshot,
        COUNT(*) OVER (PARTITION BY movie_id) AS num_snapshots
    FROM silver.movies_history
)
SELECT DISTINCT
    m.title,
    s.num_snapshots,
    s.primer_snapshot,
    s.ultimo_snapshot,
    s.primera_popularity,
    s.ultima_popularity,
    ROUND(s.ultima_popularity - s.primera_popularity, 2) AS variacion_popularity,
    CASE
        WHEN s.ultima_popularity > s.primera_popularity THEN 'subio'
        WHEN s.ultima_popularity < s.primera_popularity THEN 'bajo'
        ELSE 'igual'
    END AS tendencia
FROM snapshots_ordenados s
JOIN silver.movies m ON m.id = s.movie_id
WHERE s.num_snapshots > 1
ORDER BY variacion_popularity DESC;