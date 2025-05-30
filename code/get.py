# from fastapi import FastAPI
# from datetime import datetime

# app = FastAPI()

# @app.get("/timestamp")
# def get_timestamp():
#     # return the current UTC time in ISO format
#     return {"utc": datetime.utcnow().isoformat()}

from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
