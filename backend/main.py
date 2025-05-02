"""
Main FastAPI application for Catalyst Marketing Platform

This module initializes the FastAPI application, sets up the MCP bus,
registers all agents, and creates API endpoints for the platform.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Body, Query, Path, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in the root directory
load_dotenv(dotenv_path=Path('.') / '.env')

# Import MCP components
from backend.protocols.mcp import (
    MCPBus, 
    MCPRegistry, 
    AgentType, 
    TaskStatus,
    MessageType,
    TaskRequest,
    TaskResponse
)

# Import agents
from backend.agents.market_research_agent import MarketResearchAgent
from backend.agents.content_generation_agent import ContentGenerationAgent
from backend.agents.localization_agent import LocalizationAgent
from backend.agents.social_media_agent import SocialMediaAgent
from backend.agents.voice_agent import VoiceAgent

# Import MCP clients
from backend.integrations.mcp_clients import ApifyMCPClient, VapiMCPClient

# Import other agents (to be implemented)
# from backend.agents.icp_discovery_agent import ICPDiscoveryAgent
# from backend.agents.campaign_planning_agent import CampaignPlanningAgent
# from backend.agents.scheduler_agent import SchedulerAgent
# from backend.agents.master_controller_agent import MasterControllerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("catalyst_backend")

# Load environment variables
def get_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable or return default value"""
    value = os.environ.get(var_name, default)
    if value is None:
        logger.warning(f"Environment variable {var_name} not set")
    return value

# API keys for external services
APIFY_API_KEY = get_env_var("APIFY_API_KEY", "your_apify_api_key")
DEEPL_API_KEY = get_env_var("DEEPL_API_KEY", "your_deepl_api_key")
VIZCOM_API_KEY = get_env_var("VIZCOM_API_KEY", "your_vizcom_api_key")
VAPI_API_KEY = get_env_var("VAPI_API_KEY", "your_vapi_api_key")

# Social media API keys
TWITTER_API_KEY = get_env_var("TWITTER_API_KEY", "your_twitter_api_key")
TWITTER_API_SECRET = get_env_var("TWITTER_API_SECRET", "your_twitter_api_secret")
TWITTER_ACCESS_TOKEN = get_env_var("TWITTER_ACCESS_TOKEN", "your_twitter_access_token")
TWITTER_ACCESS_TOKEN_SECRET = get_env_var("TWITTER_ACCESS_TOKEN_SECRET", "your_twitter_access_token_secret")

FACEBOOK_ACCESS_TOKEN = get_env_var("FACEBOOK_ACCESS_TOKEN", "your_facebook_access_token")

INSTAGRAM_ACCESS_TOKEN = get_env_var("INSTAGRAM_ACCESS_TOKEN", "your_instagram_access_token")
INSTAGRAM_BUSINESS_ID = get_env_var("INSTAGRAM_BUSINESS_ID", "your_instagram_business_id")

LINKEDIN_CLIENT_ID = get_env_var("LINKEDIN_CLIENT_ID", "your_linkedin_client_id")
LINKEDIN_CLIENT_SECRET = get_env_var("LINKEDIN_CLIENT_SECRET", "your_linkedin_client_secret")
LINKEDIN_ACCESS_TOKEN = get_env_var("LINKEDIN_ACCESS_TOKEN", "your_linkedin_access_token")

