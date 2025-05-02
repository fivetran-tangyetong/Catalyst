"""
Market Research Agent for Catalyst

This agent is responsible for gathering market intelligence, trends, and competitor 
information using Apify web scraping capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import httpx
from pydantic import BaseModel

from backend.protocols.mcp import (
    BaseAgent, 
    AgentType, 
    TaskRequest, 
    TaskResponse, 
    TaskStatus, 
    MCPBus,
    Priority
)

# Import the ApifyMCPClient instead of using direct API
from backend.integrations.mcp_clients import ApifyMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market_research_agent")

class MarketTrend(BaseModel):
    """Model for market trend data"""
    keyword: str
    volume: int
    growth_rate: float
    related_terms: List[str]
    sources: List[str]
    timestamp: datetime = datetime.utcnow()

class CompetitorInfo(BaseModel):
    """Model for competitor information"""
    name: str
    website: str
    social_profiles: Dict[str, str]
    products: List[str]
    marketing_channels: List[str]
    key_messages: List[str]
    strengths: List[str]
    weaknesses: List[str]
    timestamp: datetime = datetime.utcnow()

class MarketResearchAgent(BaseAgent):
    """Agent for market research and competitive intelligence"""
    
    def __init__(self, agent_id: str, mcp_bus: MCPBus, apify_token: str):
        super().__init__(agent_id, AgentType.MARKET_RESEARCH, mcp_bus)
        # Replace ApifyClient with ApifyMCPClient
        self.apify_client = ApifyMCPClient(apify_token)
        
        # Register task handlers
        self.register_task_handler("analyze_trends", self.handle_analyze_trends)
        self.register_task_handler("research_competitors", self.handle_research_competitors)
        self.register_task_handler("keyword_research", self.handle_keyword_research)
        self.register_task_handler("social_media_analysis", self.handle_social_media_analysis)
        self.register_task_handler("market_sentiment", self.handle_market_sentiment)
    
    async def start(self) -> None:
        """Start the agent"""
        await super().start()
        logger.info(f"Market Research Agent {self.agent_id} started with Apify MCP integration")
        
        # Connect to Apify MCP server
        try:
            connected = await self.apify_client.connect()
            if connected:
                logger.info("Connected to Apify MCP server")
            else:
                logger.warning("Failed to connect to Apify MCP server")
        except Exception as e:
            logger.error(f"Error connecting to Apify MCP server: {str(e)}")
    
    async def handle_analyze_trends(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to analyze market trends"""
        try:
            # Extract parameters
            product_category = task_request.parameters.get("product_category", "")
            timeframe = task_request.parameters.get("timeframe", "last 30 days")
            
            logger.info(f"Analyzing trends for {product_category} over {timeframe}")
            await self.send_log("info", f"Starting trend analysis for {product_category}")
            
            # Search for trends using Apify MCP client
            search_results = await self.search_google(
                f"{product_category} trends {timeframe}", 
                num_results=20
            )
            
            # Extract and analyze trend data
            trends = await self._extract_trends(search_results, product_category)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "trends": [trend.dict() for trend in trends],
                    "summary": self._generate_trend_summary(trends),
                    "raw_data": search_results[:5]  # Include a sample of raw data
                }
            )
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to analyze trends: {str(e)}"
            )
    
    async def handle_research_competitors(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to research competitors"""
        try:
            # Extract parameters
            product_name = task_request.parameters.get("product_name", "")
            company_name = task_request.parameters.get("company_name", "")
            industry = task_request.parameters.get("industry", "")
            
            logger.info(f"Researching competitors for {product_name} in {industry}")
            await self.send_log("info", f"Starting competitor research for {product_name}")
            
            # Search for competitors using Apify MCP client
            search_results = await self.search_google(
                f"{industry} {product_name} competitors", 
                num_results=15
            )
            
            # Extract competitor information
            competitors = await self._extract_competitors(search_results, company_name)
            
            # Get detailed info for each competitor
            detailed_competitors = []
            for competitor in competitors[:5]:  # Limit to top 5 competitors for detailed analysis
                detailed_info = await self._get_detailed_competitor_info(competitor.name, competitor.website)
                detailed_competitors.append({**competitor.dict(), **detailed_info})
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "competitors": detailed_competitors,
                    "total_found": len(competitors),
                    "detailed_analysis": len(detailed_competitors)
                }
            )
        except Exception as e:
            logger.error(f"Error researching competitors: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to research competitors: {str(e)}"
            )
    
    async def handle_keyword_research(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to perform keyword research"""
        try:
            # Extract parameters
            product_name = task_request.parameters.get("product_name", "")
            industry = task_request.parameters.get("industry", "")
            target_audience = task_request.parameters.get("target_audience", "")
            
            logger.info(f"Performing keyword research for {product_name}")
            await self.send_log("info", f"Starting keyword research for {product_name}")
            
            # Generate seed keywords
            seed_keywords = self._generate_seed_keywords(product_name, industry, target_audience)
            
            # Search for each seed keyword
            keyword_data = []
            for keyword in seed_keywords[:10]:  # Limit to top 10 seed keywords
                search_results = await self.search_google(keyword, num_results=10)
                related_searches = self._extract_related_searches(search_results)
                
                keyword_data.append({
                    "keyword": keyword,
                    "search_volume_estimate": self._estimate_search_volume(search_results),
                    "competition_level": self._estimate_competition_level(search_results),
                    "related_searches": related_searches
                })
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "keywords": keyword_data,
                    "recommended_primary_keywords": self._select_primary_keywords(keyword_data),
                    "recommended_secondary_keywords": self._select_secondary_keywords(keyword_data)
                }
            )
        except Exception as e:
            logger.error(f"Error performing keyword research: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to perform keyword research: {str(e)}"
            )
    
    async def handle_social_media_analysis(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to analyze social media for a product or brand"""
        try:
            # Extract parameters
            product_name = task_request.parameters.get("product_name", "")
            platforms = task_request.parameters.get("platforms", ["twitter", "instagram"])
            
            logger.info(f"Analyzing social media for {product_name} on {', '.join(platforms)}")
            await self.send_log("info", f"Starting social media analysis for {product_name}")
            
            # Collect data from each platform
            platform_data = {}
            for platform in platforms:
                try:
                    data = await self.scrape_social_media(platform, product_name)
                    platform_data[platform] = data
                except ValueError as e:
                    logger.warning(f"Skipping unsupported platform {platform}: {str(e)}")
                    continue
            
            # Analyze the collected data
            analysis = self._analyze_social_media_data(platform_data, product_name)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "analysis": analysis,
                    "sample_posts": self._extract_sample_posts(platform_data),
                    "platforms_analyzed": list(platform_data.keys())
                }
            )
        except Exception as e:
            logger.error(f"Error analyzing social media: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to analyze social media: {str(e)}"
            )
    
    async def handle_market_sentiment(self, task_request: TaskRequest) -> TaskResponse:
        """Handle a request to analyze market sentiment for a product or brand"""
        try:
            # Extract parameters
            product_name = task_request.parameters.get("product_name", "")
            sources = task_request.parameters.get("sources", ["reviews", "social", "news"])
            
            logger.info(f"Analyzing market sentiment for {product_name} from {', '.join(sources)}")
            await self.send_log("info", f"Starting market sentiment analysis for {product_name}")
            
            # Collect data from different sources
            sentiment_data = {}
            
            if "reviews" in sources:
                # Search for product reviews
                search_results = await self.search_google(
                    f"{product_name} reviews", 
                    num_results=15
                )
                sentiment_data["reviews"] = self._extract_review_sentiment(search_results)
            
            if "social" in sources:
                # Get social media data
                social_data = {}
                for platform in ["twitter"]:  # Can expand to more platforms
                    try:
                        data = await self.scrape_social_media(platform, product_name)
                        social_data[platform] = data
                    except ValueError:
                        continue
                sentiment_data["social"] = self._extract_social_sentiment(social_data)
            
            if "news" in sources:
                # Search for news articles
                search_results = await self.search_google(
                    f"{product_name} news", 
                    num_results=15
                )
                sentiment_data["news"] = self._extract_news_sentiment(search_results)
            
            # Analyze overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(sentiment_data)
            
            # Return the results
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.COMPLETED,
                result={
                    "overall_sentiment": overall_sentiment,
                    "sentiment_by_source": sentiment_data,
                    "key_positive_points": self._extract_key_points(sentiment_data, "positive"),
                    "key_negative_points": self._extract_key_points(sentiment_data, "negative")
                }
            )
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {str(e)}")
            return TaskResponse(
                task_id=task_request.task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to analyze market sentiment: {str(e)}"
            )
    
    # Updated methods to use Apify MCP client
    async def search_google(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search Google using the Apify Google Search Results Scraper via MCP"""
        try:
            # Prepare input for the actor
            input_data = {
                "queries": query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": num_results,
                "mobileResults": False,
                "languageCode": "en",
                "countryCode": "US"
            }
            
            # Run the actor using MCP client
            result = await self.apify_client.run_actor("apify/google-search-scraper", input_data)
            
            # Extract and return the results
            if "content" in result and isinstance(result["content"], list):
                return result["content"]
            else:
                logger.warning("Unexpected result format from Google search")
                return []
        except Exception as e:
            logger.error(f"Error searching Google: {str(e)}")
            return []
    
    async def scrape_web_page(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a web page using the Apify Web Scraper actor via MCP"""
        try:
            # Prepare input for the actor
            input_data = {
                "startUrls": [{"url": url}],
                "pseudoUrls": [],
                "linkSelector": "a",
                "pageFunction": """
                async function pageFunction(context) {
                    const { request, log, $ } = context;
                    const title = $('title').text();
                    const metaDescription = $('meta[name="description"]').attr('content');
                    const h1 = $('h1').text();
                    
                    const data = {
                        url: request.url,
                        title: title,
                        metaDescription: metaDescription,
                        h1: h1,
                        text: $('body').text(),
                    };
                    
                    return data;
                }
                """
            }
            
            # Run the actor using MCP client
            result = await self.apify_client.run_actor("apify/web-scraper", input_data)
            
            # Extract and return the results
            if "content" in result and isinstance(result["content"], list):
                return result["content"]
            else:
                logger.warning("Unexpected result format from web scraper")
                return []
        except Exception as e:
            logger.error(f"Error scraping web page: {str(e)}")
            return []
    
    async def scrape_social_media(self, platform: str, query: str) -> List[Dict[str, Any]]:
        """Scrape social media platforms for content related to a query via MCP"""
        try:
            actor_id = None
            input_data = {}
            
            if platform.lower() == "twitter":
                actor_id = "apify/twitter-scraper"
                input_data = {
                    "searchTerms": [query],
                    "maxItems": 100,
                    "maxRequestRetries": 3
                }
            elif platform.lower() == "instagram":
                actor_id = "apify/instagram-scraper"
                input_data = {
                    "searchQuery": query,
                    "resultsLimit": 100
                }
            else:
                raise ValueError(f"Unsupported social media platform: {platform}")
            
            # Run the actor using MCP client
            result = await self.apify_client.run_actor(actor_id, input_data)
            
            # Extract and return the results
            if "content" in result and isinstance(result["content"], list):
                return result["content"]
            else:
                logger.warning(f"Unexpected result format from {platform} scraper")
                return []
        except Exception as e:
            logger.error(f"Error scraping {platform}: {str(e)}")
            return []
    
    # Helper methods for trend analysis
    async def _extract_trends(self, search_results: List[Dict[str, Any]], product_category: str) -> List[MarketTrend]:
        """Extract market trends from search results"""
        trends = []
        seen_keywords = set()
        
        for result in search_results:
            # Extract potential trend keywords from titles and snippets
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Simple keyword extraction (in a real implementation, this would be more sophisticated)
            keywords = self._extract_keywords(f"{title} {snippet}", product_category)
            
            for keyword in keywords:
                if keyword not in seen_keywords:
                    seen_keywords.add(keyword)
                    
                    # Create a trend object with estimated metrics
                    # In a real implementation, these would be calculated from actual data
                    trend = MarketTrend(
                        keyword=keyword,
                        volume=self._estimate_keyword_volume(keyword),
                        growth_rate=self._estimate_growth_rate(keyword),
                        related_terms=self._generate_related_terms(keyword),
                        sources=[result.get("url", "")]
                    )
                    trends.append(trend)
        
        # Sort trends by estimated volume
        trends.sort(key=lambda x: x.volume, reverse=True)
        return trends[:10]  # Return top 10 trends
    
    def _extract_keywords(self, text: str, product_category: str) -> List[str]:
        """Extract relevant keywords from text"""
        # This is a simplified implementation
        # In a real system, this would use NLP techniques for keyword extraction
        keywords = []
        
        # Split text into words and filter
        words = text.lower().split()
        filtered_words = [word for word in words if len(word) > 3]
        
        # Look for phrases containing the product category
        for i in range(len(filtered_words) - 1):
            if product_category.lower() in filtered_words[i]:
                if i > 0:
                    keywords.append(f"{filtered_words[i-1]} {filtered_words[i]}")
                if i < len(filtered_words) - 1:
                    keywords.append(f"{filtered_words[i]} {filtered_words[i+1]}")
        
        # Add some individual words that might be trends
        trend_indicators = ["new", "trending", "popular", "emerging", "latest"]
        for word in filtered_words:
            if word in trend_indicators and word not in keywords:
                keywords.append(word)
        
        return list(set(keywords))
    
    def _estimate_keyword_volume(self, keyword: str) -> int:
        """Estimate search volume for a keyword"""
        # This is a placeholder - in a real implementation, this would use actual data
        import random
        return random.randint(1000, 10000)
    
    def _estimate_growth_rate(self, keyword: str) -> float:
        """Estimate growth rate for a keyword trend"""
        # This is a placeholder - in a real implementation, this would use actual data
        import random
        return random.uniform(0.05, 0.5)
    
    def _generate_related_terms(self, keyword: str) -> List[str]:
        """Generate related terms for a keyword"""
        # This is a placeholder - in a real implementation, this would use actual data
        words = keyword.split()
        related = []
        
        for word in words:
            related.append(f"best {word}")
            related.append(f"{word} benefits")
            related.append(f"{word} features")
        
        return related
    
    def _generate_trend_summary(self, trends: List[MarketTrend]) -> str:
        """Generate a summary of the identified trends"""
        if not trends:
            return "No significant trends identified."
        
        top_trends = trends[:3]
        trend_names = [t.keyword for t in top_trends]
        
        summary = f"Analysis identified {len(trends)} relevant market trends. "
        summary += f"The top trends are: {', '.join(trend_names)}. "
        
        # Add some insights about the top trend
        top_trend = trends[0]
        summary += f"The leading trend '{top_trend.keyword}' shows an estimated growth rate "
        summary += f"of {int(top_trend.growth_rate * 100)}% with related terms including "
        summary += f"{', '.join(top_trend.related_terms[:3])}."
        
        return summary
    
    # Helper methods for competitor research
    async def _extract_competitors(self, search_results: List[Dict[str, Any]], company_name: str) -> List[CompetitorInfo]:
        """Extract competitor information from search results"""
        competitors = []
        seen_companies = set()
        
        if company_name:
            seen_companies.add(company_name.lower())
        
        for result in search_results:
            # Extract potential competitor names from titles and snippets
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            
            # Extract company names (simplified implementation)
            company_names = self._extract_company_names(f"{title} {snippet}")
            
            for name in company_names:
                if name.lower() not in seen_companies:
                    seen_companies.add(name.lower())
                    
                    # Create a competitor object with basic information
                    competitor = CompetitorInfo(
                        name=name,
                        website=self._extract_website(name, url),
                        social_profiles={},
                        products=[],
                        marketing_channels=[],
                        key_messages=[],
                        strengths=[],
                        weaknesses=[]
                    )
                    competitors.append(competitor)
        
        return competitors
    
    def _extract_company_names(self, text: str) -> List[str]:
        """Extract company names from text"""
        # This is a simplified implementation
        # In a real system, this would use NLP techniques for named entity recognition
        
        # Look for company indicators
        company_indicators = ["Inc", "LLC", "Ltd", "Corporation", "Corp", "Company", "Co"]
        words = text.split()
        
        companies = []
        for i in range(len(words) - 1):
            if words[i] in company_indicators:
                # Look for a potential company name before the indicator
                if i > 0:
                    companies.append(f"{words[i-1]} {words[i]}")
            
            # Look for capitalized words that might be company names
            if words[i][0].isupper() and len(words[i]) > 3:
                companies.append(words[i])
        
        return list(set(companies))
    
    def _extract_website(self, company_name: str, url: str) -> str:
        """Extract or guess a website for a company"""
        # If the company name appears in the URL, use that URL
        if company_name.lower().replace(" ", "") in url.lower():
            return url
        
        # Otherwise, make a guess based on the company name
        return f"https://www.{company_name.lower().replace(' ', '')}.com"
    
    async def _get_detailed_competitor_info(self, company_name: str, website: str) -> Dict[str, Any]:
        """Get detailed information about a competitor"""
        # This would scrape the competitor's website and social profiles
        # For simplicity, we'll return placeholder data
        
        # In a real implementation, this would use Apify to scrape the website
        # and extract actual information
        
        return {
            "products": [f"{company_name} Product 1", f"{company_name} Product 2"],
            "marketing_channels": ["Social Media", "Content Marketing", "Email"],
            "key_messages": [f"{company_name} is a leader in innovation"],
            "strengths": ["Brand recognition", "Product quality"],
            "weaknesses": ["Higher price point", "Limited market reach"]
        }
    
    # Helper methods for keyword research
    def _generate_seed_keywords(self, product_name: str, industry: str, target_audience: str) -> List[str]:
        """Generate seed keywords based on product, industry, and audience"""
        keywords = []
        
        # Product-based keywords
        keywords.append(product_name)
        keywords.append(f"best {product_name}")
        keywords.append(f"{product_name} review")
        keywords.append(f"{product_name} price")
        
        # Industry-based keywords
        keywords.append(f"{industry} {product_name}")
        keywords.append(f"best {product_name} for {industry}")
        
        # Audience-based keywords
        if target_audience:
            keywords.append(f"{product_name} for {target_audience}")
            keywords.append(f"best {product_name} for {target_audience}")
        
        # Feature-based keywords (simplified)
        keywords.append(f"{product_name} features")
        keywords.append(f"{product_name} benefits")
        
        return list(set(keywords))
    
    def _extract_related_searches(self, search_results: List[Dict[str, Any]]) -> List[str]:
        """Extract related searches from search results"""
        # In a real implementation, this would extract the "People also ask" and 
        # "Related searches" sections from Google results
        
        # For simplicity, we'll return placeholder data
        if not search_results:
            return []
        
        # Extract some words from the results to create fake related searches
        words = []
        for result in search_results[:3]:
            title = result.get("title", "")
            for word in title.split():
                if len(word) > 4:
                    words.append(word)
        
        # Create some related searches
        related = []
        for word in words[:5]:
            related.append(f"how to use {word}")
            related.append(f"best {word}")
        
        return related[:5]  # Return up to 5 related searches
    
    def _estimate_search_volume(self, search_results: List[Dict[str, Any]]) -> int:
        """Estimate search volume based on search results"""
        # This is a placeholder - in a real implementation, this would use actual data
        import random
        return random.randint(500, 50000)
    
    def _estimate_competition_level(self, search_results: List[Dict[str, Any]]) -> str:
        """Estimate competition level based on search results"""
        # Count the number of ads and commercial results
        ad_count = 0
        commercial_count = 0
        
        for result in search_results:
            title = result.get("title", "").lower()
            url = result.get("url", "").lower()
            
            if "ad" in title or "sponsored" in title:
                ad_count += 1
            
            commercial_indicators = [".com", "shop", "buy", "price", "offer"]
            if any(indicator in url for indicator in commercial_indicators):
                commercial_count += 1
        
        # Determine competition level
        total_commercial = ad_count + commercial_count
        if total_commercial > len(search_results) * 0.7:
            return "high"
        elif total_commercial > len(search_results) * 0.4:
            return "medium"
        else:
            return "low"
    
    def _select_primary_keywords(self, keyword_data: List[Dict[str, Any]]) -> List[str]:
        """Select primary keywords based on volume and competition"""
        # Sort by estimated volume and filter by competition level
        sorted_keywords = sorted(keyword_data, key=lambda x: x["search_volume_estimate"], reverse=True)
        
        # Select keywords with high volume and low/medium competition
        primary_keywords = []
        for kw in sorted_keywords:
            if kw["competition_level"] != "high" and kw["search_volume_estimate"] > 1000:
                primary_keywords.append(kw["keyword"])
        
        # If we don't have enough, add some high-competition keywords
        if len(primary_keywords) < 3:
            for kw in sorted_keywords:
                if kw["keyword"] not in primary_keywords:
                    primary_keywords.append(kw["keyword"])
                    if len(primary_keywords) >= 3:
                        break
        
        return primary_keywords[:5]  # Return up to 5 primary keywords
    
    def _select_secondary_keywords(self, keyword_data: List[Dict[str, Any]]) -> List[str]:
        """Select secondary keywords based on related searches"""
        secondary_keywords = []
        
        # Collect all related searches
        for kw in keyword_data:
            secondary_keywords.extend(kw.get("related_searches", []))
        
        # Remove duplicates
        secondary_keywords = list(set(secondary_keywords))
        
        return secondary_keywords[:10]  # Return up to 10 secondary keywords
    
    # Helper methods for social media analysis
    def _analyze_social_media_data(self, platform_data: Dict[str, List[Dict[str, Any]]], product_name: str) -> Dict[str, Any]:
        """Analyze social media data for insights"""
        analysis = {
            "total_posts": 0,
            "sentiment": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            },
            "engagement": {
                "total": 0,
                "average": 0
            },
            "top_hashtags": [],
            "influencers": [],
            "peak_times": []
        }
        
        all_hashtags = []
        all_users = []
        post_times = []
        
        # Process data from each platform
        for platform, data in platform_data.items():
            analysis["total_posts"] += len(data)
            
            for post in data:
                # Analyze sentiment (simplified)
                sentiment = self._analyze_post_sentiment(post)
                analysis["sentiment"][sentiment] += 1
                
                # Track engagement
                engagement = self._calculate_post_engagement(post, platform)
                analysis["engagement"]["total"] += engagement
                
                # Extract hashtags
                hashtags = self._extract_hashtags(post)
                all_hashtags.extend(hashtags)
                
                # Track users
                user = self._extract_user_info(post, platform)
                if user:
                    all_users.append(user)
                
                # Track post times
                post_time = self._extract_post_time(post)
                if post_time:
                    post_times.append(post_time)
        
        # Calculate average engagement
        if analysis["total_posts"] > 0:
            analysis["engagement"]["average"] = analysis["engagement"]["total"] / analysis["total_posts"]
        
        # Find top hashtags
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        
        analysis["top_hashtags"] = sorted(
            hashtag_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Find influencers
        user_engagements = {}
        for user in all_users:
            user_id = user.get("id", "")
            engagement = user.get("engagement", 0)
            if user_id:
                user_engagements[user_id] = user_engagements.get(user_id, 0) + engagement
        
        analysis["influencers"] = sorted(
            [{"id": user_id, "engagement": engagement} for user_id, engagement in user_engagements.items()],
            key=lambda x: x["engagement"],
            reverse=True
        )[:5]
        
        # Find peak posting times
        if post_times:
            # Group by hour
            hour_counts = {}
            for dt in post_times:
                hour = dt.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            analysis["peak_times"] = sorted(
                hour_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        
        return analysis
    
    def _analyze_post_sentiment(self, post: Dict[str, Any]) -> str:
        """Analyze the sentiment of a social media post"""
        # This is a simplified implementation
        # In a real system, this would use NLP for sentiment analysis
        
        text = post.get("text", "") or post.get("caption", "") or ""
        
        positive_words = ["great", "good", "love", "amazing", "excellent", "best", "happy"]
        negative_words = ["bad", "hate", "terrible", "worst", "disappointed", "awful", "poor"]
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_post_engagement(self, post: Dict[str, Any], platform: str) -> int:
        """Calculate engagement for a social media post"""
        engagement = 0
        
        if platform == "twitter":
            engagement += post.get("likes", 0) or post.get("favorite_count", 0) or 0
            engagement += post.get("retweets", 0) or post.get("retweet_count", 0) or 0
            engagement += post.get("replies", 0) or post.get("reply_count", 0) or 0
        elif platform == "instagram":
            engagement += post.get("likes", 0) or 0
            engagement += post.get("comments", 0) or 0
        
        return engagement
    
    def _extract_hashtags(self, post: Dict[str, Any]) -> List[str]:
        """Extract hashtags from a social media post"""
        hashtags = []
        
        # Try to get hashtags from dedicated field
        if "hashtags" in post:
            if isinstance(post["hashtags"], list):
                hashtags.extend(post["hashtags"])
            elif isinstance(post["hashtags"], str):
                hashtags.append(post["hashtags"])
        
        # Extract from text
        text = post.get("text", "") or post.get("caption", "") or ""
        words = text.split()
        
        for word in words:
            if word.startswith("#"):
                hashtag = word[1:].lower()
                if hashtag and hashtag not in hashtags:
                    hashtags.append(hashtag)
        
        return hashtags
    
    def _extract_user_info(self, post: Dict[str, Any], platform: str) -> Optional[Dict[str, Any]]:
        """Extract user information from a social media post"""
        user_info = {}
        
        # Try to get user data
        user = post.get("user", {}) or {}
        
        user_info["id"] = user.get("id", "") or post.get("user_id", "")
        user_info["username"] = user.get("username", "") or user.get("screen_name", "")
        user_info["followers"] = user.get("followers", 0) or user.get("followers_count", 0) or 0
        
        # Calculate user engagement
        engagement = user_info["followers"]
        if platform == "twitter":
            engagement += user.get("friends", 0) or user.get("friends_count", 0) or 0
        
        user_info["engagement"] = engagement
        
        return user_info if user_info["id"] else None
    
    def _extract_post_time(self, post: Dict[str, Any]) -> Optional[datetime]:
        """Extract the posting time from a social media post"""
        timestamp = post.get("timestamp", None) or post.get("created_at", None)
        
        if not timestamp:
            return None
        
        try:
            if isinstance(timestamp, str):
                # Try different formats
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%a %b %d %H:%M:%S %z %Y"]:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
            elif isinstance(timestamp, int):
                # Assume Unix timestamp
                return datetime.fromtimestamp(timestamp)
        except Exception:
            pass
        
        return None
    
    def _extract_sample_posts(self, platform_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract sample posts from the collected data"""
        samples = []
        
        for platform, data in platform_data.items():
            # Sort by engagement
            sorted_posts = sorted(
                data,
                key=lambda post: self._calculate_post_engagement(post, platform),
                reverse=True
            )
            
            # Take top 2 posts from each platform
            for post in sorted_posts[:2]:
                sample = {
                    "platform": platform,
                    "text": post.get("text", "") or post.get("caption", "") or "",
                    "engagement": self._calculate_post_engagement(post, platform),
                    "url": post.get("url", "") or post.get("permalink", "") or "",
                    "timestamp": self._extract_post_time(post)
                }
                samples.append(sample)
        
        return samples
    
    # Helper methods for sentiment analysis
    def _extract_review_sentiment(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract sentiment from product reviews"""
        reviews = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for result in search_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            if "review" in title.lower() or "review" in snippet.lower():
                sentiment = self._analyze_text_sentiment(f"{title} {snippet}")
                sentiment_counts[sentiment] += 1
                
                reviews.append({
                    "text": snippet,
                    "source": result.get("url", ""),
                    "sentiment": sentiment
                })
        
        total = sum(sentiment_counts.values())
        sentiment_percentages = {
            k: (v / total * 100 if total > 0 else 0) 
            for k, v in sentiment_counts.items()
        }
        
        return {
            "reviews": reviews,
            "counts": sentiment_counts,
            "percentages": sentiment_percentages
        }
    
    def _extract_social_sentiment(self, social_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract sentiment from social media data"""
        posts = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for platform, data in social_data.items():
            for post in data:
                text = post.get("text", "") or post.get("caption", "") or ""
                sentiment = self._analyze_text_sentiment(text)
                sentiment_counts[sentiment] += 1
                
                posts.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "platform": platform,
                    "sentiment": sentiment,
                    "engagement": self._calculate_post_engagement(post, platform)
                })
        
        total = sum(sentiment_counts.values())
        sentiment_percentages = {
            k: (v / total * 100 if total > 0 else 0) 
            for k, v in sentiment_counts.items()
        }
        
        return {
            "posts": posts,
            "counts": sentiment_counts,
            "percentages": sentiment_percentages
        }
    
    def _extract_news_sentiment(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract sentiment from news articles"""
        articles = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for result in search_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            sentiment = self._analyze_text_sentiment(f"{title} {snippet}")
            sentiment_counts[sentiment] += 1
            
            articles.append({
                "title": title,
                "snippet": snippet,
                "source": result.get("url", ""),
                "sentiment": sentiment
            })
        
        total = sum(sentiment_counts.values())
        sentiment_percentages = {
            k: (v / total * 100 if total > 0 else 0) 
            for k, v in sentiment_counts.items()
        }
        
        return {
            "articles": articles,
            "counts": sentiment_counts,
            "percentages": sentiment_percentages
        }
    
    def _analyze_text_sentiment(self, text: str) -> str:
        """Analyze sentiment of a text"""
        # This is a simplified implementation
        # In a real system, this would use NLP for sentiment analysis
        
        positive_words = ["great", "good", "love", "amazing", "excellent", "best", "happy", "recommend"]
        negative_words = ["bad", "hate", "terrible", "worst", "disappointed", "awful", "poor", "avoid"]
        
        text = text.lower()
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_overall_sentiment(self, sentiment_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall sentiment across all sources"""
        total_counts = {"positive": 0, "neutral": 0, "negative": 0}
        
        for source, data in sentiment_data.items():
            counts = data.get("counts", {})
            for sentiment, count in counts.items():
                total_counts[sentiment] += count
        
        total = sum(total_counts.values())
        
        # Calculate percentages
        percentages = {
            k: (v / total * 100 if total > 0 else 0) 
            for k, v in total_counts.items()
        }
        
        # Determine overall sentiment
        max_sentiment = max(total_counts.items(), key=lambda x: x[1])[0] if total > 0 else "neutral"
        
        # Calculate sentiment score (-100 to 100)
        sentiment_score = 0
        if total > 0:
            sentiment_score = (total_counts["positive"] - total_counts["negative"]) / total * 100
        
        return {
            "dominant_sentiment": max_sentiment,
            "sentiment_score": sentiment_score,
            "counts": total_counts,
            "percentages": percentages
        }
    
    def _extract_key_points(self, sentiment_data: Dict[str, Dict[str, Any]], sentiment_type: str) -> List[str]:
        """Extract key positive or negative points from sentiment data"""
        key_points = []
        
        # Extract from reviews
        if "reviews" in sentiment_data:
            reviews = sentiment_data["reviews"].get("reviews", [])
            for review in reviews:
                if review.get("sentiment") == sentiment_type:
                    text = review.get("text", "")
                    if text:
                        key_points.append(text[:100] + "..." if len(text) > 100 else text)
        
        # Extract from social posts
        if "social" in sentiment_data:
            posts = sentiment_data["social"].get("posts", [])
            for post in posts:
                if post.get("sentiment") == sentiment_type:
                    text = post.get("text", "")
                    if text:
                        key_points.append(text[:100] + "..." if len(text) > 100 else text)
        
        # Extract from news
        if "news" in sentiment_data:
            articles = sentiment_data["news"].get("articles", [])
            for article in articles:
                if article.get("sentiment") == sentiment_type:
                    text = article.get("snippet", "")
                    if text:
                        key_points.append(text[:100] + "..." if len(text) > 100 else text)
        
        # Remove duplicates and limit to top 5
        unique_points = []
        for point in key_points:
            if point not in unique_points:
                unique_points.append(point)
                if len(unique_points) >= 5:
                    break
        
        return unique_points
