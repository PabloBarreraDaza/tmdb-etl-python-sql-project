import requests
import json

API_KEY = "660e85a76dfda5c0ca1cc05896bb4c4c"
url = "https://api.themoviedb.org/3/movie/popular"
params = {"api_key": API_KEY, "language": "es-ES", "page": 1}

response = requests.get(url, params=params)
data = response.json()

# solo la primera película, bien formateada
print(json.dumps(data["results"][0], indent=2, ensure_ascii=False))