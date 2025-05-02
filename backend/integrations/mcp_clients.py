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
        server_url: str,
        api_key: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ):
        self.server_url = server_url
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
        try:
            resp = await self._session.get(self.server_url, params=params)
            if resp.status != 200:
                await self._session.close()
                logger.error(f"Failed to connect to MCP server: {resp.status}")
                return False

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
            logger.info(f"Connected to MCP server: {self.server_url}")
            return True

        except Exception as e:
            await self._session.close()
            logger.error(f"Error connecting to MCP server: {e}")
            return False

    async def disconnect(self) -> None:
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()

        self.connected = False
        self.session_id = None
        logger.info(f"Disconnected from MCP server: {self.server_url}")

    async def _process_sse_events(self, reader):
        async for event in reader:
            evt = event.get("event")
            data = event.get("data")
            if evt == "endpoint":
                info = json.loads(data)
                self.session_id = info.get("sessionId", str(uuid.uuid4()))
            elif evt == "message":
                try:
                    msg = json.loads(data)
                    mid = msg.get("id")
                    if mid and mid in self._response_futures:
                        fut = self._response_futures.pop(mid)
                        fut.set_result(msg)
                except Exception as e:
                    logger.error(f"Failed parsing SSE message: {e}")

    async def send_message(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.connected and not await self.connect():
            raise ConnectionError("Not connected to MCP server")
        if not self.session_id:
            raise ConnectionError("No session ID")

        self.message_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
            "params": params or {},
        }
        fut = asyncio.get_event_loop().create_future()
        self._response_futures[self.message_id] = fut

        url = self.server_url.replace("/sse", "/message") + f"?session_id={self.session_id}"
        if self.api_key:
            url += f"&token={self.api_key}"

        async with self._session.post(url, json=payload) as resp:
            if resp.status != 202:
                txt = await resp.text()
                logger.error(f"Failed to send message: {resp.status} – {txt}")
                raise ConnectionError(f"Failed to send message: {resp.status}")

        return await asyncio.wait_for(fut, timeout=60)

    async def list_tools(self) -> List[Dict[str, Any]]:
        resp = await self.send_message(MCPMessageType.TOOLS_LIST)
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.send_message(
            MCPMessageType.TOOLS_CALL, {"name": name, "arguments": arguments}
        )
        if "result" in resp:
            return resp["result"]
        raise Exception(f"Tool call failed: {resp.get('error')}")


class ApifyMCPClient(MCPClient):
    def __init__(self, api_key: str):
        super().__init__(
            server_url="https://actors-mcp-server.apify.actor/sse",
            api_key=api_key,
        )


class VapiMCPClient(MCPClient):
    def __init__(self, api_key: str):
        # pass your VAPI key *only* via env_vars to avoid token= param
        super().__init__(
            server_url="https://mcp.vapi.ai/sse",
            api_key=None,
            env_vars={"VAPI_API_KEY": api_key},
        )


class ArcadeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.arcade.dev/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        logger.info("Arcade: direct API, no MCP support.")

# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        client = ApifyMCPClient(api_key="YOUR_APIFY_KEY")
        if await client.connect():
            tools = await client.list_tools()
            print("Tools:", tools)
            await client.disconnect()

    asyncio.run(main())
