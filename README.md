# TMDB ETL — Pipeline de datos de películas con arquitectura Bronze/Silver/Gold

Pipeline ETL en Python que extrae datos de la API pública de [TMDB](https://www.themoviedb.org/), los transforma con `pandas` aplicando lógica analítica real, y los carga en PostgreSQL siguiendo una arquitectura de datos por capas (**Bronze → Silver → Gold**).

> **Nota sobre el alcance**: este proyecto está pensado como una demostración cerrada y reproducible, no como un servicio en producción ejecutándose de forma continua. Se puede ejecutar tantas veces como se quiera (es idempotente y acumula histórico), pero no incluye una programación automática (cron/Airflow) corriendo 24/7. Ver la sección [Cómo se llevaría a producción](#cómo-se-llevaría-a-producción) para cómo se automatizaría si hiciera falta.

## Arquitectura

```
API TMDB
   │
   ▼
[Extract]  requests → JSON crudo
   │
   ▼
┌─────────────────────────────────────────┐
│  BRONZE  → JSON crudo tal cual llega     │
│            (histórico, sin transformar)  │
└─────────────────────────────────────────┘
   │
   ▼
[Transform]  pandas → limpieza, tipado, enriquecimiento, analítica
   │
   ▼
┌─────────────────────────────────────────┐
│  SILVER  → datos limpios y enriquecidos  │
│            + métricas calculadas         │
│            + flags de calidad de datos   │
│            + histórico de snapshots      │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│  GOLD    → vistas SQL analíticas         │
│            listas para consumo           │
└─────────────────────────────────────────┘
```

**Por qué esta arquitectura**: separar por capas permite trazabilidad total (Bronze conserva el dato tal cual llegó, por si hace falta reprocesar), mantiene la lógica de negocio fuera del extract/load, y deja la capa analítica (Gold) como pura SQL declarativa, fácil de consultar desde cualquier herramienta de BI sin tocar el pipeline.

## Stack

- **Python 3.11** — `requests`, `pandas`, `psycopg2`, `python-dotenv`, `tenacity`, `pydantic`
- **PostgreSQL 16** — con schemas separados (`bronze`, `silver`, `gold`)
- **Docker / Docker Compose** — para levantar todo el proyecto con un solo comando
- **pytest** — tests unitarios de la capa de transformación
- **API**: [TMDB API v3](https://developer.themoviedb.org/reference/intro/getting-started)

## Estructura del proyecto

```
tmdb-etl/
├── .env                     # credenciales (no versionado)
├── .gitignore
├── docker-compose.yml        # levanta Postgres + ejecuta el pipeline
├── Dockerfile                 # imagen del pipeline Python
├── requirements.txt
├── etl.log                    # log de ejecución (no versionado)
├── sql/
│   ├── bronze/
│   │   └── ddl_bronze.sql     # schema y tabla de la capa bronze
│   ├── silver/
│   │   └── ddl_silver.sql     # schema y tablas de la capa silver
│   └── gold/
│       └── ddl_gold.sql       # schema y vistas de la capa gold
├── src/
│   ├── config.py               # carga de variables de entorno
│   ├── logger_config.py        # configuración de logging
│   ├── schemas.py               # modelos de validación (Pydantic)
│   ├── extract.py               # llamadas a la API TMDB (con reintentos)
│   ├── transform.py             # limpieza + analítica con pandas
│   ├── load.py                  # carga en PostgreSQL
│   └── main.py                  # orquestación del pipeline
└── tests/
    └── test_transform.py        # tests unitarios de la capa transform
```

## Capas en detalle

### Bronze
- `bronze.movies_raw`: JSON completo de cada película tal como lo devuelve la API, en una columna `JSONB`, con timestamp de extracción. Cada ejecución añade filas nuevas (no sobrescribe), funcionando como histórico de extracciones crudas.

### Silver
- `silver.genres`, `silver.movies`, `silver.movie_genres`: modelo relacional limpio y tipado.
- `silver.movies` se enriquece con una segunda llamada a la API (`/movie/{id}`) para obtener `budget`, `revenue` y `runtime`, datos que no vienen en el listado de populares.
- Incluye columnas analíticas calculadas en la transformación:
  - **`bayesian_score`**: nota ponderada por número de votos (misma fórmula que usa IMDB), para evitar que películas con pocos votos pero nota alta distorsionen el análisis.
  - **`category`**: `blockbuster` / `nicho`, según el percentil 75 de popularidad del propio dataset.
  - **Flags de calidad de datos** (`flag_low_votes`, `flag_no_financials`, `flag_future_release`, `flag_empty_overview`): en vez de descartar registros con datos incompletos o sospechosos, se marcan explícitamente — decisión de diseño para no ocultar problemas de calidad de la fuente.
- `silver.movies_history`: tabla de snapshots — cada ejecución del pipeline añade una fila por película con sus métricas del momento (popularidad, votos, nota, bayesian score), sin sobrescribir las anteriores. Permite analizar evolución en el tiempo con múltiples ejecuciones manuales.
- Carga idempotente con `ON CONFLICT ... DO UPDATE` en las tablas de estado actual: el pipeline se puede re-ejecutar sin duplicar datos, actualizando solo las métricas que cambian con el tiempo.

### Gold
Ocho vistas SQL, de complejidad creciente, calculadas directamente sobre `silver` (sin almacenamiento adicional, siempre reflejan el estado actual):

| Vista | Qué mide | Técnica SQL destacada |
|---|---|---|
| `gold.genre_stats` | Estadísticas agregadas por género | `GROUP BY`, `COUNT ... FILTER` |
| `gold.movie_profitability` | ROI por película | Filtro sobre flags + cálculo de ratio |
| `gold.top_movies_per_genre` | Top 5 películas por género según bayesian score | Window function `RANK() OVER (PARTITION BY ...)` |
| `gold.language_market_overview` | Cuota de mercado por idioma original | Window function sobre agregado (`SUM(COUNT(*)) OVER ()`) |
| `gold.genre_financial_performance` | Rentabilidad financiera por género | CTE + `RANK()` sobre datos ya agregados |
| `gold.data_quality_report` | Resumen ejecutivo de calidad del dataset | Agregación condicional múltiple (`FILTER`) |
| `gold.popularity_rating_analysis` | Relación entre popularidad y valoración | CTE + `NTILE()` (cuartiles) + `CORR()` (correlación de Pearson) |
| `gold.movie_popularity_evolution` | Evolución de popularidad entre ejecuciones del pipeline | CTE + `FIRST_VALUE() OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` |

## Calidad y fiabilidad del pipeline

- **Logging estructurado**: cada ejecución registra su progreso y errores tanto en consola como en `etl.log`, con timestamp y nivel (INFO/ERROR).
- **Reintentos con backoff exponencial** (`tenacity`): las llamadas a la API reintentan automáticamente ante fallos de red temporales (hasta 3 intentos, con espera creciente), sin tumbar el pipeline por un fallo puntual.
- **Validación de datos** (`pydantic`): cada película recibida se valida contra un esquema esperado antes de procesarse; los registros inválidos se descartan y se registran como warning, sin detener la ejecución.
- **Tests unitarios** (`pytest`): cubren la lógica de transformación (selección de columnas, deduplicación, cálculo de bayesian score, categorización, flags de calidad, construcción de la tabla puente de géneros) de forma aislada, sin depender de la API ni de la base de datos.
- **Idempotencia**: el pipeline se puede ejecutar repetidas veces sin duplicar datos en las tablas de estado actual, gracias a `ON CONFLICT ... DO UPDATE`.

## Cómo ejecutarlo

### Opción A: con Docker (recomendado)

Requiere [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

1. Clona el repo:
   ```bash
   git clone https://github.com/PabloBarreraDaza/tmdb-etl-python-sql-project.git
   cd tmdb-etl-python-sql-project
   ```

2. Crea un archivo `.env` en la raíz:
   ```
   TMDB_API_KEY=tu_api_key_de_tmdb
   DB_NAME=tmdb_etl
   DB_USER=postgres
   DB_PASSWORD=tu_password
   DB_PORT=5433
   ```
   Puedes obtener una API key gratuita en [themoviedb.org](https://www.themoviedb.org/settings/api).

3. Levanta todo con un solo comando:
   ```bash
   docker compose up --build
   ```
   Esto construye la imagen del pipeline, levanta Postgres, crea automáticamente los schemas y tablas (bronze → silver → gold, en ese orden), y ejecuta el pipeline completo.

4. Para volver a ejecutarlo (por ejemplo, para generar más snapshots de histórico):
   ```bash
   docker compose up etl
   ```

5. Para reiniciar todo desde cero (borra los datos):
   ```bash
   docker compose down -v
   ```

### Opción B: en local, sin Docker

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Configura el `.env` igual que en la Opción A (usando el puerto de tu Postgres local, normalmente `5432`).

3. Ejecuta el contenido de los archivos SQL en tu instancia de PostgreSQL, en este orden:
   ```
   sql/bronze/ddl_bronze.sql
   sql/silver/ddl_silver.sql
   sql/gold/ddl_gold.sql
   ```

4. Ejecuta el pipeline:
   ```bash
   cd src
   python main.py
   ```

### Ejecutar los tests

```bash
pytest tests/ -v
```

## Decisiones de diseño

- **Idempotencia**: el pipeline usa `ON CONFLICT` en las cargas de estado actual, permitiendo re-ejecuciones seguras sin duplicar datos.
- **Separación de responsabilidades**: `extract.py` no sabe nada de pandas ni de Postgres; `transform.py` no sabe nada de la API ni de la base de datos; `load.py` no sabe nada de la API. Cada módulo tiene una única responsabilidad.
- **No ocultar problemas de calidad de datos**: en vez de filtrar o "limpiar" silenciosamente registros con datos incompletos, se marcan con flags explícitos, dejando la decisión de uso a quien consuma los datos.
- **Vistas en vez de tablas para Gold**: al ser cálculos derivados de Silver, las vistas garantizan que Gold siempre esté sincronizado sin pasos de carga adicionales.
- **Histórico sin sobrescritura**: `silver.movies_history` solo hace `INSERT`, nunca `UPDATE`, para preservar cada snapshot tal como se observó en su momento.
- **Sin scheduling activo**: se priorizó dejar el proyecto como una demostración reproducible y cerrada antes que mantener infraestructura corriendo de forma continua (ver sección siguiente).

## Cómo se llevaría a producción

Este proyecto no incluye ejecución programada, pero está diseñado para soportarla sin cambios estructurales:

- **GitHub Actions**: un workflow con un trigger `schedule` (cron syntax) podría ejecutar `python main.py` periódicamente contra una base de datos gestionada (por ejemplo, un Postgres en Supabase o RDS con capa gratuita).
- **Orquestadores como Airflow o Prefect**: adecuados si el pipeline creciera en número de pasos o dependencias entre tareas; para el tamaño actual del proyecto serían sobreingeniería.
- El diseño actual (idempotencia, logging, reintentos, tabla de histórico) ya cumple los requisitos técnicos para poder automatizarse en cualquiera de estas opciones sin rediseñar nada.

## Roadmap

- [x] **Fase 1** — ETL básico funcional (extract → transform → load)
- [x] **Fase 1.5** — Arquitectura Bronze/Silver/Gold, enriquecimiento de datos, transformaciones analíticas, vistas Gold
- [x] **Fase 2** — Logging, reintentos con backoff, validación con Pydantic, tests unitarios con pytest
- [x] **Fase 3** — Dockerización completa (Postgres + pipeline en un solo `docker compose up`)
- [x] **Fase 4** — Histórico de snapshots (`silver.movies_history`) y vista Gold de evolución en el tiempo

## Autor

Pablo Barrera Daza