# Create FastAPI app
app = FastAPI(
    title="Catalyst Marketing Platform API",
    description="API for the Catalyst Marketing Platform, an AI-powered marketing automation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Global variables
mcp_bus = None
agents = {}
registry = MCPRegistry()

# MCP clients
apify_mcp_client = None
vapi_mcp_client = None

# Pydantic models for API requests and responses
class UserCredentials(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class CampaignCreate(BaseModel):
    name: str
    description: str
    target_audience: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    goals: Optional[List[str]] = None
    product_info: Dict[str, Any] = {}

class ContentRequest(BaseModel):
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    target_languages: Optional[List[str]] = None

class AgentTaskRequest(BaseModel):
    agent_id: str
    task_type: str
    parameters: Dict[str, Any] = {}
    priority: Optional[str] = "medium"

class DashboardMetrics(BaseModel):
    active_campaigns: int
    pending_content_items: int
    completed_content_items: int
    agent_status: Dict[str, str]
    recent_activities: List[Dict[str, Any]]

class VoiceCallRequest(BaseModel):
    phone_number: str
    assistant_id: str
    initial_message: Optional[str] = None

class ScheduledCallRequest(BaseModel):
    phone_number: str
    assistant_id: str
    schedule_time: str
    initial_message: Optional[str] = None

# Authentication functions (simplified for demo)
async def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user (simplified)"""
    # In a real implementation, this would check against a database
    return username == "admin" and password == "password"

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    # In a real implementation, this would validate the token
    # and retrieve the user from a database
    if token != "demo_token":
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": "admin"}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the MCP bus and agents on startup"""
    global mcp_bus, agents, apify_mcp_client, vapi_mcp_client
    
    logger.info("Starting Catalyst Marketing Platform")
    
    # Initialize MCP bus
    mcp_bus = MCPBus()
    await mcp_bus.start()
    
    # Initialize MCP clients
    apify_mcp_client = ApifyMCPClient(APIFY_API_KEY)
    vapi_mcp_client = VapiMCPClient(VAPI_API_KEY)
    
    # Connect MCP clients
    try:
        await apify_mcp_client.connect()
        logger.info("Connected to Apify MCP server")
    except Exception as e:
        logger.error(f"Failed to connect to Apify MCP server: {str(e)}")
    
    try:
        await vapi_mcp_client.connect()
        logger.info("Connected to Vapi MCP server")
    except Exception as e:
        logger.error(f"Failed to connect to Vapi MCP server: {str(e)}")
    
    # Prepare social media API keys dictionary
    social_media_api_keys = {
        "twitter_api_key": TWITTER_API_KEY,
        "twitter_api_secret": TWITTER_API_SECRET,
        "twitter_access_token": TWITTER_ACCESS_TOKEN,
        "twitter_access_token_secret": TWITTER_ACCESS_TOKEN_SECRET,
        "facebook_access_token": FACEBOOK_ACCESS_TOKEN,
        "instagram_access_token": INSTAGRAM_ACCESS_TOKEN,
        "instagram_business_id": INSTAGRAM_BUSINESS_ID,
        "linkedin_client_id": LINKEDIN_CLIENT_ID,
        "linkedin_client_secret": LINKEDIN_CLIENT_SECRET,
        "linkedin_access_token": LINKEDIN_ACCESS_TOKEN
    }
    
    # Initialize agents
    agents = {
        "market_research": MarketResearchAgent("market_research_agent", mcp_bus, APIFY_API_KEY),
        "content_generation": ContentGenerationAgent("content_generation_agent", mcp_bus, VIZCOM_API_KEY),
        "localization": LocalizationAgent("localization_agent", mcp_bus, DEEPL_API_KEY),
        "social_media": SocialMediaAgent("social_media_agent", mcp_bus, social_media_api_keys),
        "voice": VoiceAgent("voice_agent", mcp_bus, VAPI_API_KEY),
        # Add other agents as they are implemented
    }
    
    # Start all agents
    for agent_id, agent in agents.items():
        await agent.start()
        logger.info(f"Agent {agent_id} started")
    
    logger.info("Catalyst Marketing Platform started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the MCP bus and agents on shutdown"""
    global mcp_bus, agents, apify_mcp_client, vapi_mcp_client
    
    logger.info("Shutting down Catalyst Marketing Platform")
    
    # Stop all agents
    for agent_id, agent in agents.items():
        await agent.stop()
        logger.info(f"Agent {agent_id} stopped")
    
    # Disconnect MCP clients
    if apify_mcp_client:
        await apify_mcp_client.disconnect()
    
    if vapi_mcp_client:
        await vapi_mcp_client.disconnect()
    
    # Stop MCP bus
    if mcp_bus:
        await mcp_bus.stop()
    
    logger.info("Catalyst Marketing Platform shut down successfully")

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint for user authentication and token generation"""
    authenticated = await authenticate_user(form_data.username, form_data.password)
    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real implementation, generate a JWT token
    access_token = "demo_token"
    
    return {"access_token": access_token, "token_type": "bearer"}

# Dashboard endpoints
@app.get("/api/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    """Get dashboard metrics and status"""
    # In a real implementation, this would query a database
    # For demo purposes, return mock data
    return {
        "active_campaigns": 3,
        "pending_content_items": 12,
        "completed_content_items": 45,
        "agent_status": {
            "market_research": "active",
            "content_generation": "active",
            "localization": "active",
            "social_media": "active",
            "voice": "active",
            "icp_discovery": "idle",
            "campaign_planning": "idle",
            "scheduler": "idle",
            "master_controller": "active"
        },
        "recent_activities": [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "content_generation",
                "action": "Generated social media post",
                "status": "completed"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "localization",
                "action": "Translated content to Spanish",
                "status": "completed"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "market_research",
                "action": "Analyzed market trends for fitness trackers",
                "status": "completed"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "social_media",
                "action": "Posted content to Facebook and Twitter",
                "status": "completed"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "agent": "voice",
                "action": "Made outbound call to customer",
                "status": "completed"
            }
        ]
    }

# Campaign endpoints
@app.post("/api/campaigns")
async def create_campaign(
    background_tasks: BackgroundTasks,
    campaign: CampaignCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new marketing campaign"""
    # Generate a campaign ID
    campaign_id = f"campaign_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # In a real implementation, this would store the campaign in a database
    # and trigger the campaign planning agent
    
    # For demo purposes, log the campaign creation
    logger.info(f"Campaign created: {campaign.name} (ID: {campaign_id})")
    
    # Schedule background task to start campaign planning
    background_tasks.add_task(
        schedule_campaign_planning,
        campaign_id,
        campaign.dict()
    )
    
    return {
        "campaign_id": campaign_id,
        "name": campaign.name,
        "status": "created",
        "message": "Campaign created successfully and planning initiated"
    }

@app.get("/api/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List marketing campaigns"""
    # In a real implementation, this would query a database
    # For demo purposes, return mock data
    campaigns = [
        {
            "campaign_id": "campaign_20230601120000",
            "name": "Summer Fitness Challenge",
            "status": "active",
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "content_items": 12
        },
        {
            "campaign_id": "campaign_20230501120000",
            "name": "Spring Product Launch",
            "status": "completed",
            "start_date": "2023-05-01",
            "end_date": "2023-05-31",
            "content_items": 25
        },
        {
            "campaign_id": "campaign_20230701120000",
            "name": "Back to School Promotion",
            "status": "planned",
            "start_date": "2023-07-15",
            "end_date": "2023-09-15",
            "content_items": 5
        }
    ]
    
    # Filter by status if provided
    if status:
        campaigns = [c for c in campaigns if c["status"] == status]
    
    # Apply pagination
    paginated_campaigns = campaigns[offset:offset+limit]
    
    return {
        "campaigns": paginated_campaigns,
        "total": len(campaigns),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific campaign"""
    # In a real implementation, this would query a database
    # For demo purposes, return mock data
    if campaign_id == "campaign_20230601120000":
        return {
            "campaign_id": campaign_id,
            "name": "Summer Fitness Challenge",
            "description": "Promote fitness trackers for summer activities",
            "status": "active",
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "budget": 5000.00,
            "goals": ["Increase sales by 20%", "Generate 500 leads"],
            "target_audience": "Fitness enthusiasts aged 25-45",
            "content_items": [
                {
                    "content_id": "content_20230602120000",
                    "content_type": "social_post",
                    "status": "published",
                    "platform": "instagram"
                },
                {
                    "content_id": "content_20230605120000",
                    "content_type": "email",
                    "status": "scheduled",
                    "platform": "email"
                }
            ],
            "metrics": {
                "impressions": 12500,
                "clicks": 850,
                "conversions": 120
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Campaign not found")

# Content endpoints
@app.post("/api/content")
async def create_content(
    background_tasks: BackgroundTasks,
    content_request: ContentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new content using the content generation agent"""
    # Generate a content ID
    content_id = f"content_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Check if the content generation agent is available
    if "content_generation" not in agents:
        raise HTTPException(status_code=503, detail="Content generation agent not available")
    
    # Prepare task parameters
    task_params = {
        **content_request.parameters,
        "content_type": content_request.content_type,
        "title": content_request.title,
        "description": content_request.description
    }
    
    # Determine task type based on content type
    task_type = "generate_text_content"
    if content_request.content_type in ["banner", "social_image", "ad_image", "product_image"]:
        task_type = "generate_visual_content"
    elif content_request.content_type in ["social_post", "ad", "email"]:
        task_type = "generate_combined_content"
    
    # Schedule background task to generate content
    background_tasks.add_task(
        generate_content,
        content_id,
        task_type,
        task_params,
        content_request.target_languages
    )
    
    return {
        "content_id": content_id,
        "status": "processing",
        "message": "Content generation initiated",
        "estimated_completion_time": "30 seconds"
    }

@app.get("/api/content/{content_id}")
async def get_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details of specific content"""
    # In a real implementation, this would query a database
    # For demo purposes, return mock data
    if content_id.startswith("content_"):
        return {
            "content_id": content_id,
            "content_type": "social_post",
            "status": "completed",
            "title": "Summer Fitness Challenge",
            "text_content": {
                "body": "Get ready for summer with our new fitness tracker! Track your workouts, monitor your heart rate, and achieve your fitness goals. Limited time offer: 20% off!",
                "cta": "Shop Now"
            },
            "visual_content": {
                "image_url": "https://example.com/images/fitness-tracker.jpg",
                "alt_text": "Person wearing fitness tracker while jogging"
            },
            "metadata": {
                "created_at": "2023-06-02T12:00:00Z",
                "created_by": "content_generation_agent",
                "platform": "instagram"
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Content not found")

# Social Media endpoints
@app.post("/api/social-media/post")
async def post_to_social_media(
    background_tasks: BackgroundTasks,
    post_request: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Post content to social media platforms"""
    # Check if the social media agent is available
    if "social_media" not in agents:
        raise HTTPException(status_code=503, detail="Social media agent not available")
    
    # Extract parameters
    content_id = post_request.get("content_id")
    platforms = post_request.get("platforms", [])
    content = post_request.get("content", {})
    
    if not content_id or not platforms or not content:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # Schedule background task to post content
    post_ids = []
    for platform in platforms:
        post_id = f"post_{platform}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        post_ids.append(post_id)
        
        background_tasks.add_task(
            post_content_to_platform,
            content_id,
            platform,
            content,
            post_id
        )
    
    return {
        "content_id": content_id,
        "post_ids": post_ids,
        "platforms": platforms,
        "status": "processing",
        "message": f"Content posting initiated to {len(platforms)} platforms"
    }

@app.post("/api/social-media/schedule")
async def schedule_social_media_post(
    background_tasks: BackgroundTasks,
    schedule_request: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Schedule content for posting to social media platforms"""
    # Check if the social media agent is available
    if "social_media" not in agents:
        raise HTTPException(status_code=503, detail="Social media agent not available")
    
    # Extract parameters
    content_id = schedule_request.get("content_id")
    platforms = schedule_request.get("platforms", [])
    content = schedule_request.get("content", {})
    schedule_time = schedule_request.get("schedule_time")
    
    if not content_id or not platforms or not content or not schedule_time:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    # Schedule background task to schedule content
    schedule_ids = []
    for platform in platforms:
        schedule_id = f"schedule_{platform}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        schedule_ids.append(schedule_id)
        
        background_tasks.add_task(
            schedule_content_for_platform,
            content_id,
            platform,
            content,
            schedule_time,
            schedule_id
        )
    
    return {
        "content_id": content_id,
        "schedule_ids": schedule_ids,
        "platforms": platforms,
        "schedule_time": schedule_time,
        "status": "scheduled",
        "message": f"Content scheduled for {len(platforms)} platforms"
    }

@app.get("/api/social-media/optimal-times/{platform}")
async def get_optimal_posting_times(
    platform: str,
    current_user: dict = Depends(get_current_user)
):
    """Get optimal posting times for a platform"""
    # Check if the social media agent is available
    if "social_media" not in agents:
        raise HTTPException(status_code=503, detail="Social media agent not available")
    
    # Create task request
    task_request = TaskRequest(
        task_type="get_optimal_times",
        parameters={"platform": platform}
    )
    
    # Execute the task
    response = await agents["social_media"].handle_message({
        "message_type": MessageType.TASK_REQUEST,
        "sender": "api",
        "recipients": ["social_media_agent"],
        "payload": task_request.dict()
    })
    
    if not hasattr(response, 'status') or response.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=500, detail="Failed to get optimal posting times")
    
    return response.result

# Voice Agent endpoints
@app.post("/api/voice/call")
async def make_voice_call(
    call_request: VoiceCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """Make an outbound voice call"""
    # Check if the voice agent is available
    if "voice" not in agents:
        raise HTTPException(status_code=503, detail="Voice agent not available")
    
    # Create task request
    task_request = TaskRequest(
        task_type="make_call",
        parameters={
            "phone_number": call_request.phone_number,
            "assistant_id": call_request.assistant_id,
            "initial_message": call_request.initial_message
        }
    )
    
    # Execute the task
    response = await agents["voice"].handle_message({
        "message_type": MessageType.TASK_REQUEST,
        "sender": "api",
        "recipients": ["voice_agent"],
        "payload": task_request.dict()
    })
    
    if not hasattr(response, 'status') or response.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=500, 
            detail=getattr(response, 'error_message', "Failed to make voice call")
        )
    
    return response.result

@app.post("/api/voice/schedule")
async def schedule_voice_call(
    schedule_request: ScheduledCallRequest,
    current_user: dict = Depends(get_current_user)
):
    """Schedule an outbound voice call"""
    # Check if the voice agent is available
    if "voice" not in agents:
        raise HTTPException(status_code=503, detail="Voice agent not available")
    
    # Create task request
    task_request = TaskRequest(
        task_type="schedule_call",
        parameters={
            "phone_number": schedule_request.phone_number,
            "assistant_id": schedule_request.assistant_id,
            "schedule_time": schedule_request.schedule_time,
            "initial_message": schedule_request.initial_message
        }
    )
    
    # Execute the task
    response = await agents["voice"].handle_message({
        "message_type": MessageType.TASK_REQUEST,
        "sender": "api",
        "recipients": ["voice_agent"],
        "payload": task_request.dict()
    })
    
    if not hasattr(response, 'status') or response.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=500, 
            detail=getattr(response, 'error_message', "Failed to schedule voice call")
        )
    
    return response.result

@app.get("/api/voice/call/{call_id}")
async def get_call_status(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a voice call"""
    # Check if the voice agent is available
    if "voice" not in agents:
        raise HTTPException(status_code=503, detail="Voice agent not available")
    
    # Create task request
    task_request = TaskRequest(
        task_type="get_call_status",
        parameters={"call_id": call_id}
    )
    
    # Execute the task
    response = await agents["voice"].handle_message({
        "message_type": MessageType.TASK_REQUEST,
        "sender": "api",
        "recipients": ["voice_agent"],
        "payload": task_request.dict()
    })
    
    if not hasattr(response, 'status') or response.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=500, 
            detail=getattr(response, 'error_message', "Failed to get call status")
        )
    
    return response.result

@app.get("/api/voice/assistants")
async def list_voice_assistants(
    current_user: dict = Depends(get_current_user)
):
    """List available voice assistants"""
    # Check if the voice agent is available
    if "voice" not in agents:
        raise HTTPException(status_code=503, detail="Voice agent not available")
    
    # Create task request
    task_request = TaskRequest(
        task_type="list_assistants",
        parameters={}
    )
    
    # Execute the task
    response = await agents["voice"].handle_message({
        "message_type": MessageType.TASK_REQUEST,
        "sender": "api",
        "recipients": ["voice_agent"],
        "payload": task_request.dict()
    })
    
    if not hasattr(response, 'status') or response.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=500, 
            detail=getattr(response, 'error_message', "Failed to list voice assistants")
        )
    
    return response.result

# Agent endpoints
@app.post("/api/agents/tasks")
async def submit_agent_task(
    background_tasks: BackgroundTasks,
    task_request: AgentTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a task to a specific agent"""
    # Check if the agent exists
    agent_id = task_request.agent_id
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Generate a task ID
    task_id = f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Schedule background task to execute the agent task
    background_tasks.add_task(
        execute_agent_task,
        agent_id,
        task_id,
        task_request.task_type,
        task_request.parameters
    )
    
    return {
        "task_id": task_id,
        "agent_id": agent_id,
        "status": "submitted",
        "message": f"Task submitted to {agent_id} agent"
    }

@app.get("/api/agents/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a specific task"""
    # In a real implementation, this would query the task store in the registry
    # For demo purposes, return mock data
    task = registry.get_task(task_id)
    
    if task:
        # Return actual task data from registry
        return {
            "task_id": task_id,
            "status": task["history"][-1]["status"],
            "history": task["history"],
            "data": task["data"]
        }
    else:
        # Return mock data for demo
        return {
            "task_id": task_id,
            "status": "completed",
            "submitted_at": "2023-06-02T12:00:00Z",
            "completed_at": "2023-06-02T12:01:30Z",
            "result": {
                "success": True,
                "message": "Task completed successfully"
            }
        }

@app.get("/api/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all available agents and their status"""
    agent_statuses = {}
    
    # Get actual agent statuses
    for agent_id, agent in agents.items():
        agent_statuses[agent_id] = "active"
    
    # Add placeholder statuses for agents not yet implemented
    for agent_type in AgentType:
        agent_id = agent_type.value
        if agent_id not in agent_statuses:
            agent_statuses[agent_id] = "not_implemented"
    
    return {
        "agents": agent_statuses,
        "total_active": len([s for s in agent_statuses.values() if s == "active"])
    }

# Utility functions for background tasks
async def schedule_campaign_planning(campaign_id: str, campaign_data: Dict[str, Any]):
    """Background task to initiate campaign planning"""
    logger.info(f"Starting campaign planning for {campaign_id}")
    
    # In a real implementation, this would:
    # 1. Trigger the market research agent to gather data
    # 2. Trigger the ICP discovery agent to identify target audience
    # 3. Trigger the campaign planning agent to create a strategy
    
    # For demo purposes, just log the action
    logger.info(f"Campaign planning initiated for {campaign_id}")

async def generate_content(content_id: str, task_type: str, task_params: Dict[str, Any], target_languages: Optional[List[str]] = None):
    """Background task to generate content"""
    logger.info(f"Generating content {content_id} with task type {task_type}")
    
    try:
        # Get the content generation agent
        content_agent = agents.get("content_generation")
        if not content_agent:
            logger.error("Content generation agent not available")
            return
        
        # Create and execute the task
        task_request = TaskRequest(
            task_type=task_type,
            parameters=task_params
        )
        
        # Execute the task
        response = await content_agent.handle_message({
            "message_type": MessageType.TASK_REQUEST,
            "sender": "api",
            "recipients": ["content_generation_agent"],
            "payload": task_request.dict()
        })
        
        # If target languages are specified, localize the content
        if target_languages and response.status == TaskStatus.COMPLETED:
            await localize_content(content_id, response.result["content"], target_languages)
        
        logger.info(f"Content generation completed for {content_id}")
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")

async def localize_content(content_id: str, content: Dict[str, Any], target_languages: List[str]):
    """Background task to localize content"""
    logger.info(f"Localizing content {content_id} to {', '.join(target_languages)}")
    
    try:
        # Get the localization agent
        localization_agent = agents.get("localization")
        if not localization_agent:
            logger.error("Localization agent not available")
            return
        
        # For each target language, create and execute a translation task
        for language in target_languages:
            task_request = TaskRequest(
                task_type="translate_content",
                parameters={
                    "content_id": content_id,
                    "content_type": content.get("content_type", ""),
                    "content": content,
                    "target_lang": language
                }
            )
            
            # Execute the task
            await localization_agent.handle_message({
                "message_type": MessageType.TASK_REQUEST,
                "sender": "api",
                "recipients": ["localization_agent"],
                "payload": task_request.dict()
            })
        
        logger.info(f"Content localization completed for {content_id}")
    except Exception as e:
        logger.error(f"Error localizing content: {str(e)}")

async def post_content_to_platform(content_id: str, platform: str, content: Dict[str, Any], post_id: str):
    """Background task to post content to a social media platform"""
    logger.info(f"Posting content {content_id} to {platform}")
    
    try:
        # Get the social media agent
        social_media_agent = agents.get("social_media")
        if not social_media_agent:
            logger.error("Social media agent not available")
            return
        
        # Create and execute the task
        task_request = TaskRequest(
            task_type="post_to_platform",
            parameters={
                "content_id": content_id,
                "platform": platform,
                "content": content,
                "post_id": post_id
            }
        )
        
        # Execute the task
        await social_media_agent.handle_message({
            "message_type": MessageType.TASK_REQUEST,
            "sender": "api",
            "recipients": ["social_media_agent"],
            "payload": task_request.dict()
        })
        
        logger.info(f"Content posted to {platform} for {content_id}")
    except Exception as e:
        logger.error(f"Error posting content to {platform}: {str(e)}")

async def schedule_content_for_platform(content_id: str, platform: str, content: Dict[str, Any], schedule_time: str, schedule_id: str):
    """Background task to schedule content for a social media platform"""
    logger.info(f"Scheduling content {content_id} for {platform} at {schedule_time}")
    
    try:
        # Get the social media agent
        social_media_agent = agents.get("social_media")
        if not social_media_agent:
            logger.error("Social media agent not available")
            return
        
        # Create and execute the task
        task_request = TaskRequest(
            task_type="schedule_post",
            parameters={
                "content_id": content_id,
                "platform": platform,
                "content": content,
                "schedule_time": schedule_time,
                "schedule_id": schedule_id
            }
        )
        
        # Execute the task
        await social_media_agent.handle_message({
            "message_type": MessageType.TASK_REQUEST,
            "sender": "api",
            "recipients": ["social_media_agent"],
            "payload": task_request.dict()
        })
        
        logger.info(f"Content scheduled for {platform} at {schedule_time} for {content_id}")
    except Exception as e:
        logger.error(f"Error scheduling content for {platform}: {str(e)}")

async def execute_agent_task(agent_id: str, task_id: str, task_type: str, parameters: Dict[str, Any]):
    """Background task to execute an agent task"""
    logger.info(f"Executing task {task_id} on agent {agent_id}")
    
    try:
        # Get the agent
        agent = agents.get(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not available")
            return
        
        # Create and execute the task
        task_request = TaskRequest(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters
        )
        
        # Store the task in the registry
        registry.store_task(task_id, task_request.dict())
        
        # Update task status to in progress
        registry.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        
        # Execute the task
        response = await agent.handle_message({
            "message_type": MessageType.TASK_REQUEST,
            "sender": "api",
            "recipients": [f"{agent_id}_agent"],
            "payload": task_request.dict()
        })
        
        # Update task status based on response
        if hasattr(response, 'status'):
            registry.update_task_status(task_id, response.status)
        else:
            registry.update_task_status(task_id, TaskStatus.COMPLETED)
        
        logger.info(f"Task {task_id} executed successfully on agent {agent_id}")
    except Exception as e:
        logger.error(f"Error executing task: {str(e)}")
        registry.update_task_status(task_id, TaskStatus.FAILED, {"error": str(e)})

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
