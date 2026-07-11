# TMDB ETL — Pipeline de datos de películas con arquitectura Bronze/Silver/Gold

Pipeline ETL en Python que extrae datos de la API pública de [TMDB](https://www.themoviedb.org/), los transforma con `pandas` aplicando lógica analítica real, y los carga en PostgreSQL siguiendo una arquitectura de datos por capas (**Bronze → Silver → Gold**), similar a la que se usa en proyectos de ingeniería de datos en producción.

Proyecto creado como ejercicio práctico para consolidar Python + SQL, con foco en hacerlo representativo de un pipeline real, no solo un script de "llamar API y volcar en tabla".

## Arquitectura
API TMDB -> [Extract]  requests → JSON crudo

│  BRONZE  → JSON crudo tal cual llega (histórico, sin transformar)
│
[Transform]  pandas → limpieza, tipado, enriquecimiento, analítica
│
│  SILVER  → datos limpios y enriquecidos + métricas calculadas + flags de calidad de datos 

│  GOLD    → vistas SQL analíticas listas para consumo           


**Por qué esta arquitectura**: separar por capas permite trazabilidad total (Bronze conserva el dato tal cual llegó, por si hace falta reprocesar), mantiene la lógica de negocio fuera del extract/load, y deja la capa analítica (Gold) como pura SQL declarativa, fácil de consultar desde cualquier herramienta de BI sin tocar el pipeline.

## Stack

- **Python 3.11** — `requests`, `pandas`, `psycopg2`, `python-dotenv`
- **PostgreSQL** — con schemas separados (`bronze`, `silver`, `gold`)
- **API**: [TMDB API v3](https://developer.themoviedb.org/reference/intro/getting-started)

## Estructura del proyecto
tmdb-etl/
├── .env                  # credenciales (no versionado)
├── .gitignore
├── requirements.txt
├── sql/
│   └── bronze ── ddl_bronze.sql
    └── silver ── ddl_silver.sql
    └── gold ── ddl_gold.sql
# schemas, tablas y vistas completas
└── src/
├── config.py          # carga de variables de entorno
├── extract.py          # llamadas a la API TMDB
├── transform.py        # limpieza + analítica con pandas
├── load.py             # carga en PostgreSQL
└── main.py             # orquestación del pipeline

## Capas en detalle

### Bronze
- `bronze.movies_raw`: JSON completo de cada película tal como lo devuelve la API, en una columna `JSONB`, con timestamp de extracción. Cada ejecución añade filas nuevas (no sobrescribe), funcionando como histórico de extracciones.

### Silver
- `silver.genres`, `silver.movies`, `silver.movie_genres`: modelo relacional limpio y tipado.
- `silver.movies` se enriquece con una segunda llamada a la API (`/movie/{id}`) para obtener `budget`, `revenue` y `runtime`, datos que no vienen en el listado de populares.
- Incluye columnas analíticas calculadas en la transformación:
  - **`bayesian_score`**: nota ponderada por número de votos (misma fórmula que usa IMDB), para evitar que películas con pocos votos pero nota alta distorsionen el análisis.
  - **`category`**: `blockbuster` / `nicho`, según el percentil 75 de popularidad del propio dataset.
  - **Flags de calidad de datos** (`flag_low_votes`, `flag_no_financials`, `flag_future_release`, `flag_empty_overview`): en vez de descartar registros con datos incompletos o sospechosos, se marcan explícitamente — decisión de diseño para no ocultar problemas de calidad de la fuente.
- Carga idempotente con `ON CONFLICT ... DO UPDATE`: el pipeline se puede re-ejecutar sin duplicar datos, actualizando solo las métricas que cambian con el tiempo (popularidad, votos, etc.).

### Gold
Siete vistas SQL, de complejidad creciente, calculadas directamente sobre `silver` (sin almacenamiento adicional, siempre reflejan el estado actual):

| Vista | Qué mide | Técnica SQL destacada |
|---|---|---|
| `gold.genre_stats` | Estadísticas agregadas por género | `GROUP BY`, `COUNT ... FILTER` |
| `gold.movie_profitability` | ROI por película | Filtro sobre flags + cálculo de ratio |
| `gold.top_movies_per_genre` | Top 5 películas por género según bayesian score | Window function `RANK() OVER (PARTITION BY ...)` |
| `gold.language_market_overview` | Cuota de mercado por idioma original | Window function sobre agregado (`SUM(COUNT(*)) OVER ()`) |
| `gold.genre_financial_performance` | Rentabilidad financiera por género | CTE + `RANK()` sobre datos ya agregados |
| `gold.data_quality_report` | Resumen ejecutivo de calidad del dataset | Agregación condicional múltiple (`FILTER`) |
| `gold.popularity_rating_analysis` | Relación entre popularidad y valoración | CTE + `NTILE()` (cuartiles) + `CORR()` (correlación de Pearson) |

## Cómo ejecutarlo

### 1. Clona el repo e instala dependencias

```bash
git clone https://github.com/PabloBarreraDaza/tmdb-etl-python-sql-project.git
cd tmdb-etl-python-sql-project
pip install -r requirements.txt
```

### 2. Configura las variables de entorno

Crea un archivo `.env` en la raíz con:
TMDB_API_KEY=tu_api_key_de_tmdb
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tmdb_etl
DB_USER=postgres
DB_PASSWORD=tu_password

Puedes obtener una API key gratuita en [themoviedb.org](https://www.themoviedb.org/settings/api).

### 3. Crea el esquema de base de datos

Ejecuta el contenido de los archivos SQL en tu instancia de PostgreSQL (por ejemplo, con pgAdmin o `psql`).

### 4. Ejecuta el pipeline

## Decisiones de diseño

- **Idempotencia**: el pipeline usa `ON CONFLICT` en todas las cargas de Silver, permitiendo re-ejecuciones seguras sin duplicar datos.
- **Separación de responsabilidades**: `extract.py` no sabe nada de pandas ni de Postgres; `transform.py` no sabe nada de la API ni de la base de datos; `load.py` no sabe nada de la API. Cada módulo tiene una única responsabilidad.
- **No ocultar problemas de calidad de datos**: en vez de filtrar o "limpiar" silenciosamente registros con datos incompletos, se marcan con flags explícitos, dejando la decisión de uso a quien consuma los datos.
- **Vistas en vez de tablas para Gold**: al ser cálculos derivados de Silver, las vistas garantizan que Gold siempre esté sincronizado sin pasos de carga adicionales.

## Roadmap

- [x] **Fase 1** — ETL básico funcional (extract → transform → load)
- [x] **Fase 1.5** — Arquitectura Bronze/Silver/Gold, enriquecimiento de datos, transformaciones analíticas, 7 vistas Gold
- [ ] **Fase 2** — Tests con `pytest`, logging estructurado, manejo de errores con reintentos, validación con `pydantic`
- [ ] **Fase 3** — Dockerización completa (Postgres + pipeline en un solo `docker-compose up`)
- [ ] **Fase 4** — Scheduling automático (cron / Airflow) y cargas incrementales con histórico

## Autor

Pablo Barrera Daza
