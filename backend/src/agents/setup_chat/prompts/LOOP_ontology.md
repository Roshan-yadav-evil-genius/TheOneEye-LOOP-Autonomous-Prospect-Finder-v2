# LOOP Product Ontology & Operational Flow

**Product Name:** LOOP  
**Kind:** AI-Powered Sales Lead Generation Service  

---

## 1. Executive Summary

LOOP is an AI-powered sales lead generation service that automates B2B prospect discovery. Instead of sales teams spending hours manually researching target companies and decision-makers, sales operators define their organization, register their product offerings, and set up targeted prospecting strategies. LOOP's autonomous AI agents then conduct the research on the web, registering qualified companies and finding relevant decision-makers to maintain a continuous sales pipeline.

---

## 2. Platform Setup & Domain Hierarchy Flow

The onboarding and strategy setup follows a structured, guided sequence. At each stage, dedicated AI Setup Assistants guide the human sales operator through natural conversation to fill and validate profile forms step-by-step:

```mermaid
graph TD
    classDef seller fill:#0f172a,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef product fill:#0f172a,stroke:#8b5cf6,stroke-width:2px,color:#fff
    classDef strategy fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#fff
    classDef agent fill:#0f172a,stroke:#ec4899,stroke-width:2px,color:#fff
    classDef target fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#fff
    classDef prospect fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#fff
    classDef rule fill:#0f172a,stroke:#ef4444,stroke-width:2px,color:#fff

    subgraph Phase1 ["Step 1: Organization Setup"]
        Op1["Sales Operator"]:::seller -->|"Guided Chat"| OrgAssistant["Organization Setup Assistant"]:::agent
        OrgAssistant -->|"Fills & Validates"| OrgProfile["Organization Profile<br/>• Company overview & mission<br/>• Primary industry & business model<br/>• Customer segments & deal constraints"]:::seller
    end

    subgraph Phase2 ["Step 2: Product / Service Registration"]
        OrgProfile -->|"Owns Offerings"| ProdProfile["Product / Service Profile<br/>• Value proposition & problem solved<br/>• Ideal Customer Profile (ICP)<br/>• Buyer personas & pricing model"]:::product
        Op1 -->|"Guided Chat"| ProdAssistant["Product Setup Assistant"]:::agent
        ProdAssistant -->|"Fills & Validates"| ProdProfile
    end

    subgraph Phase3 ["Step 3: Sales Strategy Configuration"]
        ProdProfile -->|"Executes Runs"| StratProfile["Sales Strategy Run<br/>• Target company criteria & industries<br/>• Target decision-maker roles<br/>• Company & contact quotas"]:::strategy
        Op1 -->|"Guided Chat"| StratAssistant["Strategy Setup Assistant"]:::agent
        StratAssistant -->|"Fills & Validates"| StratProfile
    end

    subgraph Phase4 ["Step 4: Autonomous Research & Lead Generation"]
        StratProfile -->|"Triggers Execution"| Agents["Autonomous AI Agents<br/>• Company Finder Agent<br/>• Contact Finder Agent"]:::agent
        Agents -->|"Browses Web & Identifies"| Companies["Qualified Target Companies"]:::target
        Agents -->|"Finds Decision-Makers"| Contacts["Relevant Contacts & Decision-Makers"]:::prospect
    end

    subgraph Phase5 ["Step 5: Pipeline & Continuous Replenishment"]
        Contacts -->|"Delivered To"| SalesTeam["Sales Team"]:::seller
        SalesTeam -->|"Marks Unresponsive / Irrelevant"| Blacklist["Blacklist Contact"]:::rule
        Blacklist -->|"Auto-Resumes Research"| Agents
    end
```

---
