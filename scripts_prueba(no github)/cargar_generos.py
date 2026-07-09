import requests
import psycopg2

API_KEY = "660e85a76dfda5c0ca1cc05896bb4c4c"

# 1. EXTRACT: traer géneros de la API
url = "https://api.themoviedb.org/3/genre/movie/list"
params = {"api_key": API_KEY, "language": "es-ES"}

response = requests.get(url, params=params)
data = response.json()
genres = data["genres"]

print(f"Géneros recibidos: {len(genres)}")

# 2. LOAD: conectar a Postgres e insertar
try:
    conn = psycopg2.connect(
        host="localhost",
        dbname="TMDBetl",
        user="postgres",
        password="PBdz0505",
        port=5432
    )
    print("Conexión exitosa")
except Exception as e:
    print("ERROR DETALLADO:", str(e))
    print("TIPO:", type(e))
    if hasattr(e, 'pgcode'):
        print("PGCODE:", e.pgcode)
    if hasattr(e, 'pgerror'):
        print("PGERROR:", e.pgerror)

cur = conn.cursor()

for genre in genres:
    cur.execute(
        """
        INSERT INTO genres (id, name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (genre["id"], genre["name"])
    )

conn.commit()
cur.close()
conn.close()

print("Géneros insertados correctamente")