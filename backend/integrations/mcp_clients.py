import asyncio
from enum import Enum
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_clients")

class MCPMessageType(str, Enum):
    """Enumeration of MCP message types"""
    TOOLS_CALL = "tools/call"
    TOOLS_CALL_RESULT = "tools/callResult"
    TOOLS_LIST = "tools/list"
    TOOLS_LIST_RESULT = "tools/listResult"
    TOOLS_LIST_CHANGED_NOTIFICATION = "tools/listChangedNotification"
    RESOURCES_GET = "resources/get"
    RESOURCES_GET_RESULT = "resources/getResult"
    RESOURCES_LIST = "resources/list"
    RESOURCES_LIST_RESULT = "resources/listResult"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_LIST_RESULT = "prompts/listResult"
    PROMPTS_GET = "prompts/get"
    PROMPTS_GET_RESULT = "prompts/getResult"

class MCPClient:
    """Base class for MCP clients"""
    def __init__(self, server_url: str, api_key: str = None, env_vars: Dict[str, str] = None):
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

        # Prepare params
        params = {**self.env_vars}
        if self.api_key:
            params["token"] = self.api_key

        # Keep session open for SSE
        self._session = aiohttp.ClientSession()
        resp = await self._session.get(self.server_url, params=params)
        if resp.status != 200:
            logger.error(f"Failed to connect to MCP server: {resp.status}")
            return False

        async def sse_reader():
            buffer = {"event": None, "data": ""}
            async for raw in resp.content:
                line = raw.decode().rstrip()
                if not line:
                    # Dispatch event
                    yield buffer
                    buffer = {"event": None, "data": ""}
                elif line.startswith("event:"):
                    buffer["event"] = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    buffer["data"] += line.split(":", 1)[1].strip()

        # Start processing SSE in background\ n        self._sse_task = asyncio.create_task(self._process_sse_events(sse_reader()))
        self.connected = True
        logger.info(f"Connected to MCP server: {self.server_url}")
        return True

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
                # initial session handshake
                info = json.loads(data)
                self.session_id = info.get("sessionId", str(uuid.uuid4()))
            elif evt == "message":
                try:
                    message = json.loads(data)
                    msg_id = message.get("id")
                    if msg_id and msg_id in self._response_futures:
                        future = self._response_futures.pop(msg_id)
                        future.set_result(message)
                    else:
                        logger.debug(f"Unmatched message: {message}")
                except Exception as e:
                    logger.error(f"Failed parsing SSE message: {e}")

    async def send_message(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.connected:
            await self.connect()
        if not self.connected or not self.session_id:
            raise ConnectionError("Not connected to MCP server")

        self.message_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        future = asyncio.get_event_loop().create_future()
        self._response_futures[self.message_id] = future

        post_url = self.server_url.replace("/sse", "/message") + f"?session_id={self.session_id}"
        if self.api_key:
            post_url += f"&token={self.api_key}"

        async with self._session.post(post_url, json=payload) as resp:
            if resp.status != 202:
                text = await resp.text()
                logger.error(f"Send failed ({resp.status}): {text}")
                raise ConnectionError(f"Failed to send message: {resp.status}")

        try:
            return await asyncio.wait_for(future, timeout=60)
        except asyncio.TimeoutError:
            self._response_futures.pop(self.message_id, None)
            raise TimeoutError("No response for message")

    async def list_tools(self) -> List[Dict[str, Any]]:
        resp = await self.send_message(MCPMessageType.TOOLS_LIST)
        return resp.get("result", {}).get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.send_message(MCPMessageType.TOOLS_CALL, {"name": name, "arguments": arguments})
        if "result" in resp:
            return resp["result"]
        raise Exception(f"Error in tool call: {resp.get('error')}")


class ApifyMCPClient(MCPClient):
    def __init__(self, api_key: str):
        super().__init__(server_url="https://actors-mcp-server.apify.actor/sse", api_key=api_key)

    async def run_actor(self, actor_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(actor_id, input_data)

    async def search_actors(self, query: str) -> List[Dict[str, Any]]:
        return await self.call_tool("discover-actors", {"query": query})

    async def get_actor_details(self, actor_id: str) -> Dict[str, Any]:
        return await self.call_tool("get-actor-details", {"actorId": actor_id})

    async def add_actor_as_tool(self, actor_id: str) -> bool:
        try:
            await self.call_tool("add-actor-as-tool", {"actorId": actor_id})
            return True
        except:
            return False


class VapiMCPClient(MCPClient):
    def __init__(self, api_key: str):
        super().__init__(server_url="https://mcp.vapi.ai/sse", env_vars={"VAPI_API_KEY": api_key})

    async def make_call(self, phone_number: str, assistant_id: str, initial_message: str = None) -> Dict[str, Any]:
        args = {"phone_number": phone_number, "assistant_id": assistant_id}
        if initial_message:
            args["initial_message"] = initial_message
        return await self.call_tool("make_call", args)

    async def schedule_call(self, phone_number: str, assistant_id: str, schedule_time: str, initial_message: str = None) -> Dict[str, Any]:
        args = {"phone_number": phone_number, "assistant_id": assistant_id, "schedule_time": schedule_time}
        if initial_message:
            args["initial_message"] = initial_message
        return await self.call_tool("schedule_call", args)

    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        return await self.call_tool("get_call_status", {"call_id": call_id})

    async def list_assistants(self) -> List[Dict[str, Any]]:
        return await self.call_tool("list_assistants", {})


class ArcadeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.arcade.dev/v1"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        logger.info("Arcade: direct API, no MCP support.")
        # Add direct Arcade methods here if needed


# Example usage
async def main():
    client = ApifyMCPClient(api_key="YOUR_TOKEN_HERE")
    if not await client.connect():
        print("Connection failed.")
        return

    tools = await client.list_tools()
    print("Tools available:", tools)

    # Example actor run
    # result = await client.run_actor("actorId123", {"input": "data"})
    # print("Actor run result:", result)

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
