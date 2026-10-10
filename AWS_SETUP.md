# AWS Setup: Dining Concierge

## 1. Architecture

S3 Frontend → API Gateway → LF0 → Amazon Lex V2 → LF1 → SQS → LF2 → DynamoDB/OpenSearch → SES

**Aayushi's components:**
- S3 frontend
- API Gateway
- Lambda LF0
- Amazon Lex V2 chatbot
- Lambda LF1
- Amazon SQS

**Baani's components:**
- Restaurant data collection
- DynamoDB and OpenSearch
- Lambda LF2
- Amazon SES email delivery

## 2. AWS Configuration

| Resource | Value |
|---|---|
| AWS Region | `us-east-1` |
| AWS Account ID | `640292768358` |
| S3 Bucket | `dining-concierge-fall2026` |
| SQS Queue | `DiningRequestsQueue` |
| SQS Queue Type | Standard |
| SQS Encryption | SSE-SQS |

**API Gateway Endpoint:**

`https://7a4cnfrfk3.execute-api.us-east-1.amazonaws.com/prod/chatbot`

**SQS Queue URL:**

`https://sqs.us-east-1.amazonaws.com/640292768358/DiningRequestsQueue`

**SQS Queue ARN:**

`arn:aws:sqs:us-east-1:640292768358:DiningRequestsQueue`

## 3. Lambda Functions

### LF0: Chatbot API Handler

Receives messages from API Gateway, calls Lex V2 using `recognize_text`, and returns the chatbot response to the frontend.

Required environment variables:
- `LEX_BOT_ID`
- `LEX_BOT_ALIAS_ID`

LF0 also uses the `X-Session-Id` request header to maintain conversation state.

### LF1: Lex Fulfillment

Receives completed dining requests from Lex and sends the collected preferences to SQS.

Required environment variable:
- `SQS_QUEUE_URL`

LF1 requires `sqs:SendMessage` permission for the dining requests queue.

## 4. Amazon Lex V2

**Bot:** `DiningConciergeBot`

Configured intents:
- `GreetingIntent`
- `ThankYouIntent`
- `DiningSuggestionsIntent`
- `FallbackIntent`

DiningSuggestionsIntent collects:
- `Location`
- `Cuisine`
- `DiningDate`
- `DiningTime`
- `NumberOfPeople`
- `Email`

**Location Validation:** The chatbot uses a custom `SupportedLocation` slot type that accepts Manhattan and supported New York City aliases. Unsupported cities such as Indore and New Delhi are rejected, and the bot prompts users to enter a supported location.

The Lex V2 export ZIP is included in this repository.

## 5. SQS Message Format

LF1 sends JSON messages in the following format:

```json
{
  "location": "Manhattan",
  "cuisine": "thai",
  "diningDate": "2026-10-15",
  "diningTime": "19:00",
  "numberOfPeople": 2,
  "email": "test@example.com",
  "sessionId": "dining-final-123"
}
```

LF2 should parse these values to search for restaurant recommendations and email the results.

## 6. Cross-Account Integration

Aayushi and Baani are using separate AWS accounts.

The current SQS access policy grants access to Aayushi's AWS account only.

To connect Baani's LF2:

1. Obtain Baani's AWS account ID and LF2 execution role ARN.
2. Update the SQS queue resource policy to allow her specific execution role to consume messages.
3. Grant her LF2 execution role `sqs:ReceiveMessage`, `sqs:DeleteMessage`, and `sqs:GetQueueAttributes` permissions for this queue.
4. Configure the SQS event source mapping for LF2 in Baani's AWS account.
5. Confirm LF2 processes messages and sends results through SES.

Both sides must configure the appropriate IAM permissions. Do not share AWS access keys.

## 7. Testing Completed

- LF0 successfully calls Lex V2.
- Lex collects dining preferences through a multi-turn conversation.
- LF1 successfully sends completed requests to SQS.
- API Gateway successfully invokes LF0.
- S3 frontend successfully communicates with the chatbot.

**Pending:** Full integration with LF2, restaurant search, and SES email delivery.

## 8. Repository Files

- `lambda-functions/LF0/lambda_function.py`
- `lambda-functions/LF1/lambda_function.py`
- `frontend/chat.html`
- `frontend/assets/`
- Lex V2 bot export ZIP

## 9. Final Integration Test

1. Open the hosted S3 chatbot.
2. Request restaurant recommendations.
3. Enter the location, cuisine, date, time, party size, and email.
4. Confirm Lex completes the conversation.
5. Verify the request reaches SQS.
6. Verify LF2 consumes and processes the message.
7. Confirm the recommendation email arrives.
8. Record the final video demonstration.

