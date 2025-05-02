# Catalyst Marketing Platform Documentation

## Introduction

Catalyst is an AI-powered multi-agent marketing platform designed to help Small and Medium Businesses (SMBs) scale their presales efforts through automated content creation, market research, campaign planning, and outreach. The platform leverages multiple autonomous AI agents connected through a Model Context Protocol (MCP) to create end-to-end marketing workflows with minimal human intervention.

## System Architecture

### Overview

Catalyst employs a distributed multi-agent architecture where each agent specializes in a specific marketing function. These agents communicate asynchronously through a standardized protocol, allowing for flexible workflows and parallel processing. The system consists of:

1. **Frontend Layer**: React + TypeScript application with Mantine UI components
2. **Backend Layer**: Python FastAPI server handling API requests and agent coordination
3. **Agent Layer**: Autonomous AI agents for specialized marketing tasks
4. **Integration Layer**: Connections to third-party services (Apify, DeepL, Vizcom, etc.)
5. **Storage Layer**: Database for storing campaigns, content, and agent state

![System Architecture Diagram](https://example.com/architecture.png)

### Model Context Protocol (MCP)

The Model Context Protocol is the backbone of Catalyst, enabling standardized communication between agents. Key components include:

- **MCPBus**: Central message bus for routing messages between agents
- **MCPRegistry**: Registry for tracking agents, tasks, and their statuses
- **MCPMessage**: Standardized message format for agent communication
- **TaskRequest/TaskResponse**: Structured formats for task delegation and results

The MCP enables:
- Asynchronous communication between agents
- Task delegation and status tracking
- Error handling and recovery
- Workflow orchestration

### Agent Definitions

Catalyst implements 8 specialized agents:

1. **Market Research Agent**: Gathers market intelligence, trends, and competitor information using Apify web scraping capabilities.
   - Analyzes trends
   - Researches competitors
   - Performs keyword research
   - Analyzes social media and market sentiment

2. **ICP Discovery Agent**: Identifies ideal customer profiles and target demographics based on market research.
   - Segments audiences
   - Creates customer personas
   - Identifies target demographics

3. **Campaign Planning Agent**: Creates strategic campaign plans based on research and ICP.
   - Develops campaign strategies
   - Sets campaign goals and KPIs
   - Creates content calendars

4. **Content Generation Agent**: Creates marketing content using Vizcom's AI rendering capabilities.
   - Generates text content (social posts, emails, ad copy)
   - Creates visual content from sketches or text prompts
   - Combines text and visual elements for complete marketing assets

5. **Localization Agent**: Translates and localizes content using DeepL's translation capabilities.
   - Translates text content to multiple languages
   - Preserves formatting and context
   - Handles campaign-wide localization

6. **Scheduler/Posting Agent**: Manages timing and posting of content.
   - Schedules content for optimal times
   - Manages posting to different platforms
   - Tracks publishing status

7. **Outreach Agent**: Handles direct customer communication.
   - Manages email campaigns
   - Coordinates event invitations via Luma
   - Personalizes outreach messages

8. **Master MCP Controller**: Orchestrates the overall workflow and manages user interactions.
   - Coordinates agent activities
   - Handles user input and feedback
   - Manages approval workflows

## Agent Interactions

### Communication Flow

Agents communicate through the MCP using standardized message types:

1. **TASK_REQUEST**: Request for an agent to perform a specific task
2. **TASK_RESPONSE**: Response containing task results or error information
3. **STATUS_UPDATE**: Updates on agent status and progress
4. **ERROR**: Error notifications
5. **LOG**: Logging information
6. **COMMAND**: Commands to control agent behavior
7. **QUERY**: Requests for information
8. **NOTIFICATION**: General notifications

### Task Processing Workflow

A typical task processing workflow follows these steps:

1. User initiates a request through the frontend
2. The Master Controller receives the request and creates appropriate task requests
3. Task requests are sent to specialized agents via the MCP Bus
4. Agents process tasks asynchronously and return results
5. Results are aggregated by the Master Controller
6. Processed results are presented to the user for approval
7. Upon approval, subsequent actions are triggered (e.g., scheduling, localization)

Example workflow for content creation:
```
User → Master Controller → Content Generation Agent → Localization Agent → Scheduler Agent → Publication
```

## Integration with Sponsor Tools

### Apify for Market Research

The Market Research Agent integrates with Apify to gather market intelligence:

- **Web Scraping**: Extracts data from websites to analyze competitors and market trends
- **Google Search**: Uses Apify's Google Search Results Scraper to gather information on keywords and trends
- **Social Media Analysis**: Collects data from social platforms to understand audience sentiment and engagement

Implementation highlights:
- Asynchronous API calls to Apify actors
- Structured data extraction and processing
- Intelligent analysis of scraped content

### Vizcom for Visual Content

The Content Generation Agent leverages Vizcom's AI rendering capabilities:

- **Sketch-to-Image**: Transforms hand-drawn sketches into professional renderings
- **Text-to-Image**: Generates visual content from text descriptions
- **Image Enhancement**: Improves existing images
- **Variation Generation**: Creates multiple versions of visual content

Implementation highlights:
- Integration with Vizcom's API for image generation
- Support for different visual styles and aspect ratios
- Combination of text and visual elements for complete marketing assets

### DeepL for Localization

The Localization Agent uses DeepL's translation services:

- **Text Translation**: Translates marketing copy while preserving tone and context
- **Content Structure Preservation**: Maintains formatting and structure during translation
- **Language Detection**: Automatically identifies source language
- **Campaign-wide Localization**: Translates entire campaigns to multiple languages

Implementation highlights:
- Recursive traversal of content structures to identify translatable text
- Preservation of formatting and variables
- Support for multiple target languages

## Implementation Details

### Backend (FastAPI)

The backend is implemented using Python FastAPI, providing:

- RESTful API endpoints for frontend communication
- Asynchronous processing for improved performance
- Structured data validation with Pydantic models
- Background task processing for long-running operations

Key components:
- **API Router**: Handles HTTP requests and responses
- **Agent Manager**: Initializes and manages agent instances
- **MCP Implementation**: Provides communication infrastructure
- **Service Integrations**: Connects to external services

### Frontend (React + TypeScript)

The frontend is built with React and TypeScript, featuring:

- **Mantine UI Components**: For a polished, responsive interface
- **React Router**: For navigation between different sections
- **Form Handling**: For user input with validation
- **State Management**: For managing application state

Key components:
- **Dashboard**: Overview of campaigns, content, and agent activity
- **Content Creator**: Interface for generating new marketing content
- **Campaign Manager**: Tools for planning and managing campaigns
- **Agent Monitor**: Visibility into agent status and activities

## Example Use Case: Fitness Tracker Marketing Campaign

### Scenario

A company is launching a new fitness tracker and needs to create a marketing campaign targeting fitness enthusiasts aged 25-45.

### Workflow

1. **Market Research**:
   - The Market Research Agent scrapes competitor websites and social media
   - It identifies trending fitness topics and keywords
   - It analyzes market sentiment around fitness trackers

2. **ICP Discovery**:
   - The ICP Discovery Agent identifies key demographics and personas
   - It determines that "health-conscious professionals" are the primary target

3. **Campaign Planning**:
   - The Campaign Planning Agent creates a strategy focusing on convenience and health benefits
   - It suggests a mix of social media, email, and content marketing

4. **Content Generation**:
   - The Content Generation Agent creates social media posts highlighting key features
   - It generates product images showing the fitness tracker in use
   - It creates email templates for the product launch

5. **Localization**:
   - The Localization Agent translates content to Spanish and French
   - It ensures fitness terminology is appropriately localized

6. **Scheduling**:
   - The Scheduler Agent determines optimal posting times
   - It creates a content calendar for the campaign duration

7. **Outreach**:
   - The Outreach Agent prepares personalized emails to fitness influencers
   - It schedules demo events through Luma

### User Interaction

Throughout this process, the user:
1. Provides initial product information
2. Reviews and approves generated content
3. Makes adjustments to the campaign strategy as needed
4. Monitors performance through the dashboard

## Hackathon Requirements Fulfillment

### Building AI Agents that Plan, Decide, and Act

Catalyst implements autonomous agents that:

- **Plan**: The Campaign Planning Agent develops strategic marketing plans based on research
- **Decide**: Agents make decisions about content, timing, and targeting based on data
- **Act**: Agents execute tasks like content generation, translation, and scheduling

### Using MCP to Chain Sponsor Tools

The Model Context Protocol enables:

- Standardized communication between agents
- Seamless integration of sponsor tools (Apify, Vizcom, DeepL)
- Structured task delegation and result handling
- Error recovery and workflow management

### Autonomous End-to-End Workflow

Catalyst provides complete automation of the marketing workflow:

- From initial market research to content publication
- With human oversight at key approval points
- Across multiple marketing channels and languages

### Agent Interaction and Collaboration

Agents collaborate through:

- Task delegation (e.g., Content Generation → Localization)
- Shared context (e.g., Market Research informing Campaign Planning)
- Sequential and parallel processing
- Coordinated by the Master Controller

### Sponsor Tool Integration

Catalyst integrates multiple sponsor tools:

1. **Apify**: For web scraping and market research
2. **Vizcom**: For AI-powered visual content generation
3. **DeepL**: For high-quality content translation
4. **Luma**: For event management and scheduling

## Conclusion

The Catalyst Marketing Platform demonstrates the power of multi-agent AI systems for marketing automation. By connecting specialized agents through a standardized protocol and integrating powerful third-party tools, Catalyst enables SMBs to create sophisticated marketing campaigns with minimal manual effort.

The platform showcases how AI agents can plan, decide, and act autonomously while still providing users with control and oversight at critical points. The integration of market research, content generation, localization, and scheduling creates a comprehensive end-to-end solution for modern marketing needs.

---

## Technical Appendix

### Running the Application

#### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export APIFY_API_KEY=your_apify_api_key
export DEEPL_API_KEY=your_deepl_api_key
export VIZCOM_API_KEY=your_vizcom_api_key

# Run the FastAPI server
uvicorn backend.main:app --reload
```

#### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Run the development server
npm start
```

### API Documentation

API documentation is available at `/docs` when running the FastAPI server.
