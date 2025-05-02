# Catalyst

Catalyst is an AI-powered multi-agent marketing platform designed to help Small and Medium Businesses (SMBs) scale their presales efforts through automated content creation, market research, campaign planning, and outreach.

![Catalyst Platform](https://placehold.co/600x300/4672b4/white?text=Catalyst+Marketing+Platform)

## Features

- **Market Research**: Automatically gather market intelligence, trends, and competitor information
- **Content Generation**: Create text and visual content for multiple marketing channels
- **Localization**: Translate content to multiple languages with context preservation
- **Campaign Planning**: Develop data-driven marketing strategies
- **Scheduling & Outreach**: Automate content publishing and customer communication

## System Requirements

- **Backend**:
  - Python 3.8+
  - FastAPI
  - Uvicorn
  - Asyncio
  - Httpx
  - Pydantic
- **Frontend**:
  - Node.js 14+
  - React 17+
  - TypeScript
  - Mantine UI
  - React Router

## Setup Instructions

### API Keys

Before setting up the application, you'll need to obtain API keys for the following services:

1. **Apify API Key** (for market research)

   - Sign up at [Apify](https://apify.com/)
   - Navigate to Account Settings > Integrations
   - Create a new API key

2. **DeepL API Key** (for translation)

   - Sign up at [DeepL API](https://www.deepl.com/pro-api)
   - Choose a plan (Free tier available)
   - Copy your API key from the account dashboard

3. **Vizcom API Key** (for visual content generation)
   - Sign up at [Vizcom AI](https://www.vizcom.ai/)
   - Request API access
   - Copy your API key from the developer dashboard

### Backend Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/catalyst-platform.git
   cd catalyst-platform
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables:

   ```bash
   # Linux/macOS
   export APIFY_API_KEY=your_apify_api_key
   export DEEPL_API_KEY=your_deepl_api_key
   export VIZCOM_API_KEY=your_vizcom_api_key

   # Windows
   set APIFY_API_KEY=your_apify_api_key
   set DEEPL_API_KEY=your_deepl_api_key
   set VIZCOM_API_KEY=your_vizcom_api_key
   ```

   Alternatively, create a `.env` file in the root directory:

   ```
   APIFY_API_KEY=your_apify_api_key
   DEEPL_API_KEY=your_deepl_api_key
   VIZCOM_API_KEY=your_vizcom_api_key
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file with the backend API URL:

   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

4. Start the development server:

   ```bash
   npm start
   ```

5. The application should now be running at `http://localhost:3000`

## Usage Guide

### Login

- Use the default credentials:
  - Username: `admin`
  - Password: `password`

### Dashboard

The dashboard provides an overview of:

- Active campaigns
- Pending and completed content
- Agent status
- Recent activity

### Creating Content

1. Click "Create Content" on the dashboard or navigate to Content > New Content
2. Fill in the content details:
   - Select content type (social post, email, ad, etc.)
   - Enter title and description
   - Provide product information
3. Set content parameters:
   - Text options (tone, template, keywords)
   - Visual options (style, aspect ratio, colors)
   - Localization settings (target languages)
4. Generate the content
5. Review and approve the generated content

### Managing Campaigns

1. Navigate to Campaigns > New Campaign
2. Define campaign details:
   - Name and description
   - Target audience
   - Start and end dates
   - Goals and budget
3. The system will automatically:
   - Research market trends
   - Identify target demographics
   - Suggest content strategy
   - Generate initial content
4. Review and approve the campaign plan
5. Monitor campaign progress on the dashboard

## Project Structure

```
catalyst-platform/
├── backend/
│   ├── agents/
│   │   ├── market_research_agent.py
│   │   ├── content_generation_agent.py
│   │   ├── localization_agent.py
│   │   └── ...
│   ├── protocols/
│   │   └── mcp.py
│   └── main.py
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── Dashboard.tsx
│       │   ├── ContentCreator.tsx
│       │   └── ...
│       └── App.tsx
├── requirements.txt
└── README.md
```

## Troubleshooting

### API Connection Issues

- Verify that your API keys are correctly set in environment variables
- Check that the backend server is running and accessible
- Ensure your firewall isn't blocking connections

### Agent Failures

- Check the logs for specific error messages
- Verify that the required API services (Apify, DeepL, Vizcom) are operational
- Restart the backend server to reinitialize agents

### Content Generation Problems

- Ensure you've provided sufficient product information
- Try different parameters (tone, style, etc.)
- For visual content issues, check that image URLs or sketches are valid

## License

MIT

## Acknowledgments

This project was created for the AI Agent Hackathon and utilizes the following sponsor tools:

- [Apify](https://apify.com/) - Web scraping and automation
- [DeepL](https://www.deepl.com/) - AI translation
- [Vizcom](https://www.vizcom.ai/) - AI image generation

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com)
