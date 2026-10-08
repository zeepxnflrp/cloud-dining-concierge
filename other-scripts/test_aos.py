import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT")
USERNAME = os.getenv("OPENSEARCH_USERNAME")
PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

query = {
    "query": {
        "term": {
            "Cuisine": "japanese"
        }
    }
}

response = requests.get(
    f"{ENDPOINT}/restaurants/_search",
    auth=HTTPBasicAuth(USERNAME, PASSWORD),
    json=query
)

print(response.status_code)

data = response.json()

for hit in data["hits"]["hits"][:5]:
    print(hit["_source"])