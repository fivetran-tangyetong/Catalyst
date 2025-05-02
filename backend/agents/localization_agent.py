"""
Localization Agent for Catalyst

This agent is responsible for translating and localizing marketing content using
DeepL's translation capabilities.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("localization_agent")

# DeepL API integration
class DeepLClient:
    """Client for interacting with DeepL API for translations"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepl.com/v2"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"DeepL-Auth-Key {api_key}"
        }
    
    async def translate_text(self, 
                           text: Union[str, List[str]], 
                           target_lang: str,
                           source_lang: Optional[str] = None,
                           preserve_formatting: bool = True,
                           formality: str = "default") -> Dict[str, Any]:
        """
        Translate text using DeepL API
        
        Args:
            text: Text or list of texts to translate
            target_lang: Target language code (e.g., 'EN', 'ES', 'FR')
            source_lang: Source language code (optional, auto-detected if not provided)
            preserve_formatting: Whether to preserve formatting
            formality: Formality level ('default', 'more', 'less')
            
        Returns:
            Dictionary with translated text
        """
        payload = {
            "text": text if isinstance(text, list) else [text],
            "target_lang": target_lang.upper(),
            "preserve_formatting": preserve_formatting,
            "formality": formality
        }
        
        if source_lang:
            payload["source_lang"] = source_lang.upper()
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/translate",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of a text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detected language information
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/detect",
                headers=self.headers,
                data={"text": text},
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
    
    async def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages
        
        Returns:
            List of dictionaries with language information
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/languages",
                headers=self.headers,
                params={"type": "target"},
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
    
    async def translate_document(self, 
                               document_path: str, 
                               target_lang: str,
                               source_lang: Optional[str] = None,
                               formality: str = "default") -> Dict[str, Any]:
        """
        Translate a document using DeepL API
        
        Args:
            document_path: Path to the document file
            target_lang: Target language code
            source_lang: Source language code (optional)
            formality: Formality level
            
        Returns:
            Dictionary with translated document information
        """
        # This is a simplified implementation
        # In a real implementation, this would use the document translation endpoint
        
        # For now, we'll read the document as text and translate it
        with open(document_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        result = await self.translate_text(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            preserve_formatting=True,
            formality=formality
        )
        
        return {
            "translated_text": result.get("translations", [{}])[0].get("text", ""),
            "source_lang": result.get("translations", [{}])[0].get("detected_source_language", ""),
            "target_lang": target_lang
        }

# Localization Models
class LocalizationRequest(BaseModel):
    """Model for localization requests"""
    content_id: str
    content_type: str
    content: Dict[str, Any]
    target_languages: List[str]
    source_language: Optional[str] = None
    preserve_formatting: bool = True
    formality: str = "default"
    fields_to_translate: List[str] = []  # Empty means translate all text fields
    
class LocalizedContent(BaseModel):
    """Model for localized content"""
    original_content_id: str
    localized_content_id: str = Field(default_factory=lambda: f"loc_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    content_type: str
    source_language: str
    target_language: str
    original_content: Dict[str, Any]
    localized_content: Dict[str, Any]
    translation_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LocalizationAgent(BaseAgent):
    """Agent for content localization and translation"""
    
    def __init__(self, agent_id: str, mcp_bus: MCPBus, deepl_api_key: str):
        super().__init__(agent_id, AgentType.LOCALIZATION, mcp_bus)
        self.deepl_client = DeepLClient(deepl_api_key)
        
        # Register task handlers
        self.register_task_handler("translate_text", self.handle_translate_text)
        self.register_task_handler("translate_content", self.handle_translate_content)
        self.register_task_handler("detect_language", self.handle_detect_language)
        self.register_task_handler("get_supported_languages", self.handle_get_supported_languages)
        self.register_task_handler("localize_campaign", self.handle_localize_campaign)
    
    async def start(self) -> None:
        """Start the agent"""
        await super().start()
        logger.info(f"Localization Agent {self.agent_id} started with DeepL integration")
        
        # Verify DeepL API connectivity
        try:
            languages = await self.deepl_client.get_supported_languages()
            logger.info(f"DeepL API connected successfully. {len(languages)} languages supported.")
        except Exception as e:
            logger.error(f"Failed to connect to DeepL API: {str(e)}")
    
    async def handle_translate_text(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to translate text"""
        try:
            # Extract parameters
            text = task_request.parameters.get("text", "")
            if not text:
                raise ValueError("Text is required")
                
            target_lang = task_request.parameters.get("target_lang", "")
            if not target_lang:
                raise ValueError("Target language is required")
                
            source_lang = task_request.parameters.get("source_lang")
            preserve_formatting = task_request.parameters.get("preserve_formatting", True)
            formality = task_request.parameters.get("formality", "default")
            
            logger.info(f"Translating text to {target_lang}")
            await self.send_log("info", f"Starting text translation to {target_lang}")
            
            # Translate the text
            result = await self.deepl_client.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                preserve_formatting=preserve_formatting,
                formality=formality
            )
            
            # Extract the translation
            translations = result.get("translations", [])
            if not translations:
                raise ValueError("No translations returned")
                
            translated_text = translations[0].get("text", "")
            detected_source_lang = translations[0].get("detected_source_language", "")
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "original_text": text,
                    "translated_text": translated_text,
                    "source_language": source_lang or detected_source_lang,
                    "target_language": target_lang,
                    "character_count": len(text)
                }
            )
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to translate text: {str(e)}"
            )
    
    async def handle_translate_content(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to translate structured content"""
        try:
            # Extract parameters
            content = task_request.parameters.get("content", {})
            if not content:
                raise ValueError("Content is required")
                
            content_id = task_request.parameters.get("content_id", "")
            content_type = task_request.parameters.get("content_type", "")
            target_lang = task_request.parameters.get("target_lang", "")
            if not target_lang:
                raise ValueError("Target language is required")
                
            source_lang = task_request.parameters.get("source_lang")
            fields_to_translate = task_request.parameters.get("fields_to_translate", [])
            preserve_formatting = task_request.parameters.get("preserve_formatting", True)
            formality = task_request.parameters.get("formality", "default")
            
            logger.info(f"Translating {content_type} content to {target_lang}")
            await self.send_log("info", f"Starting content translation to {target_lang}")
            
            # Create localization request
            localization_request = LocalizationRequest(
                content_id=content_id,
                content_type=content_type,
                content=content,
                target_languages=[target_lang],
                source_language=source_lang,
                preserve_formatting=preserve_formatting,
                formality=formality,
                fields_to_translate=fields_to_translate
            )
            
            # Translate the content
            localized_content = await self._translate_content(localization_request)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "localized_content": localized_content.dict()
                }
            )
        except Exception as e:
            logger.error(f"Error translating content: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to translate content: {str(e)}"
            )
    
    async def handle_detect_language(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to detect the language of text"""
        try:
            # Extract parameters
            text = task_request.parameters.get("text", "")
            if not text:
                raise ValueError("Text is required")
                
            logger.info("Detecting language")
            await self.send_log("info", "Starting language detection")
            
            # Detect the language
            result = await self.deepl_client.detect_language(text)
            
            # Extract the detected language
            detected_lang = result[0].get("language", "")
            confidence = result[0].get("confidence", 0)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "detected_language": detected_lang,
                    "confidence": confidence,
                    "text_sample": text[:100] + "..." if len(text) > 100 else text
                }
            )
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to detect language: {str(e)}"
            )
    
    async def handle_get_supported_languages(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to get supported languages"""
        try:
            logger.info("Getting supported languages")
            await self.send_log("info", "Retrieving supported languages from DeepL")
            
            # Get supported languages
            languages = await self.deepl_client.get_supported_languages()
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "supported_languages": languages,
                    "count": len(languages)
                }
            )
        except Exception as e:
            logger.error(f"Error getting supported languages: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to get supported languages: {str(e)}"
            )
    
    async def handle_localize_campaign(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to localize an entire marketing campaign"""
        try:
            # Extract parameters
            campaign = task_request.parameters.get("campaign", {})
            if not campaign:
                raise ValueError("Campaign data is required")
                
            target_languages = task_request.parameters.get("target_languages", [])
            if not target_languages:
                raise ValueError("Target languages are required")
                
            source_lang = task_request.parameters.get("source_lang")
            formality = task_request.parameters.get("formality", "default")
            
            logger.info(f"Localizing campaign to {', '.join(target_languages)}")
            await self.send_log("info", f"Starting campaign localization to {len(target_languages)} languages")
            
            # Process each content item in the campaign
            localized_campaign = {
                "campaign_id": campaign.get("campaign_id", ""),
                "campaign_name": campaign.get("campaign_name", ""),
                "source_language": source_lang,
                "localized_content": {}
            }
            
            # Get content items from the campaign
            content_items = campaign.get("content_items", [])
            
            # Process each content item for each target language
            for target_lang in target_languages:
                localized_campaign["localized_content"][target_lang] = []
                
                for content_item in content_items:
                    content_id = content_item.get("content_id", "")
                    content_type = content_item.get("content_type", "")
                    
                    # Create localization request
                    localization_request = LocalizationRequest(
                        content_id=content_id,
                        content_type=content_type,
                        content=content_item,
                        target_languages=[target_lang],
                        source_language=source_lang,
                        formality=formality
                    )
                    
                    # Translate the content
                    localized_content = await self._translate_content(localization_request)
                    
                    # Add to localized campaign
                    localized_campaign["localized_content"][target_lang].append(
                        localized_content.dict()
                    )
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "localized_campaign": localized_campaign,
                    "languages_processed": len(target_languages),
                    "content_items_processed": len(content_items)
                }
            )
        except Exception as e:
            logger.error(f"Error localizing campaign: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to localize campaign: {str(e)}"
            )
    
    # Helper methods for content translation
    async def _translate_content(self, request: LocalizationRequest) -> LocalizedContent:
        """Translate content based on its structure and type"""
        content = request.content
        target_lang = request.target_languages[0]  # Take the first target language
        source_lang = request.source_language
        
        # Determine which fields to translate
        fields_to_translate = request.fields_to_translate
        if not fields_to_translate:
            # If no specific fields are provided, find all text fields
            fields_to_translate = self._find_text_fields(content)
        
        # Create a copy of the original content
        localized_content = json.loads(json.dumps(content))
        
        # Track translation metadata
        translation_metadata = {
            "character_count": 0,
            "fields_translated": [],
            "source_language_detected": source_lang
        }
        
        # Translate each field
        for field_path in fields_to_translate:
            # Get the value to translate
            value = self._get_nested_value(content, field_path)
            
            if value and isinstance(value, str):
                # Translate the text
                result = await self.deepl_client.translate_text(
                    text=value,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    preserve_formatting=request.preserve_formatting,
                    formality=request.formality
                )
                
                # Extract the translation
                translations = result.get("translations", [])
                if translations:
                    translated_text = translations[0].get("text", "")
                    detected_source_lang = translations[0].get("detected_source_language", "")
                    
                    # Update the source language if it was auto-detected
                    if not source_lang:
                        source_lang = detected_source_lang
                        translation_metadata["source_language_detected"] = detected_source_lang
                    
                    # Set the translated value
                    self._set_nested_value(localized_content, field_path, translated_text)
                    
                    # Update metadata
                    translation_metadata["character_count"] += len(value)
                    translation_metadata["fields_translated"].append(field_path)
        
        # Create localized content object
        return LocalizedContent(
            original_content_id=request.content_id,
            content_type=request.content_type,
            source_language=source_lang or "",
            target_language=target_lang,
            original_content=content,
            localized_content=localized_content,
            translation_metadata=translation_metadata
        )
    
    def _find_text_fields(self, content: Dict[str, Any], prefix: str = "") -> List[str]:
        """Recursively find all text fields in a content object"""
        text_fields = []
        
        if isinstance(content, dict):
            for key, value in content.items():
                path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, str) and len(value) > 0:
                    # Found a text field
                    text_fields.append(path)
                elif isinstance(value, dict) or isinstance(value, list):
                    # Recursively search nested structures
                    nested_fields = self._find_text_fields(value, path)
                    text_fields.extend(nested_fields)
        elif isinstance(content, list):
            for i, item in enumerate(content):
                path = f"{prefix}[{i}]"
                
                if isinstance(item, str) and len(item) > 0:
                    # Found a text field
                    text_fields.append(path)
                elif isinstance(item, dict) or isinstance(item, list):
                    # Recursively search nested structures
                    nested_fields = self._find_text_fields(item, path)
                    text_fields.extend(nested_fields)
        
        return text_fields
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a value from a nested object using a dot-notation path"""
        if not path:
            return obj
        
        parts = path.split(".")
        current = obj
        
        for part in parts:
            # Handle array indexing
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str[:-1])  # Remove the closing bracket
                
                if key:
                    current = current.get(key, {})
                
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                # Handle dictionary access
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
        
        return current
    
    def _set_nested_value(self, obj: Any, path: str, value: Any) -> None:
        """Set a value in a nested object using a dot-notation path"""
        if not path:
            return
        
        parts = path.split(".")
        current = obj
        
        # Navigate to the parent of the target field
        for i, part in enumerate(parts[:-1]):
            # Handle array indexing
            if "[" in part and part.endswith("]"):
                key, index_str = part.split("[", 1)
                index = int(index_str[:-1])  # Remove the closing bracket
                
                if key:
                    if key not in current:
                        current[key] = []
                    current = current[key]
                
                if isinstance(current, list):
                    while len(current) <= index:
                        current.append({})
                    current = current[index]
            else:
                # Handle dictionary access
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # Set the value in the target field
        last_part = parts[-1]
        
        # Handle array indexing in the last part
        if "[" in last_part and last_part.endswith("]"):
            key, index_str = last_part.split("[", 1)
            index = int(index_str[:-1])  # Remove the closing bracket
            
            if key:
                if key not in current:
                    current[key] = []
                current = current[key]
            
            if isinstance(current, list):
                while len(current) <= index:
                    current.append("")
                current[index] = value
        else:
            # Handle dictionary access
            current[last_part] = value
