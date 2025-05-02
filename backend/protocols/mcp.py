"""
Model Context Protocol (MCP) for Catalyst Marketing Platform

This module defines the core protocol for agent communication in the Catalyst platform.
It provides base classes, interfaces, and type definitions for standardized agent interactions.
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, Generic, Awaitable
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")

# Type definitions
T = TypeVar('T')
AgentID = str
TaskID = str
MessageID = str

class AgentType(str, Enum):
    """Enumeration of agent types in the system"""
    MARKET_RESEARCH = "market_research"
    ICP_DISCOVERY = "icp_discovery"
    CAMPAIGN_PLANNING = "campaign_planning"
    CONTENT_GENERATION = "content_generation"
    LOCALIZATION = "localization"
    SCHEDULER = "scheduler"
    OUTREACH = "outreach"
    MASTER_CONTROLLER = "master_controller"

class MessageType(str, Enum):
    """Enumeration of message types for agent communication"""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    LOG = "log"
    COMMAND = "command"
    QUERY = "query"
    NOTIFICATION = "notification"

class TaskStatus(str, Enum):
    """Enumeration of task statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class Priority(int, Enum):
    """Task priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class MCPMessage(BaseModel):
    """Base model for all messages exchanged between agents"""
    message_id: MessageID = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    sender: AgentID
    recipients: List[AgentID]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = {}

class TaskRequest(BaseModel):
    """Model for task request payloads"""
    task_id: TaskID = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    priority: Priority = Priority.MEDIUM
    parameters: Dict[str, Any] = {}
    deadline: Optional[datetime] = None
    requires_approval: bool = True
    parent_task_id: Optional[TaskID] = None

class TaskResponse(BaseModel):
    """Model for task response payloads"""
    task_id: TaskID
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completion_time: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    
class StatusUpdate(BaseModel):
    """Model for agent status updates"""
    agent_id: AgentID
    status: str
    current_tasks: List[TaskID] = []
    metrics: Dict[str, Any] = {}
    load: float = 0.0  # 0.0-1.0 indicating agent load

class ErrorMessage(BaseModel):
    """Model for error messages"""
    error_code: str
    error_message: str
    severity: str
    task_id: Optional[TaskID] = None
    stacktrace: Optional[str] = None
    
class LogMessage(BaseModel):
    """Model for log messages"""
    level: str
    message: str
    context: Dict[str, Any] = {}

class CommandMessage(BaseModel):
    """Model for command messages"""
    command: str
    parameters: Dict[str, Any] = {}

class MCPRegistry:
    """Registry for MCP agents and message handlers"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPRegistry, cls).__new__(cls)
            cls._instance.agents = {}
            cls._instance.message_handlers = {}
            cls._instance.task_store = {}
        return cls._instance
    
    def register_agent(self, agent_id: AgentID, agent_type: AgentType, agent_instance: Any) -> None:
        """Register an agent with the MCP registry"""
        self.agents[agent_id] = {
            "type": agent_type,
            "instance": agent_instance,
            "status": "idle",
            "registered_at": datetime.utcnow()
        }
        logger.info(f"Agent registered: {agent_id} ({agent_type})")
    
    def unregister_agent(self, agent_id: AgentID) -> None:
        """Unregister an agent from the MCP registry"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    def get_agent(self, agent_id: AgentID) -> Optional[Any]:
        """Get an agent instance by ID"""
        agent_info = self.agents.get(agent_id)
        return agent_info["instance"] if agent_info else None
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[Any]:
        """Get all agent instances of a specific type"""
        return [
            info["instance"] for info in self.agents.values() 
            if info["type"] == agent_type
        ]
    
    def register_message_handler(
        self, 
        message_type: MessageType, 
        handler: Callable[[MCPMessage], Awaitable[None]]
    ) -> None:
        """Register a handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def store_task(self, task_id: TaskID, task_data: Dict[str, Any]) -> None:
        """Store task data in the registry"""
        self.task_store[task_id] = {
            "data": task_data,
            "history": [{"timestamp": datetime.utcnow(), "status": TaskStatus.PENDING}]
        }
    
    def update_task_status(self, task_id: TaskID, status: TaskStatus, metadata: Dict[str, Any] = None) -> None:
        """Update the status of a task in the registry"""
        if task_id in self.task_store:
            self.task_store[task_id]["history"].append({
                "timestamp": datetime.utcnow(),
                "status": status,
                "metadata": metadata or {}
            })
            logger.info(f"Task {task_id} status updated to {status}")
    
    def get_task(self, task_id: TaskID) -> Optional[Dict[str, Any]]:
        """Get task data from the registry"""
        return self.task_store.get(task_id)

class MCPBus:
    """Message bus for the Model Context Protocol"""
    def __init__(self):
        self.registry = MCPRegistry()
        self.message_queue = asyncio.Queue()
        self.running = False
        self._message_processor_task = None
    
    async def start(self):
        """Start the message bus"""
        if not self.running:
            self.running = True
            self._message_processor_task = asyncio.create_task(self._process_messages())
            logger.info("MCP Bus started")
    
    async def stop(self):
        """Stop the message bus"""
        if self.running:
            self.running = False
            if self._message_processor_task:
                self._message_processor_task.cancel()
                try:
                    await self._message_processor_task
                except asyncio.CancelledError:
                    pass
            logger.info("MCP Bus stopped")
    
    async def publish_message(self, message: MCPMessage) -> None:
        """Publish a message to the bus"""
        await self.message_queue.put(message)
        logger.debug(f"Message published: {message.message_id} ({message.message_type})")
    
    async def _process_messages(self) -> None:
        """Process messages from the queue"""
        while self.running:
            try:
                message = await self.message_queue.get()
                await self._dispatch_message(message)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
    
    async def _dispatch_message(self, message: MCPMessage) -> None:
        """Dispatch a message to its recipients"""
        # Handle global message handlers
        handlers = self.registry.message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
        
        # Dispatch to specific recipients
        for recipient_id in message.recipients:
            recipient = self.registry.get_agent(recipient_id)
            if recipient:
                try:
                    await recipient.handle_message(message)
                except Exception as e:
                    logger.error(f"Error delivering message to {recipient_id}: {str(e)}")
            else:
                logger.warning(f"Recipient not found: {recipient_id}")

