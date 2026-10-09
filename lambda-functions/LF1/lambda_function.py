
import json
import os
import boto3

sqs = boto3.client("sqs")

def close(event, message):
    return {
        "sessionState": {
            "sessionAttributes": event.get("sessionState", {}).get(
                "sessionAttributes", {}
            ),
            "intent": {
                "name": event["sessionState"]["intent"]["name"],
                "state": "Fulfilled"
            },
            "dialogAction": {"type": "Close"}
        },
        "messages": [
            {"contentType": "PlainText", "content": message}
        ]
    }


def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]
    intent_name = intent["name"]

    if intent_name == "GreetingIntent":
        return close(event, "Hi there! How can I help you?")

    if intent_name == "ThankYouIntent":
        return close(event, "You're welcome! Have a great day!")

    if intent_name == "DiningSuggestionsIntent":
        slots = intent.get("slots") or {}

        def get_slot(name):
            slot = slots.get(name)
            if not slot:
                return None
            value = slot.get("value") or {}
            return value.get("interpretedValue")

        required = [
            "Location", "Cuisine", "DiningDate",
            "DiningTime", "NumberOfPeople", "Email"
        ]

        missing = next(
            (name for name in required if not get_slot(name)),
            None
        )

        if missing:
            return {
                "sessionState": {
                    "sessionAttributes": event["sessionState"].get(
                        "sessionAttributes", {}
                    ),
                    "intent": intent,
                    "dialogAction": {
                        "type": "ElicitSlot",
                        "slotToElicit": missing
                    }
                }
            }

        request = {
            "location": get_slot("Location"),
            "cuisine": get_slot("Cuisine").lower(),
            "diningDate": get_slot("DiningDate"),
            "diningTime": get_slot("DiningTime"),
            "numberOfPeople": int(get_slot("NumberOfPeople")),
            "email": get_slot("Email"),
            "sessionId": event.get("sessionId")
        }

        try:
            sqs.send_message(
                QueueUrl=os.environ["SQS_QUEUE_URL"],
                MessageBody=json.dumps(request)
            )
        except Exception as error:
            print("SQS error:", str(error))
            return close(
                event,
                "Sorry, I couldn't submit your request. Please try again."
            )

        return close(
            event,
            "Thank you! I have received your dining request. "
            "You will receive restaurant suggestions by email."
        )

    return close(event, "Sorry, I didn't understand that.")
