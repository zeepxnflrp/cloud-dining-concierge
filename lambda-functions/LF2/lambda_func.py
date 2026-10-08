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
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")

DYNAMODB_TABLE = "yelp-restaurants"

sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses", region_name="us-east-1")

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


def format_email(body, restaurants):
    lines = [
        "Hi! :)",
        "",
        f"Here are your {body['cuisine'].title()} restaurant suggestions "
        f"for {body['numberOfPeople']} people on "
        f"{body['diningDate']} at {body['diningTime']}:",
        ""
    ]

    for i, restaurant in enumerate(restaurants, start=1):
        lines.extend([
            f"{i}. {restaurant['Name']}",
            f"Address: {restaurant['Address']}",
            f"Rating: {restaurant['Rating']} "
            f"({restaurant['NumberOfReviews']:,} Reviews)",
            ""
        ])

    lines.append("Enjoy your meal! Remember to contact us again for recommendations. :D")

    return "\n".join(lines)


def send_email(recipient, email_body):
    response = ses.send_email(
        Source=SES_SENDER_EMAIL,
        Destination={
            "ToAddresses": [recipient]
        },
        Message={
            "Subject": {
                "Data": "Your Personal Dining Concierge Recommendations <3"
            },
            "Body": {
                "Text": {
                    "Data": email_body
                }
            }
        }
    )

    return response

def delete_sqs_message(receipt_handle):
    sqs.delete_message(
        QueueUrl=SQS_QUEUE_URL,
        ReceiptHandle=receipt_handle
    )


def main():
    message = get_sqs_message()

    if not message:
        return

    body = json.loads(message["Body"])

    print("Received request:")
    print(json.dumps(body, indent=2))

    cuisine = body["cuisine"].lower()

    restaurant_ids = search_opensearch(cuisine)

    if not restaurant_ids:
        print(f"No restaurants found for cuisine: {cuisine}")
        return

    chosen_ids = random.sample(
        restaurant_ids,
        min(3, len(restaurant_ids))
    )

    restaurants = get_restaurant_details(chosen_ids)

    if not restaurants:
        print("No restaurant details found in DynamoDB.")
        return

    print("\nRecommendations:")

    for restaurant in restaurants:
        print(
            f"- {restaurant['Name']} | "
            f"{restaurant['Address']} | "
            f"Rating: {restaurant['Rating']} "
            f"({restaurant['NumberOfReviews']:,} Reviews)"
        )

    email_body = format_email(body, restaurants)

    print("\nEmail preview:\n")
    print(email_body)

    send_email(
        body["email"],
        email_body
    )

    print("\nEmail sent successfully!")

    delete_sqs_message(message["ReceiptHandle"])
    print("SQS message deleted successfully!")


if __name__ == "__main__":
    main()