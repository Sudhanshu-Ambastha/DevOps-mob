# DevBridge

DevBridge is a crowdsourced, unified problem-solving platform connecting real-world user problems with developers. It features automated Software Requirement Specification (SRS) translation, tech stack recommendations, semantic duplicate detection, and valuation tracking powered by locally run Hugging Face NLP models.

---

## 🏗️ Repository Architecture & Multi-Branch Workflow

To keep our college project clean, avoid backend conflicts, and allow separate sub-teams to work simultaneously without merge hell, we use an isolated multi-branch architecture:

```text
DevBridge/
├── main         (Shared Core: Python FastAPI Backend + Hugging Face /ml/ pipeline)
├── web-dev      (Web Team: Frontend clients + shared /ml/)
└── mob-dev      (Mobile Team: Native Android Java clients + shared /ml/)

```

### **How the Shared AI Core Syncs**

The shared `ml/` folder on `main` houses our core NLP models and database microservices.

- **Automated Sync:** An automated GitHub Action workflow (`.github/workflows/sync-branches.yml`) running `scripts/sync.sh` synchronizes updates from the `ml/` folder on `main` into the feature branches.
- **Zero Overwrites:** This sync process **only** updates the `ml/` directory, ensuring frontend developers can build their web or mobile UIs without risking backend merge conflicts.

---

## 📂 Project Directory Structure

```text
DevBridge/
├── .github/
│   └── workflows/
│       └── sync-branches.yml   # Automated branch sync action
├── .gitignore
├── LICENSE
├── ml/
│   ├── .env                    # Environment variables (MongoDB URL, etc.)
│   ├── backend/                # Lightweight FastAPI REST API (Port 8000)
│   │   ├── config/             # Database connection handlers
│   │   ├── controllers/        # Express-style business logic handlers
│   │   ├── models/             # Pydantic validation schemas
│   │   ├── routes/             # API route endpoints
│   │   ├── services/           # AI service client (HTTP communication)
│   │   ├── main.py             # FastAPI backend entry point
│   │   └── requirements.txt    # Lightweight API dependencies (FastAPI, Motor, Pydantic)
│   ├── nlp/                    # Standalone AI/ML Worker (Port 8001)
│   │   ├── model.py            # Local Hugging Face inference pipeline
│   │   ├── main.py             # FastAPI NLP microservice entry point
│   │   └── requirements.txt    # Heavy ML dependencies (PyTorch, Transformers, Sentence-Transformers)
│   └── install.ps1             # Automated PowerShell environment setup script
├── README.md
└── scripts/
    └── sync.sh                 # Branch synchronization script

```

---

## ⚡ Core Features

1. **Unified Problem Submissions:** A streamlined form for users to raise real-world issues, categorize them, and optionally attach market valuation budgets.
2. **Semantic Duplicate Detection:** Uses `sentence-transformers/all-MiniLM-L6-v2` locally to compute cosine similarity between problem descriptions, automatically flagging duplicates and incrementing upvotes on existing issues.
3. **Automated SRS & Tech Stack Translation:** Uses compact instruction models (`Qwen/Qwen2.5-3B-Instruct`) to convert raw user complaints into structured Markdown SRS documents containing Objectives, Functional Requirements, Scope, and Recommended Tech Stacks.
4. **Decoupled Local Microservices:** Separates heavy AI model inference (running offline on port 8001) from the lightweight database-driven backend API (running on port 8000) to ensure high performance and zero external API costs.

---

## 🚀 Getting Started Locally

### **1. Clone and Setup Environment**

Open PowerShell inside your project folder and run your install script to configure your virtual environments and dependencies:

```powershell
cd ml
.\install.ps1
```

### **2. Run the Local Services (Two Terminals)**

- **Terminal 1: Start the Standalone NLP Worker (Port 8001)**

```powershell
cd ml/nlp
python -m uvicorn main:app --reload --port 8001
```

- **Terminal 2: Start the Lightweight Backend API (Port 8000)**

```powershell
cd ml/backend
uvicorn main:app --reload --port 8000
```

### **3. Test the API**

Open your browser and navigate to **`http://localhost:8000/docs`** to test your live interactive Swagger documentation and post problem statements.
