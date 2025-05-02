# backend/app.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from integrations.mcp_clients import VapiMCPClient, ApifyMCPClient

load_dotenv()

VAPI_KEY = os.getenv("VAPI_API_KEY")
APIFY_KEY = os.getenv("APIFY_API_KEY")

vapi = VapiMCPClient(api_key=VAPI_KEY)
apify = ApifyMCPClient(api_key=APIFY_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    ok = await vapi.connect()
    if not ok:
        print("Warning: could not connect to Vapi MCP server")
    ok2 = await apify.connect()
    if not ok2:
        print("Warning: could not connect to Apify MCP server")

@app.on_event("shutdown")
async def shutdown_event():
    await vapi.disconnect()
    await apify.disconnect()

# ---- Apify endpoints ----

@app.get("/api/apify/actors")
async def list_apify_actors():
    try:
        tools = await apify.search_actors("")
        return {"actors": tools}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Apify service unavailable")

@app.post("/api/apify/actors/{actor_id}/run")
async def run_apify_actor(actor_id: str, input: dict):
    try:
        result = await apify.run_actor(actor_id, input)
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail="Apify service unavailable")

# ---- Vapi endpoints ----

@app.get("/api/vapi/assistants")
async def list_vapi_assistants():
    try:
        assistants = await vapi.list_assistants()
        return {"assistants": assistants}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Voice service unavailable")

@app.post("/api/vapi/call")
async def make_vapi_call(call: dict):
    try:
        return await vapi.make_call(
            phone_number=call["phone_number"],
            assistant_id=call["assistant_id"],
            initial_message=call.get("initial_message"),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail="Voice service unavailable")

@app.post("/api/vapi/schedule_call")
async def schedule_vapi_call(call: dict):
    try:
        return await vapi.schedule_call(
            phone_number=call["phone_number"],
            assistant_id=call["assistant_id"],
            schedule_time=call["schedule_time"],
            initial_message=call.get("initial_message"),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail="Voice service unavailable")

@app.get("/api/vapi/call_status/{call_id}")
async def get_vapi_call_status(call_id: str):
    try:
        return await vapi.get_call_status(call_id)
    except Exception as e:
        raise HTTPException(status_code=503, detail="Voice service unavailable")

# ---- Localization endpoints ----

@app.post("/api/localization/translate_text")
async def translate_text(payload: dict):
    try:
        return await vapi.send_message(  # or call your DeepL client instead
            "translate_text",
            {
                "text": payload["text"],
                "target_lang": payload["target_lang"],
                **({"source_lang": payload["source_lang"]} if payload.get("source_lang") else {}),
            }
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Localization service unavailable")

# ---- Market research endpoints ----

@app.post("/api/market_research/trends")
async def analyze_trends(payload: dict):
    try:
        return await apify.send_message(
            "analyze_trends",
            {
                "product_category": payload["product_category"],
                "timeframe": payload["timeframe"],
            }
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Market research service unavailable")
