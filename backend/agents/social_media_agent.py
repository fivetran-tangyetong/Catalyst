"""
Social Media Outreach Agent for Catalyst Marketing Platform

This agent is responsible for posting and scheduling content to various social media platforms
using Arcade's API connectors.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("social_media_agent")

# Arcade API integration
class ArcadeClient:
    """Client for interacting with Arcade API for social media posting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.arcade.dev/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    async def get_platforms(self) -> List[Dict[str, Any]]:
        """Get available connected social media platforms"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/platforms",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("platforms", [])
    
    async def post_to_platform(self, 
                             platform: str, 
                             content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post content to a social media platform
        
        Args:
            platform: Platform identifier (facebook, twitter, instagram, linkedin)
            content: Content to post (text, images, links, etc.)
            
        Returns:
            Dictionary with post information
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/platforms/{platform}/post",
                headers=self.headers,
                json=content,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
    
    async def schedule_post(self, 
                          platform: str, 
                          content: Dict[str, Any],
                          schedule_time: datetime) -> Dict[str, Any]:
        """
        Schedule a post for future publishing
        
        Args:
            platform: Platform identifier
            content: Content to post
            schedule_time: When to publish the post
            
        Returns:
            Dictionary with scheduled post information
        """
        payload = {
            "content": content,
            "schedule_time": schedule_time.isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/platforms/{platform}/schedule",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
    
    async def get_post_status(self, post_id: str) -> Dict[str, Any]:
        """
        Get status of a post
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dictionary with post status information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/posts/{post_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics for a post
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dictionary with post analytics
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/posts/{post_id}/analytics",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_post(self, post_id: str) -> Dict[str, Any]:
        """
        Delete a post
        
        Args:
            post_id: ID of the post
            
        Returns:
            Dictionary with deletion status
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/posts/{post_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
    
    async def get_optimal_times(self, platform: str) -> List[Dict[str, Any]]:
        """
        Get optimal posting times for a platform
        
        Args:
            platform: Platform identifier
            
        Returns:
            List of optimal posting times with engagement scores
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/platforms/{platform}/optimal-times",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("times", [])
    
    async def get_scheduled_posts(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled posts
        
        Returns:
            List of scheduled posts
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/scheduled-posts",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("posts", [])

# Social Media Models
class SocialMediaPost(BaseModel):
    """Model for social media post data"""
    post_id: Optional[str] = None
    platform: str
    content_type: str  # text, image, video, link, carousel
    text: Optional[str] = None
    media_urls: List[str] = []
    link: Optional[str] = None
    hashtags: List[str] = []
    mentions: List[str] = []
    scheduled_time: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, published, failed
    analytics: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScheduleRequest(BaseModel):
    """Model for post scheduling requests"""
    post_id: Optional[str] = None
    platform: str
    content: Dict[str, Any]
    schedule_time: datetime
    timezone: str = "UTC"
    recurrence: Optional[str] = None  # daily, weekly, monthly
    end_date: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class SocialMediaAgent(BaseAgent):
    """Agent for social media outreach and posting"""
    
    def __init__(self, agent_id: str, mcp_bus: MCPBus, arcade_api_key: str):
        super().__init__(agent_id, AgentType.OUTREACH, mcp_bus)
        self.arcade_client = ArcadeClient(arcade_api_key)
        
        # Register task handlers
        self.register_task_handler("post_to_platform", self.handle_post_to_platform)
        self.register_task_handler("schedule_post", self.handle_schedule_post)
        self.register_task_handler("get_post_status", self.handle_get_post_status)
        self.register_task_handler("get_post_analytics", self.handle_get_post_analytics)
        self.register_task_handler("get_optimal_times", self.handle_get_optimal_times)
        self.register_task_handler("get_scheduled_posts", self.handle_get_scheduled_posts)
    
    async def start(self) -> None:
        """Start the agent"""
        await super().start()
        logger.info(f"Social Media Agent {self.agent_id} started with Arcade integration")
        
        # Verify Arcade API connectivity
        try:
            platforms = await self.arcade_client.get_platforms()
            logger.info(f"Arcade API connected successfully. {len(platforms)} platforms available.")
        except Exception as e:
            logger.error(f"Failed to connect to Arcade API: {str(e)}")
    
    async def handle_post_to_platform(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to post content to a social media platform"""
        try:
            # Extract parameters
            platform = task_request.parameters.get("platform", "")
            if not platform:
                raise ValueError("Platform is required")
                
            content = task_request.parameters.get("content", {})
            if not content:
                raise ValueError("Content is required")
            
            logger.info(f"Posting content to {platform}")
            await self.send_log("info", f"Starting content posting to {platform}")
            
            # Post the content
            result = await self.arcade_client.post_to_platform(
                platform=platform,
                content=content
            )
            
            # Create a post object
            post = SocialMediaPost(
                post_id=result.get("post_id"),
                platform=platform,
                content_type=content.get("type", "text"),
                text=content.get("text"),
                media_urls=content.get("media_urls", []),
                link=content.get("link"),
                hashtags=content.get("hashtags", []),
                mentions=content.get("mentions", []),
                status="published",
                metadata={
                    "platform_specific": result.get("platform_data", {}),
                    "original_request": task_request.parameters
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "post": post.dict(),
                    "platform_response": result
                }
            )
        except Exception as e:
            logger.error(f"Error posting to platform: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to post to platform: {str(e)}"
            )
    
    async def handle_schedule_post(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to schedule a post for future publishing"""
        try:
            # Extract parameters
            platform = task_request.parameters.get("platform", "")
            if not platform:
                raise ValueError("Platform is required")
                
            content = task_request.parameters.get("content", {})
            if not content:
                raise ValueError("Content is required")
                
            schedule_time_str = task_request.parameters.get("schedule_time", "")
            if not schedule_time_str:
                raise ValueError("Schedule time is required")
                
            # Parse schedule time
            schedule_time = datetime.fromisoformat(schedule_time_str)
            
            logger.info(f"Scheduling post for {platform} at {schedule_time}")
            await self.send_log("info", f"Scheduling content for {platform}")
            
            # Schedule the post
            result = await self.arcade_client.schedule_post(
                platform=platform,
                content=content,
                schedule_time=schedule_time
            )
            
            # Create a post object
            post = SocialMediaPost(
                post_id=result.get("post_id"),
                platform=platform,
                content_type=content.get("type", "text"),
                text=content.get("text"),
                media_urls=content.get("media_urls", []),
                link=content.get("link"),
                hashtags=content.get("hashtags", []),
                mentions=content.get("mentions", []),
                scheduled_time=schedule_time,
                status="scheduled",
                metadata={
                    "platform_specific": result.get("platform_data", {}),
                    "original_request": task_request.parameters
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "post": post.dict(),
                    "scheduled_id": result.get("scheduled_id"),
                    "scheduled_time": schedule_time.isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error scheduling post: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to schedule post: {str(e)}"
            )
    
    async def handle_get_post_status(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get the status of a post"""
        try:
            # Extract parameters
            post_id = task_request.parameters.get("post_id", "")
            if not post_id:
                raise ValueError("Post ID is required")
            
            logger.info(f"Getting status for post {post_id}")
            
            # Get post status
            result = await self.arcade_client.get_post_status(post_id)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "post_id": post_id,
                    "status": result.get("status"),
                    "platform": result.get("platform"),
                    "published_at": result.get("published_at"),
                    "url": result.get("url")
                }
            )
        except Exception as e:
            logger.error(f"Error getting post status: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get post status: {str(e)}"
            )
    
    async def handle_get_post_analytics(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get analytics for a post"""
        try:
            # Extract parameters
            post_id = task_request.parameters.get("post_id", "")
            if not post_id:
                raise ValueError("Post ID is required")
            
            logger.info(f"Getting analytics for post {post_id}")
            
            # Get post analytics
            result = await self.arcade_client.get_post_analytics(post_id)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "post_id": post_id,
                    "analytics": result.get("analytics", {}),
                    "engagement": result.get("engagement", {}),
                    "reach": result.get("reach", 0),
                    "impressions": result.get("impressions", 0),
                    "clicks": result.get("clicks", 0),
                    "likes": result.get("likes", 0),
                    "shares": result.get("shares", 0),
                    "comments": result.get("comments", 0)
                }
            )
        except Exception as e:
            logger.error(f"Error getting post analytics: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get post analytics: {str(e)}"
            )
    
    async def handle_get_optimal_times(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get optimal posting times for a platform"""
        try:
            # Extract parameters
            platform = task_request.parameters.get("platform", "")
            if not platform:
                raise ValueError("Platform is required")
            
            logger.info(f"Getting optimal posting times for {platform}")
            
            # Get optimal times
            times = await self.arcade_client.get_optimal_times(platform)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "platform": platform,
                    "optimal_times": times,
                    "best_time": times[0] if times else None,
                    "recommendations": self._generate_posting_recommendations(times)
                }
            )
        except Exception as e:
            logger.error(f"Error getting optimal times: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get optimal times: {str(e)}"
            )
    
    async def handle_get_scheduled_posts(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get all scheduled posts"""
        try:
            logger.info("Getting scheduled posts")
            
            # Get scheduled posts
            posts = await self.arcade_client.get_scheduled_posts()
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "posts": posts,
                    "count": len(posts),
                    "upcoming": [p for p in posts if datetime.fromisoformat(p.get("schedule_time", "")) > datetime.utcnow()]
                }
            )
        except Exception as e:
            logger.error(f"Error getting scheduled posts: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get scheduled posts: {str(e)}"
            )
    
    # Helper methods
    def _generate_posting_recommendations(self, optimal_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate posting recommendations based on optimal times"""
        recommendations = []
        
        if not optimal_times:
            return recommendations
        
        # Group times by day of week
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        times_by_day = {day: [] for day in days_of_week}
        
        for time_data in optimal_times:
            time_str = time_data.get("time")
            if time_str:
                dt = datetime.fromisoformat(time_str)
                day = days_of_week[dt.weekday()]
                times_by_day[day].append({
                    "time": dt.strftime("%H:%M"),
                    "engagement_score": time_data.get("engagement_score", 0)
                })
        
        # Generate recommendations for each day
        for day, times in times_by_day.items():
            if times:
                # Sort by engagement score
                sorted_times = sorted(times, key=lambda x: x["engagement_score"], reverse=True)
                best_time = sorted_times[0]
                
                recommendations.append({
                    "day": day,
                    "best_time": best_time["time"],
                    "engagement_score": best_time["engagement_score"],
                    "alternative_times": [t["time"] for t in sorted_times[1:3]] if len(sorted_times) > 1 else []
                })
        
        return recommendations
    
    async def format_content_for_platform(self, content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Format content for a specific platform"""
        formatted_content = content.copy()
        
        # Apply platform-specific formatting
        if platform == "twitter":
            # Twitter has character limits
            if "text" in formatted_content and len(formatted_content["text"]) > 280:
                formatted_content["text"] = formatted_content["text"][:277] + "..."
                
            # Limit hashtags
            if "hashtags" in formatted_content and len(formatted_content["hashtags"]) > 2:
                formatted_content["hashtags"] = formatted_content["hashtags"][:2]
                
        elif platform == "instagram":
            # Instagram requires media
            if "media_urls" not in formatted_content or not formatted_content["media_urls"]:
                raise ValueError("Instagram posts require at least one image or video")
                
        elif platform == "linkedin":
            # LinkedIn has different formatting for business posts
            if "company_id" in formatted_content:
                formatted_content["is_company_post"] = True
                
        elif platform == "facebook":
            # Facebook allows longer posts
            pass
        
        return formatted_content
    
    async def suggest_hashtags(self, content_text: str, platform: str) -> List[str]:
        """Suggest hashtags based on content text and platform"""
        # This is a simplified implementation
        # In a real system, this would use NLP or trending hashtag APIs
        
        # Extract potential hashtags from content
        words = content_text.lower().split()
        potential_tags = [word for word in words if len(word) > 4]
        
        # Filter to most relevant
        relevant_tags = potential_tags[:5]
        
        # Format as hashtags
        hashtags = [f"#{tag}" for tag in relevant_tags]
        
        # Add platform-specific popular tags
        if platform == "instagram":
            hashtags.extend(["#instagood", "#photooftheday"])
        elif platform == "twitter":
            hashtags.extend(["#trending", "#news"])
        
        # Remove duplicates
        return list(set(hashtags))
