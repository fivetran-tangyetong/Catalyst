"""
Content Generation Agent for Catalyst

This agent is responsible for generating marketing content, including text copy and 
visual content using Vizcom's AI rendering capabilities.
"""

import asyncio
import base64
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
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
logger = logging.getLogger("content_generation_agent")

# Vizcom API integration
class VizcomClient:
    """Client for interacting with Vizcom API for visual content generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.vizcom.ai/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    async def generate_from_sketch(self, 
                                  sketch_image: str, 
                                  prompt: str = None,
                                  style: str = "realistic",
                                  format: str = "png") -> Dict[str, Any]:
        """
        Transform a sketch into a photorealistic rendering
        
        Args:
            sketch_image: Base64 encoded image or URL to image
            prompt: Text prompt to guide the generation
            style: Visual style (realistic, artistic, etc.)
            format: Output format (png, jpg)
            
        Returns:
            Dictionary with generated image data
        """
        payload = {
            "image": sketch_image,
            "format": format,
            "style": style
        }
        
        if prompt:
            payload["prompt"] = prompt
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                headers=self.headers,
                json=payload,
                timeout=120  # Visual generation can take time
            )
            
            response.raise_for_status()
            return response.json()
    
    async def generate_from_text(self, 
                               prompt: str,
                               style: str = "realistic",
                               aspect_ratio: str = "1:1",
                               format: str = "png") -> Dict[str, Any]:
        """
        Generate an image from a text prompt
        
        Args:
            prompt: Text prompt describing the desired image
            style: Visual style (realistic, artistic, etc.)
            aspect_ratio: Aspect ratio of the output image
            format: Output format (png, jpg)
            
        Returns:
            Dictionary with generated image data
        """
        payload = {
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "format": format
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/create",
                headers=self.headers,
                json=payload,
                timeout=120  # Visual generation can take time
            )
            
            response.raise_for_status()
            return response.json()
    
    async def enhance_image(self, 
                          image: str, 
                          enhancement_type: str = "quality",
                          format: str = "png") -> Dict[str, Any]:
        """
        Enhance an existing image
        
        Args:
            image: Base64 encoded image or URL to image
            enhancement_type: Type of enhancement (quality, color, style)
            format: Output format (png, jpg)
            
        Returns:
            Dictionary with enhanced image data
        """
        payload = {
            "image": image,
            "enhancement_type": enhancement_type,
            "format": format
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/enhance",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
    
    async def create_variations(self, 
                              image: str, 
                              num_variations: int = 3,
                              format: str = "png") -> Dict[str, Any]:
        """
        Create variations of an existing image
        
        Args:
            image: Base64 encoded image or URL to image
            num_variations: Number of variations to generate
            format: Output format (png, jpg)
            
        Returns:
            Dictionary with variation image data
        """
        payload = {
            "image": image,
            "num_variations": num_variations,
            "format": format
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/variations",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    def encode_image_to_base64(image_path: str) -> str:
        """Convert an image file to base64 encoding"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    @staticmethod
    async def save_base64_image(base64_string: str, output_path: str) -> str:
        """Save a base64 encoded image to a file"""
        # Extract the actual base64 data if it includes a data URL prefix
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
            
        image_data = base64.b64decode(base64_string)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(image_data)
            
        return output_path

# Content Models
class ContentTemplate(BaseModel):
    """Model for content templates"""
    template_id: str
    name: str
    description: str
    template_type: str  # social_post, email, ad, etc.
    template_text: str
    variables: List[str]
    example_values: Dict[str, str]
    
