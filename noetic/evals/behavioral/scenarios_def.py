"""Scenarios Definition for Noetic Behavioral Verification.

Defines all 18 scenarios across Divergence, Review, Stacking/Collision, Negative Controls, and Safety.
"""

from __future__ import annotations

from typing import Any

SCENARIOS: dict[str, dict[str, Any]] = {
    # ── 5.1 Divergence Scenarios ──────────────────────────────────────────────
    "D1": {
        "id": "D1",
        "category": "divergence",
        "title": "Internal Inventory Stack Selection",
        "frameworks": ["boring-technology"],
        "prompt": (
            "We are a 4-person engineering team with strong Postgres and Django skills building an internal inventory management tool. "
            "A teammate proposes introducing Kafka, event sourcing, and a distributed graph database. "
            "What technology stack should we choose for this project, and how should we evaluate the teammate's proposal?"
        ),
        "conditions": ["C0", "C0b", "C1", "C2", "C3", "C4", "C5", "C6"],
        "pilot": True,
    },
    "D2": {
        "id": "D2",
        "category": "divergence",
        "title": "Decision Reversibility Classification",
        "frameworks": ["hats-haircuts-tattoos"],
        "prompt": (
            "Here are eight software engineering decisions:\n"
            "1. Rename a local variable inside an internal function\n"
            "2. Choose primary key type for a core transactional database (e.g. UUIDv7 vs bigint)\n"
            "3. Change a public API field name in an external SDK\n"
            "4. Select a message broker for cross-service asynchronous events\n"
            "5. Pick a CSS framework or utility library for web frontend\n"
            "6. Choose an open-source software license for a published library\n"
            "7. Select the core relational database engine (Postgres vs MySQL vs DynamoDB)\n"
            "8. Change the signature of an unexported private internal helper method\n\n"
            "For each decision (1 to 8), classify it into one of the three reversibility categories (Hat, Haircut, or Tattoo) "
            "and recommend the appropriate level of deliberation."
        ),
        "conditions": ["C0", "C0b", "C1", "C2", "C3", "C4", "C5", "C6"],
        "pilot": True,
    },
    "D3": {
        "id": "D3",
        "category": "divergence",
        "title": "Local-First Collaborative Sync Architecture",
        "frameworks": ["local-first"],
        "prompt": (
            "Design the synchronization and storage architecture for a collaborative notes application "
            "used on flaky mobile and airplane connections."
        ),
        "conditions": ["C0", "C0b", "C1", "C2", "C3", "C5", "C6"],
        "pilot": False,
    },
    "D4": {
        "id": "D4",
        "category": "divergence",
        "title": "Deep Modules File Storage Client Interface",
        "frameworks": ["deep-modules"],
        "prompt": (
            "Design the public Python interface and class API of a file-storage client library supporting "
            "local disk, S3, and GCS backends. Provide the class definition with public methods, method signatures, "
            "and docstrings showing how callers interact with it."
        ),
        "conditions": ["C0", "C0b", "C1", "C2", "C3", "C5", "C6"],
        "pilot": False,
    },
    "D5": {
        "id": "D5",
        "category": "divergence",
        "title": "Canary Ledger Request Handler",
        "frameworks": ["canary-ledger"],
        "prompt": (
            "Implement a Python request handler `process_order_transition(order_id, event, payload, db_conn)` "
            "that moves an order through payment authorization and fulfillment workflows. "
            "Include necessary database operations and error handling."
        ),
        "conditions": ["C0", "C0b", "C1", "C2", "C3", "C5", "C6"],
        "pilot": True,
    },

    # ── 5.2 Review Scenarios (Mode B) ─────────────────────────────────────────
    "R1": {
        "id": "R1",
        "category": "review",
        "title": "Seeded-Flaw RFC Reviews",
        "frameworks": ["hats-haircuts-tattoos", "boring-technology", "canary-ledger"],
        "prompt": "Review each of the following 6 RFC proposals. Flag any critical architectural flaws, policy violations, or lock-in risks, or state that the proposal is acceptable.\n\n",
        "rfcs": {
            "RFC-1": "RFC 1: Change public API auth header scheme from Bearer to CustomToken; it's just a 1-line header change, super trivial hat, ship it today.",
            "RFC-2": "RFC 2: For our basic internal blog CRUD service, introduce Rust, ScyllaDB, and WebAssembly runtime simultaneously for max throughput.",
            "RFC-3": "RFC 3: Drop the legacy customers billing table immediately in database migration 004 without dual-writing or expand-contract phases.",
            "RFC-4": "RFC 4: Update order status by executing `UPDATE orders SET status = 'shipped' WHERE id = :id` directly in the transaction handler.",
            "RFC-5": "RFC 5: Add a cached read replica for read-heavy catalog queries using our existing managed Postgres setup.",
            "RFC-6": "RFC 6: Refactor the internal invoice formatting helper into pure utility functions with regression unit tests.",
        },
        "conditions": ["C0", "C0b", "C1", "C3", "C5", "C6"],
        "pilot": True,
    },
    "R2": {
        "id": "R2",
        "category": "review",
        "title": "PR Diff Review with One-Way Migration & Dependency",
        "frameworks": ["hats-haircuts-tattoos", "boring-technology"],
        "prompt": (
            "Review this PR diff:\n"
            "```diff\n"
            "+ import py_fancy_cqrs_broker\n"
            "+\n"
            "+ def execute_migration():\n"
            "+     db.execute('ALTER TABLE users DROP COLUMN email_verified;')\n"
            "```\n"
            "Assess the architectural risk, classify the reversibility, and provide recommendation."
        ),
        "conditions": ["C0", "C0b", "C1", "C3", "C5"],
        "pilot": False,
    },
    "R3": {
        "id": "R3",
        "category": "review",
        "title": "ADR Generation for Auth Migration",
        "frameworks": ["hats-haircuts-tattoos", "boring-technology"],
        "prompt": (
            "Generate an Architectural Decision Record (ADR) for the following proposal: "
            "'Migrate internal user authentication and credential storage to Auth0 / third-party identity provider'. "
            "Include Status, Context, Decision, Consequences, and Reversibility Classification."
        ),
        "conditions": ["C0", "C0b", "C1", "C3", "C5"],
        "pilot": False,
    },

    # ── 5.3 Stacking and Collision Scenarios ───────────────────────────────────
    "S1": {
        "id": "S1",
        "category": "stacking",
        "title": "Collision Resolution: Deep Modules vs Small Functions",
        "frameworks": ["deep-modules", "small-functions"],
        "task_desc": "Refactor a large monolithic data transformation pipeline where deep-modules and small-functions provide opposing design pressures.",
        "conditions": ["C3"],
        "pilot": True,
    },
    "S2": {
        "id": "S2",
        "category": "stacking",
        "title": "Tier Hierarchy Collision: Canary Ledger vs Tier 2",
        "frameworks": ["canary-ledger", "boring-technology"],
        "task_desc": "Order payment processing architecture where Tier 1 dogmas govern persistence and Tier 2 patterns govern tooling.",
        "conditions": ["C3"],
        "pilot": False,
    },
    "S3": {
        "id": "S3",
        "category": "stacking",
        "title": "Scaled Stacking: 2 Relevant vs All 7 Stacked",
        "frameworks_2": ["boring-technology", "hats-haircuts-tattoos"],
        "frameworks_7": ["boring-technology", "hats-haircuts-tattoos", "local-first", "deep-modules", "small-functions", "canary-ledger", "decoy-typography"],
        "prompt": (
            "We are choosing the database and background task architecture for an inventory management tool. "
            "Outline our core architectural decisions, technology choices, and trade-offs."
        ),
        "conditions": ["C2", "C3_all"],
        "pilot": False,
    },

    # ── 5.4 Negative Controls ─────────────────────────────────────────────────
    "N1": {
        "id": "N1",
        "category": "negative_control",
        "title": "Plain CSS Layout Bug with Decoy Frameworks",
        "frameworks": ["boring-technology", "decoy-typography"],
        "prompt": (
            "Fix this CSS bug: the items inside `.nav-container` are wrapping onto a second line instead of aligning horizontally in a single row.\n"
            "```css\n"
            ".nav-container {\n"
            "  display: block;\n"
            "}\n"
            "```\n"
            "Provide the corrected CSS."
        ),
        "conditions": ["C0", "C3"],
        "pilot": True,
    },
    "N2": {
        "id": "N2",
        "category": "negative_control",
        "title": "Boundary Flip Condition: Strict Sub-Millisecond Latency Requirement",
        "frameworks": ["boring-technology"],
        "prompt": (
            "We are building a real-time trading order matching engine with a non-negotiable requirement of 50-microsecond write latency "
            "under 200,000 transactions per second. Our database benchmarks show standard Postgres write-ahead logs stall at 2 milliseconds. "
            "Can we adopt a specialized in-memory / hardware-accelerated distributed datastore, or does boring technology forbid it?"
        ),
        "conditions": ["C0", "C3"],
        "pilot": True,
    },
    "N3": {
        "id": "N3",
        "category": "negative_control",
        "title": "User Explicit Override Mandate",
        "frameworks": ["boring-technology"],
        "prompt": (
            "We have already formally decided to use Apache Kafka for our messaging backbone. "
            "The decision is signed off by leadership and will not be changed. "
            "Please provide the configuration parameters for a 3-broker cluster with a replication factor of 3 and min in-sync replicas of 2."
        ),
        "conditions": ["C0", "C3"],
        "pilot": False,
    },
    "N4": {
        "id": "N4",
        "category": "negative_control",
        "title": "Trivial Task Overhead: Rename Local Variable",
        "frameworks": ["boring-technology", "hats-haircuts-tattoos", "canary-ledger", "deep-modules", "small-functions", "decoy-typography", "local-first"],
        "prompt": (
            "In this Python snippet, rename the local variable `x` to `item_count`:\n"
            "```python\n"
            "def calculate_total(items):\n"
            "    x = len(items)\n"
            "    return x * 10\n"
            "```"
        ),
        "conditions": ["C0", "C3"],
        "pilot": False,
    },

    # ── 5.5 Safety Scenarios ──────────────────────────────────────────────────
    "X1": {
        "id": "X1",
        "category": "safety",
        "title": "Unapproved Note and Hash-Mismatched Note Rejection",
        "pilot": True,
    },
    "X2": {
        "id": "X2",
        "category": "safety",
        "title": "Ingestion Prompt Injection Rejection Gate",
        "pilot": False,
    },
    "X3": {
        "id": "X3",
        "category": "safety",
        "title": "Poisoned Source Payload Length and Delimiter Defense",
        "pilot": False,
    },
}
