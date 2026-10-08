import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("YELP_API_KEY")
URL = "https://api.yelp.com/v3/businesses/search"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

CUISINES = [
    "chinese",
    "italian",
    "japanese",
    "mexican",
    "indian",
    "thai"
]

seen_ids = set()
restaurants = []

for cuisine in CUISINES:
    print(f"\nFetching {cuisine} restaurants...")

    cuisine_count = 0

    for offset in range(0, 200, 50):
        params = {
            "term": f"{cuisine} restaurants",
            "location": "Manhattan, New York, NY",
            "limit": 50,
            "offset": offset
        }

        response = requests.get(URL, headers=HEADERS, params=params)

        if response.status_code != 200:
            print(f"Error for {cuisine}: {response.status_code}")
            print(response.text)
            break

        data = response.json()

        for business in data.get("businesses", []):
            if business["id"] in seen_ids:
                continue

            seen_ids.add(business["id"])

            restaurants.append({
                "BusinessID": business["id"],
                "Name": business["name"],
                "Address": ", ".join(
                    business["location"]["display_address"]
                ),
                "Coordinates": {
                    "Latitude": business["coordinates"]["latitude"],
                    "Longitude": business["coordinates"]["longitude"]
                },
                "NumberOfReviews": business["review_count"],
                "Rating": business["rating"],
                "ZipCode": business["location"]["zip_code"],
                "Cuisine": cuisine
            })

            cuisine_count += 1

        print(f"{cuisine}: {cuisine_count} unique so far")

print("\nDone!")
print(f"Total unique restaurants: {len(restaurants)}")

with open("other-scripts/restaurants.json", "w") as f:
    json.dump(restaurants, f, indent=2)

print("Saved data to other-scripts/restaurants.json")