class TextContent(BaseModel):
    """Model for text content"""
    content_id: str = Field(default_factory=lambda: f"txt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    content_type: str  # social_post, email, ad_copy, etc.
    title: Optional[str] = None
    body: str
    cta: Optional[str] = None  # Call to action
    keywords: List[str] = []
    tone: str = "professional"
    target_audience: Optional[str] = None
    character_limit: Optional[int] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class VisualContent(BaseModel):
    """Model for visual content"""
    content_id: str = Field(default_factory=lambda: f"img_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    content_type: str  # banner, product_image, social_graphic, etc.
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    prompt: Optional[str] = None
    style: str = "realistic"
    aspect_ratio: str = "1:1"
    colors: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class CombinedContent(BaseModel):
    """Model for combined text and visual content"""
    content_id: str = Field(default_factory=lambda: f"comb_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    content_type: str  # social_post, ad, email, etc.
    title: str
    text_content: TextContent
    visual_content: VisualContent
    platform: Optional[str] = None  # facebook, instagram, email, etc.
    target_audience: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ContentGenerationAgent(BaseAgent):
    """Agent for generating marketing content"""
    
    def __init__(self, agent_id: str, mcp_bus: MCPBus, vizcom_api_key: str):
        super().__init__(agent_id, AgentType.CONTENT_GENERATION, mcp_bus)
        self.vizcom_client = VizcomClient(vizcom_api_key)
        
        # Load content templates
        self.templates = self._load_content_templates()
        
        # Register task handlers
        self.register_task_handler("generate_text_content", self.handle_generate_text_content)
        self.register_task_handler("generate_visual_content", self.handle_generate_visual_content)
        self.register_task_handler("generate_combined_content", self.handle_generate_combined_content)
        self.register_task_handler("generate_content_variations", self.handle_generate_content_variations)
        self.register_task_handler("enhance_visual_content", self.handle_enhance_visual_content)
    
    async def start(self) -> None:
        """Start the agent"""
        await super().start()
        logger.info(f"Content Generation Agent {self.agent_id} started with Vizcom integration")
    
    def _load_content_templates(self) -> Dict[str, ContentTemplate]:
        """Load content templates from storage"""
        # In a real implementation, this would load from a database or file
        # For now, we'll return some hardcoded templates
        
        templates = {}
        
        # Social media post template
        social_template = ContentTemplate(
            template_id="social_basic_1",
            name="Basic Social Media Post",
            description="A simple social media post with a hook, body, and call to action",
            template_type="social_post",
            template_text="🔥 {hook}\n\n{body}\n\n{cta}",
            variables=["hook", "body", "cta"],
            example_values={
                "hook": "Introducing our new product!",
                "body": "Our new product solves {problem} with its innovative {feature}.",
                "cta": "Click the link to learn more and get 10% off your first purchase!"
            }
        )
        templates[social_template.template_id] = social_template
        
        # Email template
        email_template = ContentTemplate(
            template_id="email_announcement_1",
            name="Product Announcement Email",
            description="An email template for announcing a new product or feature",
            template_type="email",
            template_text="Subject: {subject}\n\nHi {first_name},\n\n{introduction}\n\n{body}\n\n{benefit_statement}\n\n{cta}\n\nBest regards,\n{sender_name}\n{company_name}",
            variables=["subject", "first_name", "introduction", "body", "benefit_statement", "cta", "sender_name", "company_name"],
            example_values={
                "subject": "Introducing Our New Product - Special Launch Offer Inside!",
                "first_name": "{first_name}",
                "introduction": "We're excited to announce the launch of our new product!",
                "body": "Our team has been working hard to create something that will help you {benefit}.",
                "benefit_statement": "With this new product, you'll be able to {key_benefit} and {secondary_benefit}.",
                "cta": "Click here to learn more and get your exclusive launch discount!",
                "sender_name": "John Smith",
                "company_name": "Acme Inc."
            }
        )
        templates[email_template.template_id] = email_template
        
        # Ad copy template
        ad_template = ContentTemplate(
            template_id="ad_copy_1",
            name="Basic Ad Copy",
            description="A template for creating ad copy with headline, body, and CTA",
            template_type="ad_copy",
            template_text="Headline: {headline}\n\nBody: {body}\n\nCTA: {cta}",
            variables=["headline", "body", "cta"],
            example_values={
                "headline": "Transform Your {pain_point} Today!",
                "body": "Our {product_name} helps you {benefit} without the {pain_point}. Join thousands of satisfied customers!",
                "cta": "Shop Now | Limited Time Offer"
            }
        )
        templates[ad_template.template_id] = ad_template
        
        return templates
    
    async def handle_generate_text_content(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to generate text content"""
        try:
            # Extract parameters
            content_type = task_request.parameters.get("content_type", "")
            if not content_type:
                raise ValueError("Content type is required")
                
            title = task_request.parameters.get("title", "")
            template_id = task_request.parameters.get("template_id", "")
            template_variables = task_request.parameters.get("template_variables", {})
            tone = task_request.parameters.get("tone", "professional")
            target_audience = task_request.parameters.get("target_audience", "")
            keywords = task_request.parameters.get("keywords", [])
            character_limit = task_request.parameters.get("character_limit")
            product_info = task_request.parameters.get("product_info", {})
            
            logger.info(f"Generating {content_type} text content with tone: {tone}")
            await self.send_log("info", f"Starting text content generation for {content_type}")
            
            # Generate the content
            if template_id and template_id in self.templates:
                # Use template-based generation
                content = await self._generate_from_template(
                    template_id, 
                    template_variables,
                    tone,
                    target_audience,
                    character_limit
                )
            else:
                # Use dynamic generation based on content type
                content = await self._generate_text_content(
                    content_type,
                    title,
                    tone,
                    target_audience,
                    keywords,
                    character_limit,
                    product_info
                )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "content": content.dict(),
                    "suggestions": await self._generate_content_suggestions(content)
                }
            )
        except Exception as e:
            logger.error(f"Error generating text content: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to generate text content: {str(e)}"
            )
    
    async def handle_generate_visual_content(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to generate visual content"""
        try:
            # Extract parameters
            content_type = task_request.parameters.get("content_type", "")
            if not content_type:
                raise ValueError("Content type is required")
                
            title = task_request.parameters.get("title", "")
            description = task_request.parameters.get("description", "")
            prompt = task_request.parameters.get("prompt", "")
            sketch_image = task_request.parameters.get("sketch_image", "")  # Base64 or URL
            style = task_request.parameters.get("style", "realistic")
            aspect_ratio = task_request.parameters.get("aspect_ratio", "1:1")
            colors = task_request.parameters.get("colors", [])
            product_info = task_request.parameters.get("product_info", {})
            
            logger.info(f"Generating {content_type} visual content with style: {style}")
            await self.send_log("info", f"Starting visual content generation for {content_type}")
            
            # Generate the content
            if sketch_image:
                # Generate from sketch
                if not prompt and description:
                    prompt = description
                    
                result = await self.vizcom_client.generate_from_sketch(
                    sketch_image=sketch_image,
                    prompt=prompt,
                    style=style
                )
                
                image_base64 = result.get("image", "")
                image_url = result.get("url", "")
            else:
                # Generate from text prompt
                if not prompt:
                    # Create prompt from description and product info
                    prompt = await self._create_visual_prompt(
                        content_type,
                        description,
                        product_info,
                        style,
                        colors
                    )
                
                result = await self.vizcom_client.generate_from_text(
                    prompt=prompt,
                    style=style,
                    aspect_ratio=aspect_ratio
                )
                
                image_base64 = result.get("image", "")
                image_url = result.get("url", "")
            
            # Create visual content object
            visual_content = VisualContent(
                content_type=content_type,
                title=title or f"{content_type.capitalize()} for {product_info.get('name', 'product')}",
                description=description,
                image_url=image_url,
                image_base64=image_base64,
                prompt=prompt,
                style=style,
                aspect_ratio=aspect_ratio,
                colors=colors,
                metadata={
                    "product_info": product_info,
                    "generation_params": {
                        "style": style,
                        "aspect_ratio": aspect_ratio
                    }
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "content": visual_content.dict(),
                    "generation_prompt": prompt
                }
            )
        except Exception as e:
            logger.error(f"Error generating visual content: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to generate visual content: {str(e)}"
            )
    
    async def handle_generate_combined_content(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to generate combined text and visual content"""
        try:
            # Extract parameters
            content_type = task_request.parameters.get("content_type", "")
            if not content_type:
                raise ValueError("Content type is required")
                
            title = task_request.parameters.get("title", "")
            platform = task_request.parameters.get("platform", "")
            target_audience = task_request.parameters.get("target_audience", "")
            product_info = task_request.parameters.get("product_info", {})
            
            # Text content parameters
            text_params = task_request.parameters.get("text_params", {})
            text_params["content_type"] = f"{content_type}_text"
            text_params["product_info"] = product_info
            text_params["target_audience"] = target_audience
            
            # Visual content parameters
            visual_params = task_request.parameters.get("visual_params", {})
            visual_params["content_type"] = f"{content_type}_image"
            visual_params["product_info"] = product_info
            
            logger.info(f"Generating combined {content_type} content for platform: {platform}")
            await self.send_log("info", f"Starting combined content generation for {content_type}")
            
            # Generate text content
            text_task = TaskRequest(
                task_type="generate_text_content",
                parameters=text_params
            )
            text_response = await self.handle_generate_text_content(text_task)
            
            if text_response.status != TaskStatus.COMPLETED:
                raise ValueError(f"Failed to generate text content: {text_response.error_message}")
            
            text_content = TextContent(**text_response.result["content"])
            
            # Use text content to enhance visual prompt if needed
            if "description" not in visual_params and text_content.body:
                visual_params["description"] = text_content.body[:100]  # Use part of the text as description
            
            # Generate visual content
            visual_task = TaskRequest(
                task_type="generate_visual_content",
                parameters=visual_params
            )
            visual_response = await self.handle_generate_visual_content(visual_task)
            
            if visual_response.status != TaskStatus.COMPLETED:
                raise ValueError(f"Failed to generate visual content: {visual_response.error_message}")
            
            visual_content = VisualContent(**visual_response.result["content"])
            
            # Create combined content
            combined_content = CombinedContent(
                content_type=content_type,
                title=title or f"{content_type.capitalize()} for {product_info.get('name', 'product')}",
                text_content=text_content,
                visual_content=visual_content,
                platform=platform,
                target_audience=target_audience,
                metadata={
                    "product_info": product_info,
                    "platform_specific": self._get_platform_specific_metadata(platform)
                }
            )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "content": combined_content.dict(),
                    "preview": self._create_content_preview(combined_content)
                }
            )
        except Exception as e:
            logger.error(f"Error generating combined content: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to generate combined content: {str(e)}"
            )
    
    async def handle_generate_content_variations(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to generate variations of existing content"""
        try:
            # Extract parameters
            content = task_request.parameters.get("content", {})
            content_type = content.get("content_type", "")
            num_variations = task_request.parameters.get("num_variations", 3)
            variation_params = task_request.parameters.get("variation_params", {})
            
            logger.info(f"Generating {num_variations} variations of {content_type} content")
            await self.send_log("info", f"Starting content variation generation for {content_type}")
            
            # Determine content type and generate variations
            variations = []
            
            if "text_content" in content and "visual_content" in content:
                # Combined content variations
                variations = await self._generate_combined_content_variations(
                    content,
                    num_variations,
                    variation_params
                )
            elif "body" in content:
                # Text content variations
                variations = await self._generate_text_content_variations(
                    content,
                    num_variations,
                    variation_params
                )
            elif "image_url" in content or "image_base64" in content:
                # Visual content variations
                variations = await self._generate_visual_content_variations(
                    content,
                    num_variations,
                    variation_params
                )
            else:
                raise ValueError("Unsupported content type for variations")
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "original_content": content,
                    "variations": variations,
                    "num_variations": len(variations)
                }
            )
        except Exception as e:
            logger.error(f"Error generating content variations: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to generate content variations: {str(e)}"
            )
    
    async def handle_enhance_visual_content(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to enhance existing visual content"""
        try:
            # Extract parameters
            image = task_request.parameters.get("image", "")  # Base64 or URL
            if not image:
                raise ValueError("Image is required")
                
            enhancement_type = task_request.parameters.get("enhancement_type", "quality")
            format = task_request.parameters.get("format", "png")
            
            logger.info(f"Enhancing visual content with enhancement type: {enhancement_type}")
            await self.send_log("info", f"Starting visual content enhancement")
            
            # Enhance the image
            result = await self.vizcom_client.enhance_image(
                image=image,
                enhancement_type=enhancement_type,
                format=format
            )
            
            enhanced_image_base64 = result.get("image", "")
            enhanced_image_url = result.get("url", "")
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "original_image": image[:100] + "..." if len(image) > 100 else image,  # Truncate for log readability
                    "enhanced_image_base64": enhanced_image_base64[:100] + "..." if len(enhanced_image_base64) > 100 else enhanced_image_base64,
                    "enhanced_image_url": enhanced_image_url,
                    "enhancement_type": enhancement_type
                }
            )
        except Exception as e:
            logger.error(f"Error enhancing visual content: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to enhance visual content: {str(e)}"
            )
    
    # Helper methods for text content generation
    async def _generate_from_template(self, 
                                    template_id: str, 
                                    variables: Dict[str, str],
                                    tone: str = "professional",
                                    target_audience: str = "",
                                    character_limit: Optional[int] = None) -> TextContent:
        """Generate text content from a template"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Fill in template variables
        text = template.template_text
        for var_name, var_value in variables.items():
            if var_name in template.variables:
                text = text.replace(f"{{{var_name}}}", var_value)
        
        # Check if all variables are filled
        for var_name in template.variables:
            if f"{{{var_name}}}" in text:
                # Variable not filled, use example value if available
                example_value = template.example_values.get(var_name, f"{{{var_name}}}")
                text = text.replace(f"{{{var_name}}}", example_value)
        
        # Apply character limit if specified
        if character_limit and len(text) > character_limit:
            text = text[:character_limit]
        
        # Create content object
        content = TextContent(
            content_type=template.template_type,
            title=variables.get("title", "") or variables.get("subject", "") or variables.get("headline", ""),
            body=text,
            cta=variables.get("cta", ""),
            keywords=[],  # Could extract keywords from the text
            tone=tone,
            target_audience=target_audience,
            character_limit=character_limit,
            metadata={
                "template_id": template_id,
                "template_name": template.name
            }
        )
        
        return content
    
    async def _generate_text_content(self,
                                   content_type: str,
                                   title: str,
                                   tone: str,
                                   target_audience: str,
                                   keywords: List[str],
                                   character_limit: Optional[int],
                                   product_info: Dict[str, Any]) -> TextContent:
        """Generate text content based on parameters"""
        # In a real implementation, this would use an LLM to generate the content
        # For this example, we'll use template-based generation
        
        # Select appropriate template based on content type
        template_id = None
        template_variables = {}
        
        if content_type in ["social_post", "social_media"]:
            template_id = "social_basic_1"
            template_variables = {
                "hook": f"Introducing {product_info.get('name', 'our new product')}!",
                "body": f"Our {product_info.get('name', 'product')} helps you {product_info.get('benefit', 'solve problems')} with its innovative {product_info.get('feature', 'features')}.",
                "cta": "Click the link to learn more and get 10% off your first purchase!"
            }
        elif content_type in ["email", "newsletter"]:
            template_id = "email_announcement_1"
            template_variables = {
                "subject": f"Introducing {product_info.get('name', 'Our New Product')} - Special Launch Offer Inside!",
                "first_name": "{first_name}",
                "introduction": f"We're excited to announce the launch of {product_info.get('name', 'our new product')}!",
                "body": f"Our team has been working hard to create something that will help you {product_info.get('benefit', 'achieve your goals')}.",
                "benefit_statement": f"With {product_info.get('name', 'this new product')}, you'll be able to {product_info.get('key_benefit', 'save time')} and {product_info.get('secondary_benefit', 'improve results')}.",
                "cta": "Click here to learn more and get your exclusive launch discount!",
                "sender_name": product_info.get('company_contact', 'The Team'),
                "company_name": product_info.get('company_name', 'Our Company')
            }
        elif content_type in ["ad", "ad_copy"]:
            template_id = "ad_copy_1"
            template_variables = {
                "headline": f"Transform Your {product_info.get('pain_point', 'Experience')} with {product_info.get('name', 'Our Product')}!",
                "body": f"Our {product_info.get('name', 'product')} helps you {product_info.get('benefit', 'achieve more')} without the {product_info.get('pain_point', 'hassle')}. Join thousands of satisfied customers!",
                "cta": "Shop Now | Limited Time Offer"
            }
        else:
            # Generic content generation for unsupported types
            body = f"Introducing {product_info.get('name', 'our new product')}!\n\n"
            body += f"Our {product_info.get('name', 'product')} is designed to {product_info.get('benefit', 'make your life easier')}. "
            body += f"With features like {product_info.get('feature', 'innovative technology')}, you'll experience {product_info.get('key_benefit', 'better results')}.\n\n"
            body += "Contact us today to learn more!"
            
            return TextContent(
                content_type=content_type,
                title=title or f"About {product_info.get('name', 'Our Product')}",
                body=body,
                cta="Learn More",
                keywords=keywords,
                tone=tone,
                target_audience=target_audience,
                character_limit=character_limit
            )
        
        # Generate from template
        return await self._generate_from_template(
            template_id,
            template_variables,
            tone,
            target_audience,
            character_limit
        )
    
    async def _generate_content_suggestions(self, content: TextContent) -> List[Dict[str, str]]:
        """Generate alternative suggestions for the content"""
        # In a real implementation, this would use an LLM to generate alternatives
        # For this example, we'll return some simple variations
        
        suggestions = []
        
        # Generate alternative headlines/titles
        if content.title:
            suggestions.append({
                "type": "alternative_title",
                "original": content.title,
                "suggestion": f"New and Improved: {content.title}"
            })
            
            suggestions.append({
                "type": "alternative_title",
                "original": content.title,
                "suggestion": f"{content.title} - Limited Time Offer!"
            })
        
        # Generate alternative CTAs
        if content.cta:
            suggestions.append({
                "type": "alternative_cta",
                "original": content.cta,
                "suggestion": f"{content.cta} Today!"
            })
            
            suggestions.append({
                "type": "alternative_cta",
                "original": content.cta,
                "suggestion": f"Don't Wait - {content.cta} Now"
            })
        
        # Generate tone variations
        suggestions.append({
            "type": "tone_variation",
            "original": "current tone",
            "suggestion": "Try a more casual, conversational tone for better engagement with younger audiences."
        })
        
        return suggestions
    
    # Helper methods for visual content generation
    async def _create_visual_prompt(self,
                                  content_type: str,
                                  description: str,
                                  product_info: Dict[str, Any],
                                  style: str,
                                  colors: List[str]) -> str:
        """Create a detailed prompt for visual content generation"""
        prompt = ""
        
        # Start with description if provided
        if description:
            prompt = description
        else:
            # Create a default prompt based on content type and product info
            product_name = product_info.get("name", "product")
            
            if content_type in ["product_image", "product_photo"]:
                prompt = f"Professional product photo of {product_name}"
                if "feature" in product_info:
                    prompt += f" showcasing its {product_info['feature']}"
                    
            elif content_type in ["banner", "header"]:
                prompt = f"Marketing banner for {product_name}"
                if "benefit" in product_info:
                    prompt += f" highlighting {product_info['benefit']}"
                    
            elif content_type in ["social_graphic", "social_image"]:
                prompt = f"Eye-catching social media graphic for {product_name}"
                if "key_benefit" in product_info:
                    prompt += f" showing {product_info['key_benefit']}"
                    
            elif content_type in ["ad_image", "advertisement"]:
                prompt = f"Compelling advertisement image for {product_name}"
                if "pain_point" in product_info:
                    prompt += f" solving {product_info['pain_point']}"
                    
            else:
                prompt = f"Visual representation of {product_name}"
        
        # Add style information
        if style and style != "realistic":
            prompt += f", in {style} style"
            
        # Add color information
        if colors:
            color_str = ", ".join(colors)
            prompt += f", using colors: {color_str}"
            
        # Add quality indicators
        prompt += ", high quality, professional lighting, detailed"
        
        return prompt
    
    # Helper methods for content variations
    async def _generate_text_content_variations(self,
                                             content: Dict[str, Any],
                                             num_variations: int,
                                             variation_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate variations of text content"""
        # In a real implementation, this would use an LLM to generate variations
        # For this example, we'll create simple variations
        
        variations = []
        original_content = TextContent(**content)
        
        # Different tones
        tones = ["professional", "casual", "enthusiastic", "formal", "friendly"]
        
        for i in range(min(num_variations, len(tones))):
            # Create a variation with a different tone
            tone = tones[i]
            if tone == original_content.tone:
                tone = tones[(i + 1) % len(tones)]
                
            # Create a variation of the body text
            body_variations = [
                f"{original_content.body} Don't miss this opportunity!",
                f"We're excited to share: {original_content.body}",
                f"Discover how {original_content.body.lower()}",
                f"Here's something special: {original_content.body}",
                f"Breaking news! {original_content.body}"
            ]
            
            variation = original_content.dict()
            variation["content_id"] = f"{original_content.content_id}_var{i+1}"
            variation["tone"] = tone
            variation["body"] = body_variations[i % len(body_variations)]
            
            if original_content.title:
                title_prefix = ["New:", "Introducing:", "Exclusive:", "Limited Offer:", "Just Launched:"]
                variation["title"] = f"{title_prefix[i % len(title_prefix)]} {original_content.title}"
                
            variations.append(variation)
        
        return variations
    
    async def _generate_visual_content_variations(self,
                                               content: Dict[str, Any],
                                               num_variations: int,
                                               variation_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate variations of visual content"""
        # In a real implementation, this would use Vizcom to generate variations
        # For this example, we'll simulate the variations
        
        variations = []
        original_content = VisualContent(**content)
        
        # If we have an image, generate real variations using Vizcom
        if original_content.image_base64:
            try:
                result = await self.vizcom_client.create_variations(
                    image=original_content.image_base64,
                    num_variations=num_variations
                )
                
                variation_images = result.get("images", [])
                
                for i, img in enumerate(variation_images):
                    variation = original_content.dict()
                    variation["content_id"] = f"{original_content.content_id}_var{i+1}"
                    variation["image_base64"] = img
                    variation["title"] = f"{original_content.title} - Variation {i+1}"
                    
                    # Vary some other properties
                    styles = ["realistic", "artistic", "minimalist", "vibrant", "vintage"]
                    variation["style"] = styles[i % len(styles)]
                    
                    variations.append(variation)
                    
                return variations
            except Exception as e:
                logger.warning(f"Failed to generate real variations, using simulated ones: {str(e)}")
        
        # If we can't generate real variations, create simulated ones
        styles = ["realistic", "artistic", "minimalist", "vibrant", "vintage"]
        aspect_ratios = ["1:1", "16:9", "4:3", "3:2", "9:16"]
        
        for i in range(num_variations):
            variation = original_content.dict()
            variation["content_id"] = f"{original_content.content_id}_var{i+1}"
            variation["style"] = styles[i % len(styles)]
            variation["aspect_ratio"] = aspect_ratios[i % len(aspect_ratios)]
            variation["title"] = f"{original_content.title} - Variation {i+1}"
            
            # We can't actually change the image without Vizcom API, so we'll keep the same image
            # but note that in a real implementation, each variation would have a different image
            
            variations.append(variation)
        
        return variations
    
    async def _generate_combined_content_variations(self,
                                                 content: Dict[str, Any],
                                                 num_variations: int,
                                                 variation_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate variations of combined content"""
        # Create variations by mixing text and visual variations
        
        variations = []
        original_content = CombinedContent(**content)
        
        # Generate text variations
        text_variations = await self._generate_text_content_variations(
            original_content.text_content.dict(),
            num_variations,
            variation_params
        )
        
        # Generate visual variations
        visual_variations = await self._generate_visual_content_variations(
            original_content.visual_content.dict(),
            num_variations,
            variation_params
        )
        
        # Create combined variations
        for i in range(num_variations):
            variation = original_content.dict()
            variation["content_id"] = f"{original_content.content_id}_var{i+1}"
            
            # Use corresponding variations if available, otherwise cycle through available ones
            text_var_idx = i % len(text_variations)
            visual_var_idx = i % len(visual_variations)
            
            variation["text_content"] = text_variations[text_var_idx]
            variation["visual_content"] = visual_variations[visual_var_idx]
            variation["title"] = f"{original_content.title} - Variation {i+1}"
            
            variations.append(variation)
        
        return variations
    
    def _get_platform_specific_metadata(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific metadata for content"""
        metadata = {}
        
        if platform.lower() == "facebook":
            metadata = {
                "optimal_image_size": "1200x630",
                "character_limit": 63206,
                "hashtag_limit": 30,
                "best_posting_times": ["9am-10am", "1pm-3pm"]
            }
        elif platform.lower() == "instagram":
            metadata = {
                "optimal_image_size": "1080x1080",
                "character_limit": 2200,
                "hashtag_limit": 30,
                "best_posting_times": ["11am-1pm", "7pm-9pm"]
            }
        elif platform.lower() == "twitter" or platform.lower() == "x":
            metadata = {
                "optimal_image_size": "1200x675",
                "character_limit": 280,
                "hashtag_limit": 2,
                "best_posting_times": ["8am-10am", "6pm-7pm"]
            }
        elif platform.lower() == "linkedin":
            metadata = {
                "optimal_image_size": "1200x627",
                "character_limit": 3000,
                "hashtag_limit": 5,
                "best_posting_times": ["8am-10am", "4pm-6pm"]
            }
        elif platform.lower() == "email":
            metadata = {
                "optimal_image_size": "600x400",
                "subject_line_limit": 50,
                "best_sending_times": ["10am-11am", "3pm-4pm"]
            }
        
        return metadata
    
    def _create_content_preview(self, content: CombinedContent) -> Dict[str, Any]:
        """Create a preview representation of the combined content"""
        preview = {
            "title": content.title,
            "platform": content.platform,
            "text_preview": content.text_content.body[:100] + "..." if len(content.text_content.body) > 100 else content.text_content.body,
            "has_image": bool(content.visual_content.image_url or content.visual_content.image_base64),
            "cta": content.text_content.cta,
            "metadata": self._get_platform_specific_metadata(content.platform) if content.platform else {}
        }
        
        return preview
