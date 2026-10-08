
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

lex = boto3.client("lexv2-runtime")


def lambda_handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

    try:
        body = json.loads(event.get("body") or "{}")
        messages = body.get("messages", [])

        if not messages:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "No messages provided"})
            }

        user_message = messages[0]["unstructured"]["text"]

        # Reuse the same session ID across conversation turns.
        # The frontend should send this header on every request.
        request_headers = event.get("headers") or {}
        session_id = next(
            (
                value for key, value in request_headers.items()
                if key.lower() == "x-session-id"
            ),
            None
        ) or str(uuid.uuid4())

        lex_response = lex.recognize_text(
            botId=os.environ["LEX_BOT_ID"],
            botAliasId=os.environ["LEX_BOT_ALIAS_ID"],
            localeId="en_US",
            sessionId=session_id,
            text=user_message
        )

        response_messages = []

        for index, message in enumerate(
            lex_response.get("messages", [])
        ):
            if message.get("contentType") == "PlainText":
                response_messages.append({
                    "type": "unstructured",
                    "unstructured": {
                        "id": str(index + 1),
                        "text": message["content"],
                        "timestamp": datetime.now(
                            timezone.utc
                        ).isoformat()
                    }
                })

        return {
            "statusCode": 200,
            "headers": {
                **headers,
                "Access-Control-Expose-Headers": "X-Session-Id",
                "X-Session-Id": session_id
            },
            "body": json.dumps({
                "messages": response_messages
            })
        }

    except Exception as error:
        print("LF0 error:", str(error))
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "Unable to process chatbot request"
            })
        }
