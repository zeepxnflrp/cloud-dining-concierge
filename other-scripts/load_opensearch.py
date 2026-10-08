import os
import json
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT")
USERNAME = os.getenv("OPENSEARCH_USERNAME")
PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

INDEX_NAME = "restaurants"

auth = HTTPBasicAuth(USERNAME, PASSWORD)

# Create the restaurants index
mapping = {
    "mappings": {
        "properties": {
            "RestaurantID": {
                "type": "keyword"
            },
            "Cuisine": {
                "type": "keyword"
            }
        }
    }
}

response = requests.put(
    f"{ENDPOINT}/{INDEX_NAME}",
    auth=auth,
    headers={"Content-Type": "application/json"},
    json=mapping
)

if response.status_code in [200, 201]:
    print("Created restaurants index.")
elif response.status_code == 400 and "resource_already_exists_exception" in response.text:
    print("restaurants index already exists.")
else:
    print("Error creating index:")
    print(response.status_code, response.text)
    raise SystemExit


# Load restaurant data
with open("other-scripts/restaurants.json", "r") as f:
    restaurants = json.load(f)

print(f"Loaded {len(restaurants)} restaurants")


# Build Bulk API request
bulk_lines = []

for restaurant in restaurants:
    restaurant_id = restaurant["BusinessID"]

    bulk_lines.append(
        json.dumps({
            "index": {
                "_index": INDEX_NAME,
                "_id": restaurant_id
            }
        })
    )

    bulk_lines.append(
        json.dumps({
            "RestaurantID": restaurant_id,
            "Cuisine": restaurant["Cuisine"]
        })
    )

bulk_body = "\n".join(bulk_lines) + "\n"

response = requests.post(
    f"{ENDPOINT}/_bulk",
    auth=auth,
    headers={"Content-Type": "application/x-ndjson"},
    data=bulk_body
)

if response.status_code != 200:
    print("Bulk indexing failed:")
    print(response.status_code)
    print(response.text)
    raise SystemExit

result = response.json()

if result.get("errors"):
    print("Some documents failed to index. :C")
else:
    print(f"Successfully indexed {len(restaurants)} restaurants!!")