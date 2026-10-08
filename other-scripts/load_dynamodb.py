import json
import boto3
from datetime import datetime, timezone
from decimal import Decimal

TABLE_NAME = "yelp-restaurants"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def convert_floats(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))

    if isinstance(obj, dict):
        return {
            key: convert_floats(value)
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [
            convert_floats(value)
            for value in obj
        ]

    return obj


with open("other-scripts/restaurants.json", "r") as f:
    restaurants = json.load(f)

print(f"Loaded {len(restaurants)} restaurants")

with table.batch_writer() as batch:
    for index, restaurant in enumerate(restaurants, start=1):

        restaurant["insertedAtTimestamp"] = (
            datetime.now(timezone.utc).isoformat()
        )

        restaurant = convert_floats(restaurant)

        batch.put_item(Item=restaurant)

        if index % 100 == 0:
            print(f"Inserted {index} restaurants")

print(f"Done! Inserted {len(restaurants)} restaurants.")