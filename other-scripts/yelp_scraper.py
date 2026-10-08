import os
import json
import requests
from dotenv import load_dotenv

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

# filter only with manhattan restaurants, mainly zipcodes starting with 100, 101, and 102
def is_manhattan(business):
    zip_code = business.get("location", {}).get("zip_code", "")

    return zip_code.startswith(
        ("100", "101", "102")
    )


for cuisine in CUISINES:
    print(f"\nFetching {cuisine} restaurants...")

    cuisine_count = 0

    # Yelp exposes up to 240 results for one search query.
    for offset in range(0, 240, 50):
        limit = min(50, 240 - offset)

        params = {
            "term": f"{cuisine} restaurants",
            "location": "Manhattan, New York, NY",
            "limit": limit,
            "offset": offset
        }

        response = requests.get(
            URL,
            headers=HEADERS,
            params=params
        )

        if response.status_code != 200:
            print(
                f"Error for {cuisine}: "
                f"{response.status_code}"
            )
            print(response.text)
            break

        data = response.json()
        businesses = data.get("businesses", [])

        if not businesses:
            break

        for business in businesses:

            # yelp may return nearby restaurants outside manhattan
            if not is_manhattan(business):
                continue

            # avoid duplicates across pages / cuisines
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
                    "Latitude":
                        business["coordinates"]["latitude"],
                    "Longitude":
                        business["coordinates"]["longitude"]
                },
                "NumberOfReviews":
                    business["review_count"],
                "Rating":
                    business["rating"],
                "ZipCode":
                    business["location"]["zip_code"],
                "Cuisine":
                    cuisine
            })

            cuisine_count += 1

        print(
            f"{cuisine}: "
            f"{cuisine_count} unique manhattan restaurants so far"
        )

print("\nDone!!!")
print(
    f"Total unique Manhattan restaurants: "
    f"{len(restaurants)}"
)

with open(
    "other-scripts/restaurants.json",
    "w"
) as f:
    json.dump(
        restaurants,
        f,
        indent=2
    )

print(
    "Saved data to "
    "other-scripts/restaurants.json"
)