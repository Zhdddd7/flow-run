import os, json, base64, asyncio
from prefect.client import OrionClient
from google.cloud import functions_v1

PREFECT_API_URL = os.getenv("PREFECT_API_URL")
BASIC_USER, BASIC_PASS = os.getenv("PREFECT_API_AUTH_STRING").split(":",1)
DEPLOYMENT_ID = "b31ded3a-ba73-4029-b2df-c398c56de3f9"

async def _trigger_prefect_run(image_path):
    async with OrionClient(api=PREFECT_API_URL, auth=(BASIC_USER, BASIC_PASS)) as client:
        fr = await client.create_flow_run(
            deployment_id=DEPLOYMENT_ID,
            parameters={"image_path": image_path},
        )
        print("👉 Created flow run", fr.id)

def handle_gcs_event(event: dict, context: functions_v1.Context):
    # read from attributes
    attrs = event.get("attributes", {})
    image_path = attrs.get("objectId")
    # read from data
    if not image_path and event.get("data"):
        payload = json.loads(base64.b64decode(event["data"]).decode())
        image_path = payload.get("name")
    if not image_path:
        raise ValueError("no objectId/name found in the event")
    print("📥 New image upload:", image_path)
    asyncio.run(_trigger_prefect_run(image_path))
