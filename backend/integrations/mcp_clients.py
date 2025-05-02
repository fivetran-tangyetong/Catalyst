import asyncio
import json
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_clients")


class MCPMessageType(str, Enum):
    TOOLS_CALL = "tools/call"
    TOOLS_LIST = "tools/list"


class MCPClient:
    def __init__(
        self,
        sse_url: str,
        message_url: str,
        api_key: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ):
        self.sse_url = sse_url
        self.message_url = message_url
        self.api_key = api_key
        self.env_vars = env_vars or {}
        self.session_id: Optional[str] = None
        self.message_id: int = 0
        self.connected: bool = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._sse_task: Optional[asyncio.Task] = None
        self._response_futures: Dict[int, asyncio.Future] = {}

    async def connect(self) -> bool:
        if self.connected:
            return True

        params = {**self.env_vars}
        if self.api_key:
            params["token"] = self.api_key

        self._session = aiohttp.ClientSession()
        resp = await self._session.get(self.sse_url, params=params)
        if resp.status != 200:
            logger.error(f"Failed to open SSE: {resp.status}")
            await self._session.close()
            return False

        # Read the first endpoint event to grab sessionId
        buf = {"event": None, "data": ""}
        async for raw in resp.content:
            line = raw.decode().rstrip()
            if not line:
                if buf["event"] == "endpoint":
                    # data like "/message?sessionId=xxx"
                    sid = buf["data"].split("sessionId=")[-1]
                    self.session_id = sid.strip()
                    break
                buf = {"event": None, "data": ""}
            elif line.startswith("event:"):
                buf["event"] = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                buf["data"] += line.split(":", 1)[1].strip()

        if not self.session_id:
            logger.error("No sessionId received in handshake")
            await self._session.close()
            return False

        # background reader for messages
        async def sse_reader():
            buf = {"event": None, "data": ""}
            async for raw in resp.content:
                line = raw.decode().rstrip()
                if not line:
                    yield buf
                    buf = {"event": None, "data": ""}
                elif line.startswith("event:"):
                    buf["event"] = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    buf["data"] += line.split(":", 1)[1].strip()

        self._sse_task = asyncio.create_task(self._process_sse_events(sse_reader()))
        self.connected = True
        logger.info(f"✅ Connected SSE (session_id={self.session_id})")
        return True

    async def disconnect(self) -> None:
        if self._sse_task:
            self._sse_task.cancel()
            await self._sse_task
        if self._session:
            await self._session.close()
        self.connected = False
        self.session_id = None

    async def _process_sse_events(self, reader):
        async for event in reader:
            if event["event"] == "message":
                try:
                    msg = json.loads(event["data"])
                    mid = msg.get("id")
                    if mid in self._response_futures:
                        fut = self._response_futures.pop(mid)
                        fut.set_result(msg)
                except Exception:
                    logger.exception("Failed parsing SSE message")

    async def send_message(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not (self.connected or await self.connect()):
            raise ConnectionError("Not connected to MCP server")
        if not self.session_id:
            raise ConnectionError("No session ID")

        self.message_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
            "params": params,
        }
        fut = asyncio.get_event_loop().create_future()
        self._response_futures[self.message_id] = fut

        url = f"{self.message_url}?session_id={self.session_id}"
        if self.api_key:
            url += f"&token={self.api_key}"

        async with self._session.post(url, json=payload) as resp:
            if resp.status != 202:
                text = await resp.text()
                raise ConnectionError(f"Failed to send message: {resp.status} – {text}")

        return await asyncio.wait_for(fut, timeout=60)

    async def list_tools(self) -> List[Dict[str, Any]]:
        resp = await self.send_message(MCPMessageType.TOOLS_LIST, {})
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.send_message(
            MCPMessageType.TOOLS_CALL, {"name": name, "arguments": arguments}
        )
        if "result" in resp:
            return resp["result"]
        raise Exception(f"Tool call error: {resp.get('error')}")


class ApifyMCPClient(MCPClient):
    def __init__(self, api_key: str):
        # SSE only for the Twitter scraper actor
        sse = "https://actors-mcp-server.apify.actor/sse?actors=quacker/twitter-scraper"
        message = "https://actors-mcp-server.apify.actor/message"
        super().__init__(sse_url=sse, message_url=message, api_key=api_key)


class VapiMCPClient(MCPClient):
    def __init__(self, api_key: str):
        sse = "https://mcp.vapi.ai/sse"
        message = "https://mcp.vapi.ai/message"
        # We pass the key as an env var so it's sent in headers, not query
        super().__init__(sse_url=sse, message_url=message, api_key=None, env_vars={"VAPI_API_KEY": api_key})


# Quick smoke-test
if __name__ == "__main__":
    async def main():
        apify = ApifyMCPClient(api_key="YOUR_APIFY_TOKEN")
        if await apify.connect():
            tools = await apify.list_tools()
            print("Apify tools:", tools)
            data = await apify.call_tool("quacker/twitter-scraper", {
                "handles": ["onepeloton"],
                "tweetsDesired": 10,
                "proxyConfig": {"useApifyProxy": True},
            })
            print("Scraped tweets:", data.get("tweets", [])[:2])
            await apify.disconnect()

        vapi = VapiMCPClient(api_key="YOUR_VAPI_TOKEN")
        if await vapi.connect():
            assistants = await vapi.list_tools()  # same JSON-RPC
            print("VAPI tools:", assistants)
            await vapi.disconnect()

    asyncio.run(main())
