# Twitter Build-in-Public Project Pack

**Block:** PROJECTS  
**Role:** Audience & Authority Engine (Linked to Goal G7 & Competency C2)

This project pack runs on top of the OverMind core harness. It turns thinking frameworks and curated signals into high-density Twitter/X threads and build-in-public logs.

## Structure
- `commands/`: Claude Code slash commands (`/draft`, `/ship`, `/journey`)
- `prompts/`: Agent prompt templates (`draft.md`, `journey.md`)
- `schemas/`: Output schemas (`thread.json`, `journey.json`)
- `pipelines/`: Pipeline definitions (`draft.py`, `journey.py`)
- `tools/`: Domain tools (`tweets.py` - weighted character counter)
- `scripts/`: Local validators (`thread_validator.py`)
- `seed/`: Vault seeds (`posted.md`, `README.md`)

## Principles
1. **Manual Posting Only:** The agent drafts; the human reviews and posts by hand.
2. **Strict Character Checking:** Twitter weights URLs as 23 characters and emoji as 2.
3. **Decoupled from Core Harness:** The core OverMind engine remains pure; Twitter is an applied project.
