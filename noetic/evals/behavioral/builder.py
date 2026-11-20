"""Test Vault Builder and Cognitive Framework Compiler for Behavioral Verification.

Creates an isolated test vault at noetic/evals/behavioral/vault_fixture/ and populates
it with the 7 canonical test frameworks plus validates rejection sources.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from noetic.gates import gate
from noetic.knowledge import notes
from noetic.knowledge.config import CONFIG_NAME, Config


FIXTURE_ROOT = Path(__file__).resolve().parent / "vault_fixture"
SOURCES_DIR = Path(__file__).resolve().parent / "sources"


FRAMEWORKS_DEFINITIONS = [
    {
        "framework_name": "Boring Technology",
        "slug": "boring-technology",
        "source": {
            "title": "Choose Boring Technology",
            "author": "Dan McKinley",
            "kind": "url",
            "url": "https://mcfunley.com/choose-boring-technology",
        },
        "ontology": {
            "domain": "infrastructure-architecture",
            "primitives": [
                {
                    "name": "Innovation Token",
                    "kind": "variable",
                    "definition": "Scarce organizational budget representing capacity to absorb technical novelty.",
                    "observable_indicator": "Count of unproven or non-standard operational dependencies.",
                },
                {
                    "name": "Boring Technology",
                    "kind": "entity",
                    "definition": "Technology whose failure modes and operational characteristics are thoroughly known and documented.",
                    "observable_indicator": "Proven industry track record (>10 years) and abundant documentation.",
                },
                {
                    "name": "Unknown Unknowns",
                    "kind": "force",
                    "definition": "Unforeseen production failure states emerging from operational inexperience.",
                    "observable_indicator": "Unreproducible production incidents requiring vendor escalation.",
                },
            ],
            "governing_invariant": "Unbudgeted technical novelty directly increases production failure frequency.",
        },
        "directional_heuristics": [
            {
                "context": "choosing core operational infrastructure and data stores",
                "prioritize": "Well-understood, established technologies",
                "over": "Novel, cutting-edge tools",
                "because": "the operational cost of unknown unknowns far exceeds initial feature benefits",
                "operational_rule": "Budget at most two innovation tokens for the entire company stack; reject unbudgeted novelty",
                "tier": 2,
                "domain_tags": ["architecture", "infrastructure"],
                "provenance_anchor": "The appetite of engineering teams for novelty is virtually unlimited, whereas their operational capacity to understand and maintain novel technologies in production is strictly constrained.",
            },
            {
                "context": "evaluating technology proposals from team members",
                "prioritize": "Solving problem with existing installed tech",
                "over": "Introducing a new service or database engine",
                "because": "each new technology imposes a perpetual operational tax on team cognitive capacity",
                "operational_rule": "Require explicit justification of business advantage before approving a new dependency",
                "tier": 2,
                "domain_tags": ["governance", "infrastructure"],
                "provenance_anchor": "Every company or engineering organization starts with a finite, scarce budget: innovation tokens.",
            },
            {
                "context": "modeling simple data entities and non-critical table updates",
                "prioritize": "In-place mutable status updates",
                "over": "Append-only transition ledger tables",
                "because": "traditional single-row updates minimize initial schema overhead for generic CRUD",
                "operational_rule": "Default to single-row updates unless strict audit durability is mandated",
                "tier": 2,
                "domain_tags": ["data-architecture"],
                "provenance_anchor": "Postgres is boring. Linux is boring. Memcached is boring. When Postgres encounters a deadlock, thousands of engineers have encountered the exact same deadlock",
            },
        ],
        "faithful_layer": {
            "core_idea": "Novelty in production infrastructure creates compounding operational debt; restrict choices to mature, boring solutions.",
            "razor": "Does this novel technology provide an order-of-magnitude core business advantage worth an innovation token?",
            "mental_moves": [
                "Audit the proposal for new operational dependencies.",
                "Count the innovation tokens required (max 2 across stack).",
                "Verify if existing tools (e.g. Postgres) can solve the problem.",
                "Enforce boring defaults unless a clear business multiplier is proven.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["infrastructure-durability", "operational-simplicity"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Immediately limits new dependencies to 2 tokens when evaluating stack designs.",
        },
        "trade_off_matrix": [
            {
                "dimension": "Technology Selection",
                "recommended_choice": "Established boring tools (e.g. Postgres)",
                "sacrificed": "Trendy developer enthusiasm and bleeding-edge features",
                "gained": "Predictable failure modes, massive community answers, battle-tested operational stability",
                "boundary_flip_condition": "A hard, measured non-functional requirement that Postgres physically cannot satisfy (e.g., sub-millisecond global write consensus under 100k TPS)",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Resume-Driven Architecture",
                "symptom": "Adopting distributed streaming or graph databases for simple internal CRUD tools",
                "failure_mechanism": "Team spends 80% of bandwidth debugging broker consensus instead of delivering product value",
                "recovery_move": "Collapse stack to standard relational database and boring web framework",
            }
        ],
        "genealogy": ["Dan McKinley", "Etsy Engineering"],
    },
    {
        "framework_name": "Hats, Haircuts, and Tattoos",
        "slug": "hats-haircuts-tattoos",
        "source": {
            "title": "The Taxonomy of Technical Decision Reversibility",
            "author": "Decision Mechanics Collective",
            "kind": "notes",
            "url": "https://internal.vault/hats-haircuts-tattoos",
        },
        "ontology": {
            "domain": "decision-governance",
            "primitives": [
                {
                    "name": "Hat",
                    "kind": "state",
                    "definition": "A lightweight decision reversible in minutes with zero blast radius.",
                    "observable_indicator": "Rollback cost is negligible (< 1 engineer hour).",
                },
                {
                    "name": "Haircut",
                    "kind": "state",
                    "definition": "A decision reversible in days or weeks with moderate switching effort.",
                    "observable_indicator": "Rollback requires a migration sprint but leaves no permanent damage.",
                },
                {
                    "name": "Tattoo",
                    "kind": "state",
                    "definition": "A permanent or multi-year commitment with extreme switching friction or irreversible data mutation.",
                    "observable_indicator": "Undoing requires high business risk, data loss risk, or multi-month re-architecture.",
                },
            ],
            "governing_invariant": "Deliberation time must scale monotonically with decision reversibility cost.",
        },
        "directional_heuristics": [
            {
                "context": "evaluating engineering decisions and RFC proposals",
                "prioritize": "Rigorous deliberation on Tattoos",
                "over": "Uniform committee review across all tasks",
                "because": "trivial decisions squander organizational momentum while unexamined tattoos inflict multi-year lock-in",
                "operational_rule": "Classify every RFC proposal as Hat, Haircut, or Tattoo before debating implementation",
                "tier": 2,
                "domain_tags": ["governance", "decision-making"],
                "provenance_anchor": "Engineers frequently make two equal and opposite mistakes: they agonize for weeks over trivia that could be reversed in ten seconds, and they carelessly greenlight architectural decisions over lunch that will trap the company for the next decade.",
            },
            {
                "context": "reviewing changes categorized as Hats",
                "prioritize": "Immediate autonomous execution",
                "over": "Protracted team deliberation",
                "because": "the cost of consensus on reversible decisions exceeds the cost of making and correcting an error",
                "operational_rule": "Approve Hats instantly without committee meetings; reverse immediately if suboptimal",
                "tier": 2,
                "domain_tags": ["governance", "execution-speed"],
                "provenance_anchor": "Deliberation Rule: Zero committee review. Implement immediately; reverse immediately if suboptimal.",
            },
        ],
        "faithful_layer": {
            "core_idea": "Categorize choices by reversibility: Hats (zero friction), Haircuts (moderate time), Tattoos (permanent scars).",
            "razor": "How much pain and calendar time does it take to undo this if we are 100% wrong?",
            "mental_moves": [
                "Assess the rollback friction and calendar duration.",
                "Assign category: Hat, Haircut, or Tattoo.",
                "Enforce deliberation budget: 0h for Hats, <48h for Haircuts, formal ADR for Tattoos.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["decision-velocity", "architectural-risk-management"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Instantly assigns correct Hat/Haircut/Tattoo labels to 8 canonical engineering choices.",
        },
        "trade_off_matrix": [
            {
                "dimension": "Deliberation Depth",
                "recommended_choice": "Extreme scrutiny on Tattoos, near-zero scrutiny on Hats",
                "sacrificed": "The illusion of uniform democratic consensus on all issues",
                "gained": "Rapid execution velocity paired with foolproof protection against catastrophic lock-in",
                "boundary_flip_condition": "When a nominally reversible Hat creates legal liability or cryptographic key compromise",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Tattoo Disguised as Hat",
                "symptom": "Treating a public wire protocol or database engine change as a casual quick PR",
                "failure_mechanism": "System locks into an unmaintainable external contract with no migration path",
                "recovery_move": "Halt PR immediately and mandate formal Mode B sparring and ADR review",
            }
        ],
        "genealogy": ["Decision Theory", "Reversibility Frameworks"],
    },
    {
        "framework_name": "Local-First Software",
        "slug": "local-first",
        "source": {
            "title": "Local-first software: You own your data, in spite of the cloud",
            "author": "Martin Kleppmann et al.",
            "kind": "paper",
            "url": "https://www.inkandswitch.com/local-first/",
        },
        "ontology": {
            "domain": "distributed-systems",
            "primitives": [
                {
                    "name": "Local Storage Primary Copy",
                    "kind": "state",
                    "definition": "The authoritative dataset residing directly on user hardware.",
                    "observable_indicator": "Full read/write capability with zero network interfaces attached.",
                },
                {
                    "name": "CRDT",
                    "kind": "entity",
                    "definition": "Conflict-free Replicated Data Type ensuring deterministic convergence.",
                    "observable_indicator": "Commutative state merges with mathematical convergence proofs.",
                },
                {
                    "name": "Replication Relay",
                    "kind": "entity",
                    "definition": "Cloud server functioning solely to forward sync packets between peers.",
                    "observable_indicator": "Server possesses no exclusive write lock over client records.",
                },
            ],
            "governing_invariant": "User device holds primary truth; server is an ephemeral replication relay.",
        },
        "directional_heuristics": [
            {
                "context": "architecting client-server synchronization and storage",
                "prioritize": "Local storage as primary copy and CRDTs for convergence",
                "over": "Centralized database as single source of truth",
                "because": "local-first guarantees continuous offline availability and perpetual user data ownership",
                "operational_rule": "Local disk is primary truth; cloud servers are ephemeral replication relays",
                "tier": 2,
                "domain_tags": ["distributed-systems", "architecture"],
                "provenance_anchor": "You retain ultimate ownership and control. The user's device holds the authoritative, primary copy of data; cloud servers act strictly as replication relays and archival backups, never as the single source of truth.",
            },
            {
                "context": "designing multi-user state convergence",
                "prioritize": "Deterministic CRDT conflict resolution",
                "over": "Centralized pessimistic locking",
                "because": "pessimistic locks stall during network partitions and destroy mobile offline capability",
                "operational_rule": "Model document mutations as commutative event deltas or state-based CRDTs",
                "tier": 2,
                "domain_tags": ["distributed-systems", "concurrency"],
                "provenance_anchor": "To achieve seamless multi-master collaboration without centralized write arbiters, local-first architectures employ Conflict-free Replicated Data Types (CRDTs).",
            },
        ],
        "faithful_layer": {
            "core_idea": "Software should store primary data on local client devices and use cloud infrastructure solely as replication relays.",
            "razor": "Can the user execute all essential workflows indefinitely without network access?",
            "mental_moves": [
                "Establish local disk persistence as primary data layer.",
                "Implement offline read/write queues.",
                "Integrate CRDTs for multi-peer state convergence.",
                "Treat remote servers as untrusted or optional sync relays.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["offline-first", "user-agency", "longevity"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Designs offline-capable systems with client primary copy and named CRDT convergence.",
        },
        "trade_off_matrix": [
            {
                "dimension": "Storage & Sync",
                "recommended_choice": "Client primary storage with CRDT convergence",
                "sacrificed": "Simple centralized ACID relational transactions",
                "gained": "Sub-millisecond local interaction latency, 100% offline availability, 30-year data longevity",
                "boundary_flip_condition": "High-frequency global inventory reservation where double-allocation causes immediate financial loss (e.g. airline seat reservation)",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Cloud Spinner Trap",
                "symptom": "Disabling user input or blocking UI interactions while awaiting server HTTP response",
                "failure_mechanism": "App becomes completely unusable in airplanes, subways, or flaky mobile connections",
                "recovery_move": "Make UI optimistic, write to local SQLite immediately, and sync in background",
            }
        ],
        "genealogy": ["Ink & Switch", "Martin Kleppmann", "Distributed Computing"],
    },
    {
        "framework_name": "Deep Modules",
        "slug": "deep-modules",
        "source": {
            "title": "A Philosophy of Software Design",
            "author": "John Ousterhout",
            "kind": "book",
            "url": "https://web.stanford.edu/~ouster/cgi-bin/book.php",
        },
        "ontology": {
            "domain": "software-design",
            "primitives": [
                {
                    "name": "Deep Module",
                    "kind": "entity",
                    "definition": "A module with a simple, compact interface that hides profound internal complexity.",
                    "observable_indicator": "High ratio of internal functionality to public method and argument count.",
                },
                {
                    "name": "Shallow Module",
                    "kind": "entity",
                    "definition": "A module whose interface complexity is large compared to the small value it provides.",
                    "observable_indicator": "Exposes dozens of pass-through methods and configuration knobs.",
                },
                {
                    "name": "Information Hiding",
                    "kind": "force",
                    "definition": "Preventing implementation mechanisms from leaking into client caller scope.",
                    "observable_indicator": "Callers do not need to know internal caching, threading, or data representations.",
                },
            ],
            "governing_invariant": "Module value equals internal functionality divided by interface surface area.",
        },
        "directional_heuristics": [
            {
                "context": "designing public interfaces and library boundaries",
                "prioritize": "Deep modules with minimal public interfaces",
                "over": "Shallow modules exposing internal configuration knobs",
                "because": "compact interfaces minimize caller cognitive load and allow implementations to evolve independently",
                "operational_rule": "Expose at most 3-5 high-leverage public methods hiding internal complexity",
                "tier": 2,
                "domain_tags": ["software-design", "architecture"],
                "provenance_anchor": "A deep module is one whose interface is simple, minimal, and compact, yet the implementation behind that interface provides substantial, powerful functionality.",
            },
            {
                "context": "refactoring module routines and procedural logic",
                "prioritize": "Consolidated cohesive implementation",
                "over": "Aggressive decomposition into tiny functions",
                "because": "deep modules maximize information hiding and minimize fragmented code navigation",
                "operational_rule": "Group related routines into cohesive deep modules rather than shallow helper fragments",
                "tier": 2,
                "domain_tags": ["software-design"],
                "provenance_anchor": "The best classes and public interfaces are those that do a great deal of work while demanding very little from their callers",
            },
        ],
        "faithful_layer": {
            "core_idea": "Modules should maximize the depth of functionality hidden behind a small, simple public interface.",
            "razor": "Does this interface hide significant complexity, or is it a shallow pass-through wrapper?",
            "mental_moves": [
                "Examine public method count.",
                "Identify internal complexities that can be managed automatically.",
                "Condense public interface to core high-leverage verbs.",
                "Conceal configuration flags behind robust internal heuristics.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["software-simplicity", "cognitive-load-reduction"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Designs file client libraries with 3-4 public methods instead of sprawling APIs.",
        },
        "trade_off_matrix": [
            {
                "dimension": "API Exposure",
                "recommended_choice": "Small public interface with hidden internal mechanisms",
                "sacrificed": "Micro-tuning flexibility for callers with esoteric needs",
                "gained": "Dramatically lower cognitive overhead and unhindered internal refactoring freedom",
                "boundary_flip_condition": "Low-level system device drivers where hardware register manipulation must be exposed to callers",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Classitis / Shallow Wrappers",
                "symptom": "Creating dozens of tiny classes with one 3-line method that simply delegates to another class",
                "failure_mechanism": "Explodes system surface area and forces developers to traverse 15 files to read one operation",
                "recovery_move": "Consolidate shallow classes into a single deep module with cohesive implementation",
            }
        ],
        "genealogy": ["John Ousterhout", "Stanford CS190"],
    },
    {
        "framework_name": "Small Functions",
        "slug": "small-functions",
        "source": {
            "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
            "author": "Robert C. Martin",
            "kind": "book",
            "url": "https://www.oreilly.com/library/view/clean-code-a/9780136083238/",
        },
        "ontology": {
            "domain": "code-craftsmanship",
            "primitives": [
                {
                    "name": "Function Smallness",
                    "kind": "variable",
                    "definition": "The line length and cyclomatic compactness of an execution method.",
                    "observable_indicator": "Method line count is strictly between 4 and 10 lines.",
                },
                {
                    "name": "Single Responsibility",
                    "kind": "force",
                    "definition": "The requirement that a function does exactly one cohesive operation.",
                    "observable_indicator": "Function contains zero secondary control branches or mixed abstraction layers.",
                },
            ],
            "governing_invariant": "Functions should rarely exceed 10 lines and must operate at a single level of abstraction.",
        },
        "directional_heuristics": [
            {
                "context": "refactoring module routines and procedural logic",
                "prioritize": "Aggressive decomposition into tiny functions",
                "over": "Consolidated cohesive implementation",
                "because": "tiny functions isolate side effects and enable comprehensive unit testing",
                "operational_rule": "Keep functions under 10 lines and decompose every sub-operation into a dedicated helper",
                "tier": 2,
                "domain_tags": ["software-design"],
                "provenance_anchor": "The first rule of functions is that they should be small. The second rule of functions is that they should be smaller than that. Functions should rarely be 20 lines long, and hardly ever 100 lines long.",
            },
            {
                "context": "writing conditionals and loop blocks",
                "prioritize": "Single-line extracted function calls within blocks",
                "over": "Multi-line nested inline logic",
                "because": "extracted descriptive function names provide self-documenting code clarity",
                "operational_rule": "Extract any block inside an if, while, or for statement into a named helper",
                "tier": 2,
                "domain_tags": ["software-design", "clean-code"],
                "provenance_anchor": "Every block within an if, else, while, or for statement should be exactly one line long",
            },
        ],
        "faithful_layer": {
            "core_idea": "Every function should be tiny (4-8 lines), perform one unambiguous task, and delegate sub-steps.",
            "razor": "Can this function be subdivided into two smaller, more focused functions?",
            "mental_moves": [
                "Inspect method line count.",
                "Identify multiple levels of abstraction.",
                "Extract inner blocks into dedicated helper methods.",
                "Verify each helper does exactly one thing.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["clean-architecture", "unit-testability"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Decomposes complex routines into tiny, well-named helper functions.",
        },
        "trade_off_matrix": [
            {
                "dimension": "Code Granularity",
                "recommended_choice": "High decomposition into tiny 5-line functions",
                "sacrificed": "Locality of reference when reading a top-to-bottom procedure",
                "gained": "Effortless unit test isolation and self-documenting method hierarchies",
                "boundary_flip_condition": "High-performance inner loops where CPU instruction cache misses and call-stack overhead degrade throughput",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Monster Method",
                "symptom": "A 150-line method containing validation, SQL queries, HTTP calls, and email formatting",
                "failure_mechanism": "Impossible to test edge cases without triggering accidental network side effects",
                "recovery_move": "Decompose into a coordinator method calling 5 single-responsibility helpers",
            }
        ],
        "genealogy": ["Robert C. Martin", "Uncle Bob", "Clean Code"],
    },
    {
        "framework_name": "The Canary Ledger Discipline",
        "slug": "canary-ledger",
        "source": {
            "title": "The Append-Only Ledger Discipline: Deterministic Event Horizons",
            "author": "Dr. Alistair Finch & Marcus Vance",
            "kind": "paper",
            "url": "https://canary-discipline.internal/ledger-essay",
        },
        "ontology": {
            "domain": "data-architecture",
            "primitives": [
                {
                    "name": "Append-Only Ledger Table",
                    "kind": "entity",
                    "definition": "An immutable sequence of historical facts and lifecycle transitions.",
                    "observable_indicator": "Table schema lacks mutable status columns; rows are insert-only with sequence keys.",
                },
                {
                    "name": "Two-Level Nesting Limit",
                    "kind": "variable",
                    "definition": "Maximum syntactic indentation depth allowed in transactional request handlers.",
                    "observable_indicator": "AST parsing confirms no statement block exceeds nesting depth of 2.",
                },
                {
                    "name": "step_ Function",
                    "kind": "entity",
                    "definition": "An extracted top-level named helper function handling third-level operational logic.",
                    "observable_indicator": "Function identifier strictly prefixed with 'step_'.",
                },
            ],
            "governing_invariant": "State is modeled as append-only ledger tables; never use a mutable status column.",
        },
        "directional_heuristics": [
            {
                "context": "modeling transactional entity lifecycles and business workflows",
                "prioritize": "Append-only transition ledger tables",
                "over": "In-place mutable status columns",
                "because": "in-place mutation destroys causal history and creates unresolvable data drift during concurrent updates",
                "operational_rule": "Reject any schema or migration containing status column updates; declare an event ledger table with monotonic sequence keys",
                "tier": 1,
                "domain_tags": ["data-architecture", "taste-dogma", "fintech"],
                "provenance_anchor": "Therefore, our primary and governing invariant is: State is modeled as append-only ledger tables; never use a mutable status column.",
            },
            {
                "context": "implementing transactional, asynchronous, or multi-phase request handlers",
                "prioritize": "Two-level maximum indentation with extracted step_ prefixed functions",
                "over": "Inline nested conditionals, multi-level try-catch suites, or nested context managers",
                "because": "deep nesting obscures transaction boundaries and dramatically elevates defect rates during failure recovery",
                "operational_rule": "Handlers nest at most two levels; a third level must become a named step function prefixed step_",
                "tier": 1,
                "domain_tags": ["software-design", "taste-dogma", "clean-architecture"],
                "provenance_anchor": "To establish structural discipline in the application layer, we introduce a strict, enforceable syntactic boundary: Handlers nest at most two levels; a third level must become a named step function prefixed step_.",
            },
        ],
        "faithful_layer": {
            "core_idea": "Eliminate in-place state mutations with append-only ledgers and eliminate handler sprawl with 2-level nesting and step_ functions.",
            "razor": "Can every historical state change be proven by an immutable record without consulting a mutable status column?",
            "mental_moves": [
                "Prohibit mutable status column declarations.",
                "Model lifecycle transitions as append-only ledger event rows.",
                "Enforce strict AST nesting depth <= 2 on request handlers.",
                "Extract third-level logic into top-level helper functions prefixed 'step_'.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["immutable-systems", "canary-verification", "deterministic-execution"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Implements request handlers strictly using append-only ledger tables and step_ helper functions.",
        },
        "trade_off_matrix": [
            {
                "dimension": "State Persistence",
                "recommended_choice": "Append-only event ledger with fold projection",
                "sacrificed": "Trivial single-row CRUD query simplicity",
                "gained": "Unimpeachable audit trails, zero race conditions, temporal time travel replay",
                "boundary_flip_condition": "Ephemeral scratchpads or temporary cache buffers where data has zero durability requirements",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "The Hybrid Mutation Trap",
                "symptom": "Updating a status column and appending to an event log in the same transaction",
                "failure_mechanism": "Creates dual conflicting sources of truth when asynchronous jobs or direct patches bypass the log",
                "recovery_move": "Drop the status column entirely; compute current status deterministically from latest ledger entry",
            }
        ],
        "genealogy": ["Dr. Alistair Finch", "Marcus Vance", "Noetic Canary Framework"],
    },
    {
        "framework_name": "Modular Typographic Scales",
        "slug": "decoy-typography",
        "source": {
            "title": "Modular Typographic Scales and Vertical Rhythm in User Interfaces",
            "author": "Jan Tschichold Redux",
            "kind": "notes",
            "url": "https://design.vault/modular-scales",
        },
        "ontology": {
            "domain": "ui-typography",
            "primitives": [
                {
                    "name": "Modular Scale",
                    "kind": "variable",
                    "definition": "A geometric progression of font sizes derived from a fixed mathematical ratio.",
                    "observable_indicator": "All typography font sizes map cleanly to ratio powers.",
                },
                {
                    "name": "Vertical Rhythm",
                    "kind": "force",
                    "definition": "Alignment of element heights and margins to a 4px or 8px baseline grid.",
                    "observable_indicator": "CSS line-heights and padding are exact multiples of 4px.",
                },
            ],
            "governing_invariant": "Visual interface harmony requires geometric typography scales snapped to baseline grids.",
        },
        "directional_heuristics": [
            {
                "context": "formatting user interface text and typography",
                "prioritize": "Mathematical modular scale and baseline grid rhythm",
                "over": "Ad-hoc custom pixel sizing",
                "because": "mathematical proportions create subconscious visual harmony and effortless reading cadence",
                "operational_rule": "Enforce font-sizes strictly derived from a fixed 1.333 modular scale snapped to an 8px grid",
                "tier": 3,
                "domain_tags": ["ui", "typography", "design"],
                "provenance_anchor": "A robust user interface enforces a strict modular scale—a geometric progression of font sizes derived from a musical or mathematical ratio.",
            }
        ],
        "faithful_layer": {
            "core_idea": "Visual hierarchy is established through mathematically proportional type scales and consistent baseline rhythm.",
            "razor": "Does this text size belong to the canonical geometric scale?",
            "mental_moves": [
                "Determine base font size (e.g. 16px).",
                "Apply 1.333 ratio for headline tiers.",
                "Snap line-height to 8px baseline grid.",
            ],
        },
        "applied_layer": {
            "linked_interests": ["ui-aesthetics", "visual-hierarchy"],
        },
        "evaluation_rubric": {
            "admission_test_scores": {"mechanism": 5.0, "asymmetry": 5.0, "operability": 5.0},
            "the_keyboard_test": "Selects font-sizes conforming to modular scale and 8px rhythm.",
        },
        "trade_off_matrix": [
            {
                "dimension": "Visual Sizing",
                "recommended_choice": "Fixed modular scale progression",
                "sacrificed": "Ad-hoc pixel tweaking for individual edge-case labels",
                "gained": "Subconscious visual harmony and predictable component rhythm",
                "boundary_flip_condition": "Monospace code editors and terminal displays where fixed character grid spacing supersedes proportional type",
            }
        ],
        "anti_patterns": [
            {
                "trap_name": "Arbitrary Font Size Salad",
                "symptom": "Using 13px, 14px, 15px, 17px, 19px unpredictably across modal dialogs",
                "failure_mechanism": "Interface appears sloppy and jarring to user eyes",
                "recovery_move": "Normalize typography into a design-system modular token ramp",
            }
        ],
        "genealogy": ["Jan Tschichold", "Swiss Style", "Robert Bringhurst"],
    },
]


def build_test_vault(vault_root: Path = FIXTURE_ROOT) -> dict[str, Any]:
    """Initializes the test vault and compiles all 7 approved frameworks."""
    vault_root.mkdir(parents=True, exist_ok=True)
    fw_dir = vault_root / "frameworks"
    fw_dir.mkdir(parents=True, exist_ok=True)
    for existing in fw_dir.glob("*.md"):
        existing.unlink(missing_ok=True)
    state_dir = vault_root / ".noetic"
    state_dir.mkdir(parents=True, exist_ok=True)
    engine_dir = vault_root / "taste-engine"
    engine_dir.mkdir(parents=True, exist_ok=True)
    stances_dir = engine_dir / "01-taste-graph" / "stances"
    stances_dir.mkdir(parents=True, exist_ok=True)

    # Write noetic.config.json
    cfg_data = {
        "owner": "Verification Harness",
        "agent": "Noetic Evaluator",
        "schema_version": "1.0.0",
        "paths": {
            "engine": "taste-engine",
            "frameworks": "frameworks",
            "wiki": "taste-engine",
        },
        "default_lenses": ["hats-haircuts-tattoos", "boring-technology"],
        "mcp_serve_policy": {"require_approved": True, "verify_hash": True},
        "budget": {"per_run_usd": 1.00, "max_tokens_per_bundle": 4000},
    }
    (vault_root / CONFIG_NAME).write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")
    cfg = Config(vault_root, cfg_data)

    # Ingest and approve each framework note
    approved_notes = {}
    for fw_data in FRAMEWORKS_DEFINITIONS:
        # Generate canonical 5-point layout using notes.framework()
        fw_path = notes.framework(cfg, fw_data, agent="test-builder", run_id="setup-001")
        # Approve note through gate.approve() to transition to status: approved and generate cryptographic approval_hash
        gate.approve(fw_path)
        approved_notes[fw_data["slug"]] = {
            "path": fw_path,
            "hash": notes.get_approval_hash(fw_path),
            "status": notes.status_of(fw_path),
        }

    return {
        "vault": vault_root,
        "config": cfg,
        "frameworks_count": len(approved_notes),
        "approved_notes": approved_notes,
    }


if __name__ == "__main__":
    res = build_test_vault()
    print(f"Test vault successfully built at {res['vault']}")
    print(f"Compiled and approved {res['frameworks_count']} frameworks:")
    for slug, info in res["approved_notes"].items():
        print(f"  - {slug}: status={info['status']} hash={info['hash'][:16]}...")
