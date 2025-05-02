flowchart TD
    %% Main User Interface
    UI[Dashboard UI] --> MCP
    
    %% Model Context Protocol (MCP) Controller
    MCP[Master MCP Controller] --> MRA
    MCP --> ICPA
    MCP --> CPA
    MCP --> CGA
    MCP --> LA
    MCP --> SPA
    MCP --> OA
    MCP --> DB[(Database)]
    
    %% Individual Agents
    MRA[Market Research Agent] --> Apify
    MRA --> MCP
    
    ICPA[ICP Discovery Agent] --> DB
    ICPA --> MCP
    
    CPA[Campaign Planning Agent] --> DB
    CPA --> MCP
    
    CGA[Content Generation Agent] --> Vizcom
    CGA --> MCP
    
    LA[Localization Agent] --> DeepL
    LA --> MCP
    
    SPA[Scheduler/Posting Agent] --> Calendar
    SPA --> MCP
    
    OA[Outreach Agent] --> Email
    OA --> Luma
    OA --> MCP
    
    %% External Services
    Apify[Apify<br>• Web Scraping<br>• Data Collection]
    DeepL[DeepL<br>• Translation<br>• Localization]
    Vizcom[Vizcom<br>• Ad Rendering<br>• Visual Content]
    Luma[Luma<br>• Event Management]
    Calendar[Calendar APIs<br>• Scheduling]
    Email[Email APIs<br>• Outreach]
    
    %% User Workflow
    User((User)) --> UI
    UI --> User
    
    %% Data Flow for Example Use Case
    User -->|1. Enter Product<br>Description| UI
    MRA -->|2. Find Market<br>Trends| MCP
    ICPA -->|3. Identify Target<br>Audience| MCP
    CPA -->|4. Create Campaign<br>Strategy| MCP
    CGA -->|5. Generate<br>Content| MCP
    LA -->|6. Localize<br>Content| MCP
    SPA -->|7. Schedule<br>Posts| MCP
    OA -->|8. Initiate<br>Outreach| MCP
    MCP -->|9. Present Results<br>for Approval| UI
    
    %% Styling
    classDef agent fill:#4672b4,color:white,stroke:#333,stroke-width:1px
    classDef controller fill:#8b251e,color:white,stroke:#333,stroke-width:1px
    classDef service fill:#47956f,color:white,stroke:#333,stroke-width:1px
    classDef interface fill:#de953e,color:white,stroke:#333,stroke-width:1px
    classDef storage fill:#666666,color:white,stroke:#333,stroke-width:1px
    classDef userNode fill:#333333,color:white,stroke:#333,stroke-width:1px
    
    class MRA,ICPA,CPA,CGA,LA,SPA,OA agent
    class MCP controller
    class Apify,DeepL,Vizcom,Luma,Calendar,Email service
    class UI interface
    class DB storage
    class User userNode
