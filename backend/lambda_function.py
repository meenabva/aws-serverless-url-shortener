import json
import os
import random
import string
import time
from urllib.parse import urlparse

import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
client_errors = table.meta.client.exceptions
ALPHABET = string.ascii_letters + string.digits


def respond(status, body=None, headers=None):
    h = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
    if headers:
        h.update(headers)
    return {
        "statusCode": status,
        "headers": h,
        "body": json.dumps(body) if body is not None else "",
    }


def is_valid_url(url):
    try:
        parts = urlparse(url)
        return parts.scheme in ("http", "https") and bool(parts.netloc)
    except Exception:
        return False


def shorten(event):
    try:
        data = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return respond(400, {"error": "Body must be valid JSON"})

    url = data.get("url", "")
    if not is_valid_url(url):
        return respond(400, {"error": "Provide a valid http(s) URL"})

    for _ in range(5):  # retry if the random code already exists
        code = "".join(random.choices(ALPHABET, k=7))
        try:
            table.put_item(
                Item={"short_id": code, "url": url, "clicks": 0,
                      "created_at": int(time.time())},
                ConditionExpression="attribute_not_exists(short_id)",
            )
            break
        except client_errors.ConditionalCheckFailedException:
            continue
    else:
        return respond(500, {"error": "Could not generate a unique code"})

    domain = event["requestContext"]["domainName"]
    return respond(201, {"code": code, "short_url": f"https://{domain}/{code}"})


def redirect(code):
    try:
        result = table.update_item(
            Key={"short_id": code},
            UpdateExpression="SET #c = #c + :one",
            ConditionExpression="attribute_exists(short_id)",
            ExpressionAttributeNames={"#c": "clicks"},
            ExpressionAttributeValues={":one": 1},
            ReturnValues="ALL_NEW",
        )
    except client_errors.ConditionalCheckFailedException:
        return respond(404, {"error": "Short link not found"})
    target = result["Attributes"]["url"]
    return {"statusCode": 301, "headers": {"Location": target}, "body": ""}


def stats(code):
    item = table.get_item(Key={"short_id": code}).get("Item")
    if not item:
        return respond(404, {"error": "Short link not found"})
    return respond(200, {
        "code": code,
        "url": item["url"],
        "clicks": int(item["clicks"]),
        "created_at": int(item["created_at"]),
    })


def lambda_handler(event, context):
    route = event.get("routeKey")
    params = event.get("pathParameters") or {}

    if route == "POST /shorten":
        return shorten(event)
    if route == "GET /stats/{code}":
        return stats(params["code"])
    if route == "GET /{code}":
        return redirect(params["code"])
    return respond(404, {"error": "Route not found"})
