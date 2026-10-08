import os
import json
import random
import boto3
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT")
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

DYNAMODB_TABLE = "yelp-restaurants"

sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


def get_sqs_message():
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1
    )

    messages = response.get("Messages", [])

    if not messages:
        print("No messages in queue.")
        return None

    return messages[0]


def search_opensearch(cuisine):
    query = {
        "size": 50,
        "query": {
            "term": {
                "Cuisine": cuisine
            }
        }
    }

    response = requests.get(
        f"{OPENSEARCH_ENDPOINT}/restaurants/_search",
        auth=HTTPBasicAuth(
            OPENSEARCH_USERNAME,
            OPENSEARCH_PASSWORD
        ),
        json=query
    )

    response.raise_for_status()

    hits = response.json()["hits"]["hits"]

    restaurant_ids = [
        hit["_source"]["RestaurantID"]
        for hit in hits
    ]

    return restaurant_ids


def get_restaurant_details(restaurant_ids):
    restaurants = []

    for restaurant_id in restaurant_ids:
        response = table.get_item(
            Key={
                "BusinessID": restaurant_id
            }
        )

        item = response.get("Item")

        if item:
            restaurants.append(item)

    return restaurants


def main():
    message = get_sqs_message()

    if not message:
        return

    body = json.loads(message["Body"])

    print("Received request:")
    print(json.dumps(body, indent=2))

    cuisine = body["cuisine"]

    restaurant_ids = search_opensearch(cuisine)

    if not restaurant_ids:
        print(f"No restaurants found for cuisine: {cuisine}")
        return

    chosen_ids = random.sample(
        restaurant_ids,
        min(3, len(restaurant_ids))
    )

    restaurants = get_restaurant_details(chosen_ids)

    print("\nRecommendations:")

    for restaurant in restaurants:
        print(
            f"- {restaurant['Name']} | "
            f"{restaurant['Address']} | "
            f"Rating: {restaurant['Rating']} "
            f"({restaurant['NumberOfReviews']:,} Reviews)"
        )


if __name__ == "__main__":
    main()