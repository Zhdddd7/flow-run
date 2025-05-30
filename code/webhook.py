import os, json, base64, asyncio
from fastapi import FastAPI, Request, HTTPException
from prefect.client import OrionClient

app = FastAPI()


PREFECT_API_URL      = os.environ["PREFECT_API_URL"]
BASIC_USER, BASIC_PASS = os.environ["PREFECT_API_AUTH_STRING"].split(":",1)
DEPLOYMENT_ID        = os.environ["DEPLOYMENT_ID"]

@app.post("/")
async def pubsub_handler(request: Request):
    envelope = await request.json()
    msg = envelope.get("message", {})
    image_path = msg.get("attributes", {}).get("objectId")
    # read from data
    if not image_path and msg.get("data"):
        payload = json.loads(base64.b64decode(msg["data"]).decode())
        image_path = payload.get("name")
    if not image_path:
        raise HTTPException(400, "No objectId/name in Pub/Sub message")

    # trigger Prefect flow run asynchronously
    async with OrionClient(api=PREFECT_API_URL, auth=(BASIC_USER, BASIC_PASS)) as client:
        fr = await client.create_flow_run(
            deployment_id=DEPLOYMENT_ID,
            parameters={"image_path": image_path},
        )
    return {"flow_run_id": fr.id}
