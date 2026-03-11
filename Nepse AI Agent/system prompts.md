graph TB
    %% Data Sources
    A1[Real-time Market Data]
    A2[Historical Data]
    A3[News & Research]
    A4[Market Depth]
    A5[Sector Data]

    %% Autonomous Agent
    subgraph AutonomousAgent[Autonomous Agent]
        B1[System Prompt: NEPSE Market Analyst]
        B2[Analysis Components]
        B3[Output Components]
    end

    %% Trading Signal Agent
    subgraph TradingAgent[Trading Signal Agent]
        C1[System Prompt: Trading Signal Generator]
        C2[Analysis Components]
        C3[Output Components]
    end

    %% Research Agent
    subgraph ResearchAgent[Research Agent]
        D1[System Prompt: Market Researcher]
        D2[Analysis Components]
        D3[Output Components]
    end

    %% Market Analysis Agent
    subgraph MarketAgent[Market Analysis Agent]
        E1[System Prompt: Market Behavior Analyst]
        E2[Analysis Components]
        E3[Output Components]
    end

    %% Data Storage
    subgraph Storage[Data Storage]
        F1[Redis Cache]
        F2[PostgreSQL DB]
    end

    %% API Layer
    subgraph API[API Layer]
        G1[FastAPI Server]
        G2[WebSocket Server]
    end

    %% Data Flow
    A1 --> B1
    A1 --> C1
    A1 --> D1
    A1 --> E1
    
    A2 --> B1
    A2 --> C1
    A2 --> E1
    
    A3 --> D1
    A3 --> B1
    
    A4 --> E1
    A4 --> C1
    
    A5 --> E1
    A5 --> B1

    %% Agent Analysis Flow
    B1 --> B2
    B2 --> B3
    B3 --> F1
    B3 --> F2
    
    C1 --> C2
    C2 --> C3
    C3 --> F1
    C3 --> F2
    
    D1 --> D2
    D2 --> D3
    D3 --> F1
    D3 --> F2
    
    E1 --> E2
    E2 --> E3
    E3 --> F1
    E3 --> F2

    %% API Flow
    F1 --> G1
    F1 --> G2
    F2 --> G1
    F2 --> G2




---------
2) Trading signal agent prompt

graph TB
    %% Autonomous Agent Analysis
    subgraph AutonomousAnalysis[Autonomous Agent Analysis]
        B2.1[Technical Analysis]
        B2.2[Fundamental Analysis]
        B2.3[Market Behavior]
        B2.4[Pattern Recognition]
    end

    %% Trading Signal Analysis
    subgraph TradingAnalysis[Trading Signal Analysis]
        C2.1[Price Analysis]
        C2.2[Volume Analysis]
        C2.3[Pattern Analysis]
        C2.4[Risk Analysis]
    end

    %% Research Analysis
    subgraph ResearchAnalysis[Research Analysis]
        D2.1[News Analysis]
        D2.2[Sentiment Analysis]
        D2.3[Fact Checking]
        D2.4[Market Correlation]
    end

    %% Market Analysis
    subgraph MarketAnalysis[Market Analysis]
        E2.1[Market Trends]
        E2.2[Sector Analysis]
        E2.3[Depth Analysis]
        E2.4[Pattern Analysis]
    end

4) Market Analysis Agent Prompt
You are a comprehensive NEPSE market analyst. Your responsibilities include:
- Analyze all stocks in real-time
- Consider T+3 settlement
- Account for liquidity constraints
- Monitor market timing
- Generate detailed trading signals
- Provide entry/exit points
- Assess risks
- Include market context
- Generate daily reports
- Monitor market behavior