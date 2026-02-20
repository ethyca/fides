"""
External webhook server for testing Fides pre-approval webhooks.

Rotates between three outcomes per request:
  - 1st request -> eligible (auto-approved)
  - 2nd request -> not-eligible (flagged for manual review)
  - 3rd request -> deny (denied directly via admin API)
  - 4th request -> eligible
  - ...

Usage:
    python scripts/test_pre_approval_webhook_server.py
"""

import threading
from datetime import datetime, timezone

import httpx
import uvicorn
from fastapi import FastAPI, Request

FIDES_BASE_URL = "http://localhost:8080/api/v1"
PORT = 8090
OAUTH_CLIENT_ID = "fidesadmin"
OAUTH_CLIENT_SECRET = "fidesadminsecret"

app = FastAPI(title="Pre-Approval Webhook Test Server")

request_counter = 0
counter_lock = threading.Lock()
oauth_token: str | None = None


async def get_oauth_token() -> str:
    """Fetch an OAuth access token from Fides using client credentials."""
    global oauth_token
    if oauth_token:
        return oauth_token

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FIDES_BASE_URL}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        oauth_token = response.json()["access_token"]
        return oauth_token


@app.post("/webhook")
async def receive_webhook(request: Request):
    global request_counter

    body = await request.json()
    headers = dict(request.headers)

    privacy_request_id = body.get("privacy_request_id", "unknown")
    policy_action = body.get("policy_action", "unknown")
    identity = body.get("identity", {})

    reply_to_eligible = headers.get("reply-to-eligible")
    reply_to_not_eligible = headers.get("reply-to-not-eligible")
    reply_to_token = headers.get("reply-to-token")

    with counter_lock:
        request_counter += 1
        current_count = request_counter

    outcome = current_count % 3
    if outcome == 1:
        decision = "eligible"
    elif outcome == 2:
        decision = "not-eligible"
    else:
        decision = "deny"

    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"\n{'=' * 70}")
    print(f"[{timestamp}] Webhook #{current_count} received")
    print(f"  Privacy Request ID: {privacy_request_id}")
    print(f"  Policy Action:      {policy_action}")
    print(f"  Identity:           {identity}")
    print(f"  Decision:           {decision}")

    async with httpx.AsyncClient() as client:
        if decision == "eligible":
            callback_url = f"{FIDES_BASE_URL}{reply_to_eligible}"
            print(f"  Callback URL:       {callback_url}")
            response = await client.post(
                callback_url,
                headers={"Authorization": f"Bearer {reply_to_token}"},
                json={},
            )
            print(f"  Callback Response:  {response.status_code}")
            if response.status_code != 200:
                print(f"  Response Body:      {response.text}")

        elif decision == "not-eligible":
            callback_url = f"{FIDES_BASE_URL}{reply_to_not_eligible}"
            print(f"  Callback URL:       {callback_url}")
            response = await client.post(
                callback_url,
                headers={"Authorization": f"Bearer {reply_to_token}"},
                json={},
            )
            print(f"  Callback Response:  {response.status_code}")
            if response.status_code != 200:
                print(f"  Response Body:      {response.text}")

        else:
            token = await get_oauth_token()
            deny_url = f"{FIDES_BASE_URL}/privacy-request/administrate/deny"
            print(f"  Deny URL:           {deny_url}")
            response = await client.patch(
                deny_url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "request_ids": [privacy_request_id],
                    "reason": "Denied by external pre-approval system: data subject does not meet eligibility criteria for automated processing",
                },
            )
            print(f"  Deny Response:      {response.status_code}")
            if response.status_code != 200:
                print(f"  Response Body:      {response.text}")

    print(f"{'=' * 70}")

    return {"status": "ok", "decision": decision, "request_number": current_count}


@app.get("/health")
async def health():
    return {"status": "healthy", "request_count": request_counter}


if __name__ == "__main__":
    print(f"Starting Pre-Approval Webhook Test Server on port {PORT}")
    print(f"Fides callback base URL: {FIDES_BASE_URL}")
    print(f"Pattern: request #1 -> eligible, #2 -> not-eligible, #3 -> deny, repeat")
    print()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
