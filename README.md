# DevBridge

DevBridge is a crowdsourced, unified problem-solving platform connecting real-world user problems with developers, featuring automated Software Requirement Specification (SRS) translation and semantic duplicate detection using Hugging Face NLP models.

## Repository Architecture & Multi-Branch Workflow

To keep our college project clean, avoid backend conflicts, and allow separate sub-teams to work simultaneously without merge hell, we use an isolated multi-branch architecture:

```
DevBridge/
├── main          (Shared Core: Python + Hugging Face /ml/ pipeline)
├── web-dev       (Web Team: Express + React + Vite + shared /ml/)
└── mob-dev       (Mobile Team: Native Android Java/XML + shared /ml/)
```

## How the Shared AI Core Syncs

The shared `ml/` folder on `main` contains our core NLP models (for semantic duplicate detection and text-to-SRS translation).

- **Automated Sync:** An automated GitHub Action script (`scripts/sync.sh`) runs daily (or can be triggered manually in the Actions tab) to copy the latest updates from the `ml/` folder on `main` directly into `web-dev` and `mob-dev`.
- **Zero Overwrites:** This sync process **only** updates the `ml/` directory. It never touches or overrides the web or mobile frontend code, ensuring team members can work safely on their respective platforms.

---