class BaseAgent:
    """Base class for all agents in the system"""
    def __init__(self, agent_id: AgentID, agent_type: AgentType, mcp_bus: MCPBus):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.mcp_bus = mcp_bus
        self.registry = MCPRegistry()
        self.registry.register_agent(agent_id, agent_type, self)
        self.task_handlers = {}
        
    async def start(self) -> None:
        """Start the agent"""
        logger.info(f"Agent {self.agent_id} started")
        
    async def stop(self) -> None:
        """Stop the agent"""
        logger.info(f"Agent {self.agent_id} stopped")
        self.registry.unregister_agent(self.agent_id)
        
    def register_task_handler(self, task_type: str, handler: Callable[[TaskRequest], Awaitable[TaskResponse]]) -> None:
        """Register a handler for a specific task type"""
        self.task_handlers[task_type] = handler
        
    async def handle_message(self, message: MCPMessage) -> None:
        """Handle an incoming message"""
        logger.debug(f"Agent {self.agent_id} received message: {message.message_id}")
        
        if message.message_type == MessageType.TASK_REQUEST:
            await self._handle_task_request(message)
        elif message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        # Add other message type handlers as needed
            
    async def _handle_task_request(self, message: MCPMessage) -> None:
        """Handle a task request message"""
        task_request = TaskRequest(**message.payload)
        
        # Store the task in the registry
        self.registry.store_task(task_request.task_id, task_request.dict())
        
        # Update task status to in progress
        self.registry.update_task_status(task_request.task_id, TaskStatus.IN_PROGRESS)
        
        # Find the appropriate handler
        handler = self.task_handlers.get(task_request.task_type)
        if not handler:
            logger.warning(f"No handler for task type: {task_request.task_type}")
            await self._send_task_failure(task_request, message.sender, "No handler for this task type")
            return
            
        try:
            # Execute the task handler
            response = await handler(task_request)
            
            # Update task status based on response
            self.registry.update_task_status(task_request.task_id, response.status)
            
            # Send the response
            await self._send_task_response(response, message.sender, task_request.task_id)
            
        except Exception as e:
            logger.error(f"Error handling task {task_request.task_id}: {str(e)}")
            await self._send_task_failure(task_request, message.sender, str(e))
            
    async def _handle_command(self, message: MCPMessage) -> None:
        """Handle a command message"""
        command = CommandMessage(**message.payload)
        logger.info(f"Agent {self.agent_id} received command: {command.command}")
        # Implement command handling logic
            
    async def _send_task_response(self, response: TaskResponse, recipient: AgentID, task_id: TaskID) -> None:
        """Send a task response message"""
        message = MCPMessage(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            recipients=[recipient],
            payload=response.dict(),
            correlation_id=task_id
        )
        await self.mcp_bus.publish_message(message)
            
    async def _send_task_failure(self, task_request: TaskRequest, recipient: AgentID, error_message: str) -> None:
        """Send a task failure message"""
        response = TaskResponse(
            task_id=task_request.task_id,
            status=TaskStatus.FAILED,
            error_message=error_message
        )
        await self._send_task_response(response, recipient, task_request.task_id)
            
    async def send_task_request(
        self, 
        recipient: AgentID, 
        task_type: str, 
        parameters: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        deadline: Optional[datetime] = None,
        requires_approval: bool = True
    ) -> TaskID:
        """Send a task request to another agent"""
        task_request = TaskRequest(
            task_type=task_type,
            priority=priority,
            parameters=parameters,
            deadline=deadline,
            requires_approval=requires_approval
        )
        
        message = MCPMessage(
            message_type=MessageType.TASK_REQUEST,
            sender=self.agent_id,
            recipients=[recipient],
            payload=task_request.dict()
        )
        
        await self.mcp_bus.publish_message(message)
        return task_request.task_id
            
    async def send_status_update(self, status: str, current_tasks: List[TaskID] = None, metrics: Dict[str, Any] = None) -> None:
        """Send a status update message"""
        status_update = StatusUpdate(
            agent_id=self.agent_id,
            status=status,
            current_tasks=current_tasks or [],
            metrics=metrics or {}
        )
        
        message = MCPMessage(
            message_type=MessageType.STATUS_UPDATE,
            sender=self.agent_id,
            recipients=[AgentType.MASTER_CONTROLLER],  # Status updates typically go to the controller
            payload=status_update.dict()
        )
        
        await self.mcp_bus.publish_message(message)
            
    async def send_log(self, level: str, log_message: str, context: Dict[str, Any] = None) -> None:
        """Send a log message"""
        log = LogMessage(
            level=level,
            message=log_message,
            context=context or {}
        )
        
        message = MCPMessage(
            message_type=MessageType.LOG,
            sender=self.agent_id,
            recipients=[AgentType.MASTER_CONTROLLER],  # Logs typically go to the controller
            payload=log.dict()
        )
        
        await self.mcp_bus.publish_message(message)
