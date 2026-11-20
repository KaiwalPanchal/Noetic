# Hats, Haircuts, and Tattoos: The Taxonomy of Technical Decision Reversibility

By The Decision Mechanics Collective (2022)

## 1. The Three Reversibility Classes

Engineers frequently make two equal and opposite mistakes: they agonize for weeks over trivia that could be reversed in ten seconds, and they carelessly greenlight architectural decisions over lunch that will trap the company for the next decade. To align deliberation effort with actual risk, every engineering decision must be categorized into one of three distinct reversibility tiers:

### Class 1: Hats (Reversible in Minutes or Hours)
A **Hat** is a choice that can be tried on, swapped, or removed with virtually zero residual friction or blast radius. If you put on a hat and dislike how it looks, you take it off.
- Examples: Renaming a local variable or private method; adjusting internal indentation formatting; tuning an internal loop benchmark; trying out a developer CLI tool.
- Deliberation Rule: Zero committee review. Implement immediately; reverse immediately if suboptimal.

### Class 2: Haircuts (Reversible in Days or Weeks)
A **Haircut** is a decision that requires noticeable effort and patience to undo, but will naturally grow back without permanently altering the underlying organism. It carries moderate switching cost, but does not present existential lock-in.
- Examples: Choosing a CSS utility library (e.g. Tailwind vs Sass); selecting a primary key representation strategy (UUIDv7 vs bigint) within an unreleased schema; swapping a lightweight cache adapter; structuring directory layouts in a monorepo.
- Deliberation Rule: Brief peer discussion or RFC review (under 48 hours). Validate against foreseeable 6-month needs, then proceed.

### Class 3: Tattoos (Permanent or Multi-Year Irreversible)
A **Tattoo** is permanent ink injected deep into the epidermis. Once applied, removing it requires excruciating, agonizing laser surgery that leaves permanent scar tissue.
- Examples: Choosing an open-source software license (e.g. GPL vs Apache 2.0 vs MIT); defining public API endpoint names and wire field contracts consumed by external SDK clients; selecting the primary database engine for a core transactional system; choosing the messaging substrate for distributed inter-service communication; one-way schema migrations that drop legacy columns without dual-write phases.
- Deliberation Rule: Mandatory formal RFC and ADR review. Rigorous adversarial sparring, multi-stakeholder approval, and proof of migration paths before commitment.

## 2. Directional Heuristics

- **When classifying engineering decisions** → Prioritize **Rigorous deliberation on Tattoos** over _Uniform committee review across all tasks_ because trivial decisions squander organizational momentum while unexamined tattoos inflict multi-year lock-in. (Rule: `Classify every RFC proposal as Hat, Haircut, or Tattoo before debating implementation`) [Tier 2] [Tags: governance, decision-making]
- **The Core Question / Razor:** "How much pain and calendar time does it take to undo this if we are 100% wrong?"
