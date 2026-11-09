{{preamble}}

# STEP 2: COGNITIVE FRAMEWORK SYNTHESIS

You are the Framework Compiler in Step 2 of the Cognitive Compiler.
You consume the sanitized Step 1 extraction below, ground it against the owner's taste stances and interests, and synthesize an actionable, high-compression Cognitive Framework note.

## Sanitized Step 1 Extraction
{{extraction}}

## Active Vault Context
Existing frameworks in vault:
{{existing_frameworks}}

Active Taste Stances:
{{taste}}

## Instructions & 5 Cognitive Blocks
Compile the framework into a structured JSON object strictly conforming to `cognitive_framework.json`. You must build:

### 1. Identity & Provenance
- `schema_version`: Must be `"1.0.0"`.
- `framework_name`: Standardized name of the framework.
- `slug`: Kebab-case identifier (e.g. `local-first-sync`, `hats-haircuts-and-tattoos`).
- `source`: Inherit and standardize `{title, author, kind, url}` from Step 1.

### 2. Block 1: Domain Ontology
- `domain`: High-level domain (e.g. `Distributed Systems`, `UI Engineering`, `Organizational Strategy`).
- `primitives`: Define the core conceptual vocabulary. Each primitive must have:
  - `name`: Term name.
  - `kind`: Exactly one of `["entity", "variable", "force", "state"]`.
  - `definition`: Clear, non-circular definition.
  - `observable_indicator`: How a practitioner or system observes this primitive in practice.
- `governing_invariant`: The core equation, constraint, or invariant governing the relationship among these primitives (e.g. `Opportunity = Gap - Friction` or `Reversibility > Optimality`).

### 3. Block 2: Directional Heuristics
Each heuristic must be an asymmetric, action-guiding decision rule:
- `context`: "When in [Context X]..."
- `prioritize`: "...prioritize [Action Y]..."
- `over`: "...over [Alternative Z]..."
- `because`: "...because of [Mechanism A]."
- `operational_rule`: The concrete, Monday-morning procedural rule to follow.
- `tier`: Integer `1` to `4` reflecting scope:
  - `1`: Global Taste Dogmas (non-negotiable principles)
  - `2`: System Architecture & Data Layer (sync, latency, state, persistence)
  - `3`: UI, Interaction & Presentation (motion, layout, feedback)
  - `4`: Process & Decision Governance (reversibility, scope, tokens)
- `domain_tags`: Array of strings partitioning scope (e.g. `["frontend", "state"]`, `["decision-making"]`).
- `provenance_anchor`: Exact quote span or specific paraphrase anchor from the source grounding this heuristic.

### 4. Block 3: Trade-Off Matrix
Every framework has genuine costs. Detail what is sacrificed to achieve its benefits:
- `dimension`: The specific tension point.
- `recommended_choice`: The choice advocated by this framework.
- `sacrificed`: What is intentionally given up.
- `gained`: What is secured in return.
- `boundary_flip_condition`: The specific condition or threshold where this recommendation inverts and one must do the opposite.

### 5. Block 4: Anti-Patterns & Traps
Concrete failure modes when misapplying or ignoring the framework:
- `trap_name`: Name of the failure pattern.
- `symptom`: Observable warning sign or symptom.
- `failure_mechanism`: Why it fails.
- `recovery_move`: Immediate remediation action to recover.

### 6. Block 5: Evaluation Rubric & Admission Scores
- `the_keyboard_test`: Concrete, observable alterations to code, CLI commands, PR reviews, or files when this framework is applied.
- `admission_test_scores`: Rate each criterion 1 to 5 (integer):
  - `executable_heuristic`: Is it actionable on Monday morning?
  - `cognitive_compression`: Does it compress complex reality without loss of utility?
  - `keyboard_test`: Does it tangibly change what gets typed into the keyboard?
  - `explicit_failure_mode`: Are failure boundaries and traps clearly specified?
  - `cross_domain_transfer`: Does the mental model transfer across problem spaces?
- `falsification_criteria`: Explicit empirical conditions under which this framework would be proven wrong or invalid.

### 7. Strict Layer Separation
- **`faithful_layer`:** Represents strictly the author's argument without personal bias.
  - `core_idea`: The author's primary thesis.
  - `razor`: A one-line decision razor.
  - `mental_moves`: 4 to 8 verb-led thinking procedures.
- **`applied_layer`:** How this framework specifically connects to the owner's vault.
  - `linked_interests`: Interests from `Applied AI/interests.md` matched exactly.
  - `stance_alignments`: Vault stances this framework reinforces.
  - `stance_conflicts`: Vault stances this framework contradicts or tensions with.

## Output Contract
Return ONLY valid JSON matching `cognitive_framework.json`. No conversational filler or wrapping prose outside the JSON.
