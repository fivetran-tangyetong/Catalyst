"""
Voice Agent for Catalyst Marketing Platform

This agent is responsible for making outbound calls, scheduling calls,
and managing voice interactions using Vapi's MCP server.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import httpx
from pydantic import BaseModel, Field

from backend.protocols.mcp import (
    BaseAgent, 
    AgentType, 
    TaskRequest, 
    TaskResponse, 
    TaskStatus, 
    MCPBus,
    Priority
)

from backend.integrations.mcp_clients import VapiMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_agent")

# Voice Call Models
class VoiceCallRequest(BaseModel):
    """Model for voice call requests"""
    phone_number: str
    assistant_id: str
    initial_message: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ScheduledCallRequest(BaseModel):
    """Model for scheduled call requests"""
    phone_number: str
    assistant_id: str
    schedule_time: datetime
    initial_message: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = {}

class VoiceCall(BaseModel):
    """Model for voice call data"""
    call_id: str
    phone_number: str
    assistant_id: str
    status: str  # initiated, ringing, in-progress, completed, failed, etc.
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds
    transcript: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VoiceAssistant(BaseModel):
    """Model for voice assistant data"""
    assistant_id: str
    name: str
    description: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = {}

class VoiceAgent(BaseAgent):
    """Agent for voice interactions and outbound calling"""
    
    def __init__(self, agent_id: str, mcp_bus: MCPBus, vapi_api_key: str):
        super().__init__(agent_id, AgentType.OUTREACH, mcp_bus)
        self.vapi_client = VapiMCPClient(vapi_api_key)
        
        # Register task handlers
        self.register_task_handler("make_call", self.handle_make_call)
        self.register_task_handler("schedule_call", self.handle_schedule_call)
        self.register_task_handler("get_call_status", self.handle_get_call_status)
        self.register_task_handler("list_assistants", self.handle_list_assistants)
    
    async def start(self) -> None:
        """Start the agent"""
        await super().start()
        logger.info(f"Voice Agent {self.agent_id} started with Vapi MCP integration")
        
        # Connect to Vapi MCP server
        try:
            connected = await self.vapi_client.connect()
            if connected:
                logger.info("Connected to Vapi MCP server")
            else:
                logger.warning("Failed to connect to Vapi MCP server")
        except Exception as e:
            logger.error(f"Error connecting to Vapi MCP server: {str(e)}")
    
    async def stop(self) -> None:
        """Stop the agent"""
        await self.vapi_client.disconnect()
        await super().stop()
        logger.info(f"Voice Agent {self.agent_id} stopped")
    
    async def handle_make_call(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to make an outbound call"""
        try:
            # Extract parameters
            phone_number = task_request.parameters.get("phone_number", "")
            if not phone_number:
                raise ValueError("Phone number is required")
                
            assistant_id = task_request.parameters.get("assistant_id", "")
            if not assistant_id:
                raise ValueError("Assistant ID is required")
                
            initial_message = task_request.parameters.get("initial_message")
            
            logger.info(f"Making outbound call to {phone_number} using assistant {assistant_id}")
            await self.send_log("info", f"Starting outbound call to {phone_number}")
            
            # Make the call using Vapi MCP client
            result = await self.vapi_client.make_call(
                phone_number=phone_number,
                assistant_id=assistant_id,
                initial_message=initial_message
            )
            
            # Create a voice call object
            call = VoiceCall(
                call_id=result.get("call_id", ""),
                phone_number=phone_number,
                assistant_id=assistant_id,
                status=result.get("status", "initiated"),
                metadata={
                    "vapi_response": result,
                    "original_request": task_request.parameters
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "call": call.dict(),
                    "message": f"Call initiated to {phone_number}"
                }
            )
        except Exception as e:
            logger.error(f"Error making outbound call: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to make outbound call: {str(e)}"
            )
    
    async def handle_schedule_call(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to schedule a call for future execution"""
        try:
            # Extract parameters
            phone_number = task_request.parameters.get("phone_number", "")
            if not phone_number:
                raise ValueError("Phone number is required")
                
            assistant_id = task_request.parameters.get("assistant_id", "")
            if not assistant_id:
                raise ValueError("Assistant ID is required")
                
            schedule_time_str = task_request.parameters.get("schedule_time", "")
            if not schedule_time_str:
                raise ValueError("Schedule time is required")
                
            # Parse schedule time
            if isinstance(schedule_time_str, str):
                schedule_time = datetime.fromisoformat(schedule_time_str)
            else:
                schedule_time = schedule_time_str
                
            initial_message = task_request.parameters.get("initial_message")
            
            logger.info(f"Scheduling call to {phone_number} at {schedule_time}")
            await self.send_log("info", f"Scheduling call to {phone_number}")
            
            # Schedule the call using Vapi MCP client
            result = await self.vapi_client.schedule_call(
                phone_number=phone_number,
                assistant_id=assistant_id,
                schedule_time=schedule_time.isoformat(),
                initial_message=initial_message
            )
            
            # Create a scheduled call object
            scheduled_call = ScheduledCallRequest(
                phone_number=phone_number,
                assistant_id=assistant_id,
                schedule_time=schedule_time,
                initial_message=initial_message,
                metadata={
                    "vapi_response": result,
                    "original_request": task_request.parameters
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "scheduled_call": scheduled_call.dict(),
                    "schedule_id": result.get("schedule_id", ""),
                    "message": f"Call scheduled to {phone_number} at {schedule_time.isoformat()}"
                }
            )
        except Exception as e:
            logger.error(f"Error scheduling call: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to schedule call: {str(e)}"
            )
    
    async def handle_get_call_status(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get the status of a call"""
        try:
            # Extract parameters
            call_id = task_request.parameters.get("call_id", "")
            if not call_id:
                raise ValueError("Call ID is required")
            
            logger.info(f"Getting status for call {call_id}")
            
            # Get call status using Vapi MCP client
            result = await self.vapi_client.get_call_status(call_id)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "call_id": call_id,
                    "status": result.get("status", "unknown"),
                    "duration": result.get("duration"),
                    "transcript": result.get("transcript"),
                    "start_time": result.get("start_time"),
                    "end_time": result.get("end_time")
                }
            )
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get call status: {str(e)}"
            )
    
    async def handle_list_assistants(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to list available voice assistants"""
        try:
            logger.info("Listing voice assistants")
            
            # List assistants using Vapi MCP client
            result = await self.vapi_client.list_assistants()
            
            # Format the assistants
            assistants = []
            for assistant_data in result.get("assistants", []):
                assistant = VoiceAssistant(
                    assistant_id=assistant_data.get("id", ""),
                    name=assistant_data.get("name", ""),
                    description=assistant_data.get("description"),
                    voice_id=assistant_data.get("voice_id"),
                    language=assistant_data.get("language"),
                    metadata=assistant_data.get("metadata", {})
                )
                assistants.append(assistant.dict())
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "assistants": assistants,
                    "count": len(assistants)
                }
            )
        except Exception as e:
            logger.error(f"Error listing assistants: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to list assistants: {str(e)}"
            )
    
    # Helper methods
    async def get_assistant_by_name(self, name: str) -> Optional[VoiceAssistant]:
        """Get an assistant by name"""
        try:
            # List all assistants
            result = await self.vapi_client.list_assistants()
            
            # Find the assistant with the matching name
            for assistant_data in result.get("assistants", []):
                if assistant_data.get("name", "").lower() == name.lower():
                    return VoiceAssistant(
                        assistant_id=assistant_data.get("id", ""),
                        name=assistant_data.get("name", ""),
                        description=assistant_data.get("description"),
                        voice_id=assistant_data.get("voice_id"),
                        language=assistant_data.get("language"),
                        metadata=assistant_data.get("metadata", {})
                    )
            
            return None
        except Exception as e:
            logger.error(f"Error getting assistant by name: {str(e)}")
            return None
    
    async def format_phone_number(self, phone_number: str) -> str:
        """Format a phone number to E.164 format"""
        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if missing
        if len(digits) == 10:  # US number without country code
            return f"+1{digits}"
        elif len(digits) > 10 and not digits.startswith('+'):
            return f"+{digits}"
        elif not phone_number.startswith('+'):
            return f"+{digits}"
        
        return phone_number
