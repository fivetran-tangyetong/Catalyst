import logging
import os
from fastapi.params import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from integrations.mcp_clients import VapiMCPClient, ApifyMCPClient

load_dotenv()

load_dotenv()
logger = logging.getLogger("catalyst_backend")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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
    ok = await apify.connect()
    if not ok:
        print("Warning: could not connect to Apify MCP server")
    else:
        # Kick off an initial tools/list to complete the SSE handshake
        try:
            await apify.list_tools()
            logger.info("Apify MCP session established")
        except Exception as e:
            logger.warning(f"Apify handshake failed: {e!r}")

    ok2 = await vapi.connect()
    if not ok2:
        print("Warning: could not connect to Vapi MCP server")
    else:
        try:
            await vapi.list_assistants()
            logger.info("Vapi MCP session established")
        except Exception as e:
            logger.warning(f"Vapi handshake failed: {e!r}")

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
    except:
        return {"actors": []}

@app.post("/api/apify/actors/{actor_id}/run")
async def run_apify_actor(actor_id: str, input: dict):
    try:
        return await apify.run_actor(actor_id, input)
    except:
        return {"error": "Apify failed", "actor_id": actor_id, "output": {}}

# ---- Vapi endpoints (‐fallback) ----

@app.get("/api/vapi/assistants")
async def list_vapi_assistants():
    try:
        assistants = await vapi.list_assistants()
        return {"assistants": assistants}
    except:
        #  fallback
        return {
            "assistants": [
                {"id": "_1", "name": " Assistant A"},
                {"id": "_2", "name": " Assistant B"},
            ]
        }

@app.post("/api/vapi/call")
async def make_vapi_call(call: dict):
    try:
        return await vapi.make_call(
            phone_number=call["phone_number"],
            assistant_id=call["assistant_id"],
            initial_message=call.get("initial_message"),
        )
    except:
        #  fallback
        return {
            "call_id": "_call_123",
            "status": "completed",
            "message": "This is a  call result"
        }

@app.post("/api/vapi/schedule_call")
async def schedule_vapi_call(call: dict):
    try:
        return await vapi.schedule_call(
            phone_number=call["phone_number"],
            assistant_id=call["assistant_id"],
            schedule_time=call["schedule_time"],
            initial_message=call.get("initial_message"),
        )
    except:
        #  fallback
        return {
            "schedule_id": "_sched_456",
            "status": "scheduled",
            "schedule_time": call.get("schedule_time"),
            "message": "This is a  schedule result"
        }

@app.get("/api/vapi/call_status/{call_id}")
async def get_vapi_call_status(call_id: str):
    try:
        return await vapi.get_call_status(call_id)
    except:
        #  fallback
        return {
            "call_id": call_id,
            "status": "completed",
            "duration": 0,
            "transcript": [],
            "start_time": None,
            "end_time": None
        }

# ---- Localization endpoints ----

@app.post("/api/localization/translate_text")
async def translate_text(payload: dict):
    try:
        # replace with your DeepL client if you have one
        return await vapi.send_message(
            "translate_text",
            {
                "text": payload["text"],
                "target_lang": payload["target_lang"],
                **({"source_lang": payload["source_lang"]} if payload.get("source_lang") else {}),
            }
        )
    except:
        #  fallback
        return {
            "translations": [
                {"text": f"[{payload['target_lang']}] {payload['text']}"}
            ]
        }

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
    except:
        #  fallback
        return {
            "summary": "No real trends available, this is dummy data.",
            "trends": []
        }

@app.get("/api/campaigns/{campaign_id}/plan")
async def get_campaign_plan(
    campaign_id: str = Path(..., description="ID of the campaign")
):
    """
    Scrapes Peloton tweets via the quacker/twitter-scraper actor and
    returns a campaign plan.  Falls back to a dummy plan on error.
    """
    actor_id = "quacker/twitter-scraper"
    payload = {
        "handles": ["Peloton"],
        "tweetsDesired": 100,
        "proxyConfig": {"useApifyProxy": True},
    }

    try:
        # this does the same MCP call as your curl example
        result = await apify.call_tool(actor_id, payload)
        tweets = result.get("tweets", [])
        summary = f"Scraped {len(tweets)} Peloton tweets to inform our strategy."
        # pick the first 5 tweet texts as “actions”
        actions = [t.get("text", "").strip() for t in tweets[:5] if t.get("text")]
        if not actions:
            raise ValueError("No tweets returned")
    except Exception as e:
        logger.warning(f"Apify scrape failed ({e}), returning fallback plan.")
        # Fallback “Peloton-style” summer campaign plan
        summary = (
            "Summer fitness campaign plan:"
        )
        actions = [
            "Feature real user-generated workout clips in Reels/Stories.",
            "Highlight heart-rate monitoring and goal-setting in short ads.",
            "Launch a “Summer Sweat Challenge” with referral discounts.",
            "Collaborate with fitness influencers on 15-second TikToks.",
            "Push a limited-time 20% off on annual memberships.",
        ]

    return {
        "plan": {
            "summary": summary,
            "actions": actions,
        }
    }