# from fastapi import FastAPI
# from pydantic import BaseModel
# from datetime import datetime
# from dateutil import parser, tz

# app = FastAPI()

# class ConvertRequest(BaseModel):
#     utc: str

# @app.post("/convert")
# def convert_to_pst(req: ConvertRequest):
#     dt = parser.isoparse(req.utc)
#     pst = dt.astimezone(tz.gettz("America/Los_Angeles"))
#     return {"pst": pst.isoformat()}

import sys, pytz, datetime
utc = sys.argv[1]
dt = datetime.datetime.fromisoformat(utc).replace(tzinfo=pytz.UTC)
pst = dt.astimezone(pytz.timezone("America/Los_Angeles"))
print(pst.isoformat())
