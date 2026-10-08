# Noetic implementation plan (steps 1 to 4 + docs)

Audience: an implementing agent with no prior context. Follow it literally. Every task lists exact files, signatures,
a test, and a command that proves it. If anything here disagrees with the code, **stop and report the mismatch**; do not improvise.

Status when this was written (branch `refactor/agent-agnostic`, verify with `git log --oneline | head -5`):

| Step | What | State |
|---|---|---|
| 0 | cleanup (`tools/pipeline.py` removed, ROADMAP honest) | DONE, commit `8939ddd` |
| 5 | `.noetic/` state + `noetic.config.json` + `noetic migrate` | DONE, commit `0ccc472` (253 tests passing) |
| 1 | tool registry, agent spec, Sensei, capture (clip) | TODO (Part A) |
| 2 | bounded loop executor | TODO (Part B) |
| 3 | taste gate | TODO (Part C) |
| 4 | Liminal sidecar client | TODO (Part D) |
| docs | README, ARCHITECTURE, HOW_TO_USE, VISUAL_REFERENCE, ROADMAP, vault log | TODO (Part E) |

Do the parts in order A, B, C, D, E. One commit per part. Never use `--no-verify`. Do not push unless the owner asks.

---

## 0. Rules that must survive every change (from `ARCHITECTURE.md` and the `noetic-builder` skill)

1. **The core never imports a workflow by name.** Workflows are found by `noetic/orchestration/loader.py:load_workflows`. New products go in `workflows/<name>/` with a `workflow.py` exposing `register(app, registry)`.
2. **Dependencies point down only:** `workflows -> orchestration -> agents/tools/gates -> knowledge`. `noetic/knowledge/*` must not import `noetic.orchestration`.
3. **Agents are steps; Python owns control flow.** Every agent output is JSON-schema validated (`noetic/tools/schema_check.py`). Loops are allowed only through the bounded executor of Part B.
4. **Human gate.** Machine output is `status: pending_review`. Never write `status: curated`. Never post externally. Never commit or push inside a target repo.
5. **Private data stays private.** Anything that reads the vault must go through `noetic/knowledge/context.py:iter_notes`/`is_private`. Never read `the private profile folder under <overmind>/wiki/`.
6. **Idempotent writes.** Never clobber user text.
7. **Deterministic where possible.** No-LLM paths first; say so in `--help` text.
8. **Code style:** 2-space indent, `from __future__ import annotations`, module docstring first, type hints like the neighbours. Match `noetic/orchestration/*.py`.
9. **Tests:** pytest, no network, no real agent CLIs (mock `run_agent`; see `tests/test_fleet.py` for the pattern). Fixtures `vault`, `cfg` are in `tests/conftest.py`.
10. **Drift test:** `tests/test_visual_reference.py` fails unless every new CLI command, MCP tool, pipeline and slash command **name appears as text** in `docs/VISUAL_REFERENCE.md`. Update that doc in the same commit as the code.

Verification command used everywhere: `python -m pytest -q` from `C:/External Apps/overmind-taste-engine`. Baseline is **253 passed**.

---

## Part A: unified agent model, tool registry, Sensei, capture (step 1)

Goal: every worker is one spec (prompt + tools + trigger + execution policy); tools live in one registry; Phase 1 tools `focus`, `park`, `think`, `clip` move from the vault harness into the package.

### Source material to port (read before writing)

| Port from (vault harness, read-only) | To |
|---|---|
| `<VAULT>/OverMind/harness/focus.py` | `workflows/sensei/focus.py` |
| `.../harness/think.py` (`split_verdict`, `park_tangent`, `run_think`) | `workflows/sensei/pipelines.py` (pipeline `think`) |
| `.../harness/clipper.py` | already in package: `noetic/tools/clipper.py` (do not re-port; only add the CLI command) |
| `.../harness/web.py`, `static/` | **out of scope.** Leave in the vault. Record this in ROADMAP (Part E). |

The harness uses module globals (`FOCUS_FILE`, `PARKED_FILE`, `PROJECTS_DIR`). In the package, take paths from `Config`:
`focus_file = cfg.overmind / "wiki" / "focus.md"`, `parked_file = cfg.vault / "ideas" / "PARKED.md"`, `log_dir = cfg.overmind / "wiki" / "log"`, `inbox = cfg.vault / "inbox"`. If `cfg.overmind is None`, raise `noetic.orchestration.run.PipelineError("NO_OVERMIND", "paths.overmind is not set in noetic.config.json")` (CLI commands print it and exit 1).

### A1. Tool registry: `noetic/tools/registry.py` (new)

```python
@dataclass(frozen=True)
class Tool: name: str; fn: Callable; help: str; needs_cfg: bool = False
TOOLS: dict[str, Tool] = {}
def tool(name: str, *, help: str, needs_cfg: bool = False)   # decorator, registers into TOOLS
def call(name: str, cfg=None, **kwargs)                       # KeyError on unknown; ValueError if needs_cfg and cfg is None
def discover() -> dict[str, Tool]                             # imports noetic.tools.builtin, then orchestration.registry.discover()
```
Model it on `noetic/orchestration/registry.py` (same decorator + dict + `discover()` shape).

`noetic/tools/builtin.py` (new): register exactly these four, each a thin wrapper that imports lazily:
`clip_url(url, timeout=15)` -> `clipper.clip_url`; `verify_url(url)` -> `links.url_ok`; `check_schema(data, schema_name)` -> `check(data, prompts.schema(schema_name))`; `tweet_length(text)` -> `tweets.weighted_length`.
Cross-ref: `noetic/tools/clipper.py:85`, `noetic/tools/links.py:13`, `noetic/tools/prompts.py:45`, `noetic/tools/schema_check.py:20`, `noetic/tools/tweets.py:14`.

CLI: `noetic tools` lists `name  help` sorted (add to `noetic/cli.py`, `@app.command()`, calls `registry.discover()`).

### A2. Agent spec: `noetic/agents/spec.py` (new)

Dataclass `AgentSpec(name, description, trigger, policy, pipeline, tools, payload, budget, prompt_name, body, path)`.
Functions: `parse(text, path=None) -> AgentSpec` (YAML frontmatter via `yaml.safe_load`; `pyyaml` is already a dependency in `pyproject.toml`), `load_specs() -> dict[str, AgentSpec]` (scans `noetic.orchestration.loader.resource_dirs("agents")`, i.e. `workflows/*/agents/*.md`; duplicate names raise `SpecError`), `validate(spec, tool_names, pipeline_names) -> list[str]`, `find_by_hook(specs, event)`. `AgentSpec.render(values)` returns `prompts.contract() + "\n" + prompts.fill(template, values)` (same ordering as `noetic/tools/prompts.py:40 render_raw`). When `prompt_name` is set the template is `find_resource("prompts", f"{prompt_name}.md")`, else the spec body.

Frontmatter fields: `name, description, trigger, policy, pipeline` required; `tools` (list), `payload`, `budget` (mapping), `prompt` optional.
Validation rules (each a separate test):
- `policy` in `("workflow", "loop")`.
- `trigger` is `on-demand`, `schedule:<daily|weekly|hourly>`, or `hook:<event>`; a `hook:` spec must also have `payload` (the pipeline argument name that receives the hook text).
- `pipeline` is a key of `noetic.orchestration.registry.PIPELINES`.
- every `tools` entry is a key of `noetic.tools.registry.TOOLS`.
- `policy: loop` requires `budget.max_iterations` as an int >= 1.

Note: `noetic/agents/` already holds role contracts (`overmind.md`, `architect.md`, `_contract.md`). Leave them. Specs live in workflows, contracts stay in the core.

### A3. Fleet agents: Librarian and Worker

1. In `workflows/fleet/librarian.py` register a **pipeline** wrapper so the librarian can be run by a spec (do not remove the Typer command; `tests/test_fleet.py` covers `run_librarian`):
   ```python
   @pipeline("librarian", kind="knowledge", help="daily inbox digest (deterministic, no LLM, never moves notes)",
             args=[arg("--force", action="store_true")], agent_flag=False)
   def librarian_pipeline(run, a) -> list[str]:
     path = run.step("scan", lambda: str(run_librarian(run.cfg, bool(a.get("force")))) )
   ```
   Careful: `run_librarian` returns `None` when it ran in the last 24 h. Return `[]` in that case, else `[run.output(path)]`. Imports needed: `from noetic.orchestration.registry import arg, pipeline`.
2. Register tool `scan_inbox` (`needs_cfg=True`, wraps `librarian.scan`) in the same module via `@tool`.
3. Create `workflows/fleet/agents/librarian.md`:
   ```
   ---
   name: librarian
   description: Daily inbox triage. Flags empty/duplicate notes and suggests links. Never moves, edits or deletes.
   trigger: schedule:daily
   policy: workflow
   pipeline: librarian
   tools: [scan_inbox]
   ---
   Deterministic. No model is called. Output is a pending_review digest note.
   ```
4. Create `workflows/fleet/agents/worker.md`: `name: worker`, `trigger: on-demand`, `policy: loop`, `pipeline: delegate`, `prompt: delegate` (reuses `workflows/fleet/prompts/delegate.md`), `budget: {max_iterations: 3}`, `tools: []`.

### A4. Sensei workflow (new): `workflows/sensei/`

Files:
- `__init__.py` (empty), `workflow.py`, `focus.py`, `pipelines.py`, `schemas/think_verdict.json`, `agents/sensei.md`.
- `focus.py`: port `get_focus` (parse `focus.md` frontmatter using `noetic.knowledge.registry.split_frontmatter`, `noetic/knowledge/registry.py:67`), `write_focus`, `clear_focus`, `switch_focus`, `finish_focus`, `recent_switches`, `park_idea`, `log_event`. All take `cfg` as first arg. Behaviour must match the harness file exactly (same log headings `## DATE — Focus switched|Focus set|Focus done`, same frontmatter keys `project, commitment, done_when, committed`). `park_idea(cfg, title, note, thought="", focus=None)` appends to `ideas/PARKED.md` and never overwrites.
- Tools registered with `@tool(..., needs_cfg=True)` at import: `focus_get` (returns dict or `{}`), `park_idea`.
- `schemas/think_verdict.json`: strict (`additionalProperties: false`), all required: `brief` (string), `verdict` (enum `on_focus|tangent|switch`), `park_title` (string), `park_note` (string), `harness_notes` (array of strings). Copy the style of `workflows/fleet/schemas/delegate_report.json`.
- `agents/sensei.md`: `name: sensei`, `trigger: hook:off-focus`, `payload: thought`, `policy: workflow`, `pipeline: think`, `tools: [focus_get, park_idea]`. Body is the prompt, with placeholders `{{focus}}`, `{{thought}}`, `{{owner}}`. Port the judging instructions from the harness (`OverMind/harness/context.py` `assemble_thinking_prompt`); drop the old "verdict line" sentinel format since output is now JSON. Required content: judge the thought against the focus; `tangent` means park it and return to the commitment; `switch` only if the owner said so; keep `brief` to Core Signal / Applied Framework / bounded Next Action; put gaps in `harness_notes`.
- `pipelines.py`: `@pipeline("think", kind="project", help="Sensei: judge a thought against your focus; parks tangents", args=[arg("thought")])`. Steps: `focus = get_focus(cfg)`; prompt = `load_specs()["sensei"].render({...})`; `data = run.step("judge", lambda: agent_step(run, "judge", "think", prompt, "think_verdict", extra_check=...))`. `extra_check` returns `["park_title is empty for a tangent"]` when verdict is `tangent` and `park_title` is blank. If verdict is `tangent` **and** a focus exists, call `park_idea` and return `[run.output(parked_file)]`; otherwise return `[]`. Print `brief`. With no focus set: never park.
- `workflow.py` `register(app, registry)`: import `pipelines` and `focus` (this registers the pipeline and tools even when `app is None`; guard only the Typer commands with `if app is None: return` placed **after** the imports, as `workflows/fleet/workflow.py` does). Commands: `noetic focus ["commitment"] [--project P] [--done-when "..."] [--done]` (no args shows current focus; warn when `recent_switches(cfg, 7) >= 3`), `noetic park "<thought>" [--title T]`.

### A5. Capture workflow (new): `workflows/capture/`

`workflow.py` only. Command `noetic clip <url|text> [--context "..."]`: if the argument starts with `http` call `clipper.clip_url`, else treat it as raw text; write `inbox/<slug>.md` using `clipper.format_as_signal_note` (`noetic/tools/clipper.py:100`); never overwrite an existing file (append `-2`, `-3`, ...). Prints the path. No LLM.

### A6. Run the agents from the CLI (`noetic/cli.py`)

Add (all `@app.command()` on the Typer app; each calls `discover` first):
- `noetic agents`: table of `name | trigger | policy | pipeline | tools | problems` (problems from `spec.validate`; `-` when none).
- `noetic agent <name> [--arg key=value ...]`: run the spec's pipeline through `noetic.orchestration.cli.execute(cfg, spec.pipeline, args)`. Unknown name -> exit 2 with the list of known names.
- `noetic fire <event> [text]`: for each spec returned by `find_by_hook(specs, event)` execute it with `{spec.payload: text}`. This is the entry point for a Claude Code `UserPromptSubmit` hook.
Naming: put the Typer functions in `noetic/cli.py`; keep the logic in `noetic/agents/spec.py` so it is unit-testable.

### A7. Tests (new files; names are required, counts are minimums)

- `tests/test_tool_registry.py` (4): register+call; unknown name raises KeyError; `needs_cfg` without cfg raises; `discover()` contains the four builtins plus `focus_get`, `park_idea`, `scan_inbox`.
- `tests/test_agent_spec.py` (8): parse OK; each validation rule in A2 fails with a distinct message; `load_specs()` finds `librarian`, `worker`, `sensei`; **every shipped spec validates with zero problems** (this is the cross-reference check); duplicate name raises.
- `tests/test_sensei.py` (6): `switch_focus` writes frontmatter and logs `Focus set` then `Focus switched`; `finish_focus` clears; `recent_switches` counts only the last 7 days; `park_idea` appends and never overwrites; `think` pipeline with `steps_mod.run_agent` mocked (copy the mock style from `tests/test_fleet.py`): tangent is parked, `on_focus` is not, no-focus never parks, blank `park_title` on a tangent triggers the retry path.
- `tests/test_capture.py` (3): text clip lands in `inbox/`; second identical title does not overwrite; `http` input calls `clipper.clip_url` (monkeypatch it).

### A8. Acceptance for Part A (all must be true)

```
python -m pytest -q                                 # all green, >= 253 + 21 new
python -m noetic.cli agents 2>&1 | head -8          # shows librarian, sensei, worker, no "problems"
python -m noetic.cli tools                          # lists clip_url verify_url check_schema tweet_length focus_get park_idea scan_inbox
git grep -n "from workflows" noetic/                # only noetic/orchestration/loader.py and noetic/mcp/server.py (pre-existing) may match
```
If `python -m noetic.cli` does not run, use `python -c "from noetic.cli import app; app()" agents`. Commit message: `feat: unified agent spec, tool registry, Sensei and capture workflows`.

---

## Part B: bounded loop executor (step 2)

Goal: allow evaluator-optimizer loops while Python still owns control flow and the run stays resumable. Replaces the "no open-ended loop" rule with "loops only through `run_loop`, always budgeted".

### B1. `noetic/orchestration/loop.py` (new)

```python
@dataclass
class Verdict: ok: bool; feedback: str = ""
@dataclass
class LoopResult: result: object; verdict: Verdict; iterations: int; stopped_by: str   # "passed" | "max_iterations" | "max_seconds"
def run_loop(run, name, act, evaluate, *, max_iterations, max_seconds=None) -> LoopResult
```
Semantics:
- For `i in 1..max_iterations`: `result = run.step(f"{name}-act-{i}", lambda: act(i, feedback))`, then `verdict = Verdict(**run.step(f"{name}-eval-{i}", lambda: asdict(evaluate(i, result))))`. If `verdict.ok`, stop with `"passed"`. Else `feedback = verdict.feedback` and continue.
- Steps go through `run.step` (`noetic/orchestration/run.py:60`) so a resumed run reuses finished iterations.
- `max_iterations` must be >= 1 else `ValueError`. Check `max_seconds` against `time.monotonic()` **between** iterations only; never kill an agent mid-call. Stop reason `"max_seconds"`.
- `act` and `evaluate` return JSON-serializable data (they are cached in the run file).
- Never raises on exhaustion; the caller decides what a failed loop means.

### B2. Refactor `workflows/fleet/delegate.py` onto `run_loop`

Current loop is the `for i in range(1, limit + 1)` block (see `delegate.py` after the `base = run.step("prepare-repo", ...)` call). Replace it with `run_loop`: `act(i, feedback)` renders the delegate prompt and calls `agent_step(... write=True ...)`; `evaluate(i, report)` runs `run_tests` when `--test` is given (Verdict `ok = tests["passed"]`, feedback = the existing "The test command ... FAILED" text), and when there is no test command returns `Verdict(ok=True)` after the first attempt. **Keep step names compatible?** No: step names change to `delegate-act-N`/`delegate-eval-N`; update the one assertion in `tests/test_fleet.py` that inspects step names if any (search `attempt-`/`tests-`). Behaviour that must not change: branch isolation, `enforce_contract`, log entry text, return value, `CONTRACT_VIOLATION` semantics.

Take `max_iterations` from the CLI arg; if the `worker` spec is loaded, cap it at `spec.budget["max_iterations"]` only when the CLI arg is absent.

### B3. Tests

- `tests/test_loop.py` (6): passes on iteration 2; exhausts at `max_iterations` with `stopped_by == "max_iterations"`; `max_seconds=0` stops after iteration 1 (monkeypatch `time.monotonic`); `max_iterations=0` raises; **resume** (construct a `Run` with `run_id` of a half-finished run; confirm `act` is not called again for the finished iteration); feedback from iteration N reaches iteration N+1.
- `tests/test_fleet.py` must still pass after the refactor with only step-name edits.

### B4. Acceptance

`python -m pytest -q` green; `git grep -n "for i in range" workflows/ noetic/orchestration/` shows no hand-rolled agent loop left. Commit: `feat: bounded loop executor; delegate uses it`.

---

## Part C: taste gate (step 3)

Goal: reject generic output **before** it is persisted, using the owner's rules, deterministically first.

### C1. Rule files (owner-editable markdown), in `<state_dir>/taste/` i.e. `.noetic/taste/`

- `dogmas.md`: free text. Injected into prompts (C3). Not parsed.
- `anti-patterns.md`: parsed. Three optional sections, each a bullet list:
  - `## Banned phrases`: case-insensitive substring.
  - `## Banned patterns`: each bullet is a regex inside backticks, e.g. ``- `\bgame[- ]changer\b` ``.
  - `## Required`: substrings that must appear in at least one string field of the output (use sparingly).
No file = no enforcement (existing tests must stay green).

### C2. `noetic/gates/taste.py` (new)

```python
@dataclass
class TasteRules: dogmas: str; phrases: list[str]; patterns: list[re.Pattern]; required: list[str]
def load(cfg) -> TasteRules | None                       # None when no files exist
def violations(rules: TasteRules, data) -> list[str]     # walk every str in nested dict/list, skip key "harness_notes"
def prompt_block(rules: TasteRules) -> str               # "## Taste bar (non-negotiable)" + dogmas + bans
```
Messages are exact and actionable, e.g. `taste: banned phrase "game changer" in $.hooks[0].text`. Invalid regex in the file -> raise `ValueError` naming the bullet (fail loudly, do not skip).

### C3. Wire into `agent_step` (`noetic/orchestration/steps.py`)

- Before the call loop: `rules = taste.load(cfg)`; if present append `prompt_block(rules)` to the prompt.
- At the line `problems = check(res.data, schema) + (extra_check(res.data) if extra_check else [])` (currently `steps.py:58`) add `+ (taste.violations(rules, res.data) if rules else [])`. The existing retry-once-with-exact-errors path then handles rejection with no new control flow.
- Add a `taste: bool = True` keyword to `agent_step`; pass `False` for the Sensei `think` pipeline (judging output is not content).
- `noetic/gates/__init__.py`: export `taste`.

### C4. Seed + CLI + MCP

- `noetic/seed/taste/anti-patterns.md`: a short generic starter list (phrases like "delve into", "in today's fast-paced world", "game-changer", "unlock the power of", "rich tapestry", "it's important to note"). Installer copies it to `.noetic/taste/` **only if absent** (edit `noetic/installer.py` near the engine-dir creation, `installer.py:~210`). Also install an empty-but-commented `dogmas.md` if absent.
- CLI `noetic taste check <file>`: prints violations for a text/markdown file, exit 1 if any; `noetic taste show`: prints the active rules. (One Typer sub-app or two commands named `taste-check` and `taste-show`; the drift test needs the command names to appear in VISUAL_REFERENCE.)
- MCP tool `check_taste(text: str)` in `noetic/mcp/server.py` (decorator pattern at `server.py` `@server.tool()` blocks). Return `{"ok": bool, "violations": [...]}`.

### C5. Tests (`tests/test_taste.py`, 8)

parse each section; no files -> `load` returns None; phrase hit and miss (case-insensitive); regex hit; required missing; nested path in message (`$.hooks[0].text`); `harness_notes` ignored; **agent_step integration**: mock `run_agent` to first return a banned phrase then clean text, assert 2 attempts and the retry prompt contains the violation text (follow `tests/test_orchestration.py` for the mock pattern); invalid regex raises `ValueError`.

### C6. Acceptance & honesty

`python -m pytest -q` green. In docs state plainly: the gate is **deterministic string/regex rules only**; there is no LLM judge yet (listed as a gap in VISUAL_REFERENCE section 6). Commit: `feat: taste gate rejects generic output before it is written`.

---

## Part D: Liminal sidecar (step 4)

Decision (owner, 2026-10-09): **sidecar only.** Liminal is the separate repo `liminalfinal` (a public repo on the owner's GitHub) (co-built; its frontend belongs to a collaborator, so nothing from it is copied here). Noetic talks to it over HTTP. Noetic must work fully when Liminal is absent.

### D0. Liminal's API (verified by reading source on GitHub on 2026-10-09; **not run**)

Source: `liminalfinal/backend/app/{main.py, api/query.py, api/ingest.py, core/models.py, core/config.py}`. Re-check these before coding; if they differ, the repo wins and this section must be updated.

| Call | Request | Response fields used |
|---|---|---|
| `GET {base}/health` | none | `status`, `neo4j_connected` |
| `POST {base}/api/query` | `{"query": str (min 2 chars), "max_hops": 1-3, "top_k": 1-20, "filter_by_goal": str\|null}` | `answer`, `status` (`GROUNDED` or `REFUSED_INSUFFICIENT_CONTEXT`), `confidence_score`, `cited_nodes[]` (`node_id, entity_name, entity_type, hop_level`), `cited_passages[]` |
| `POST {base}/api/ingest/document` | `{"content": str, "title": str, "source_type": "note\|obsidian\|code_architecture\|postmortem\|research\|agent_insight", "source_url": str\|null, "author": str\|null, "tags": [str], "metadata": {}}` | `document_id`, `status`, `nodes_created`, `edges_created`, `wikilinks_detected[]` |

Default backend port is 8000 (`config.py`, `PORT`). There is no auth in the source; do not invent an API key header.

### D1. Config

`noetic.config.json` gains optional `"liminal": {"url": "http://localhost:8000", "timeout": 10}`. Env override `NOETIC_LIMINAL_URL`. In `noetic/knowledge/config.py` `Config.__init__` add `self.liminal_url: str | None` and `self.liminal_timeout: int`; `DEFAULTS` gets `"liminal": None`. Absent = Liminal disabled (not an error).

### D2. `noetic/knowledge/liminal.py` (new), stdlib only (`urllib.request`, `json`)

```python
class LiminalError(Exception)
class LiminalClient:
  def __init__(self, base_url: str, timeout: int = 10)
  def health(self) -> dict
  def query(self, question: str, *, max_hops=2, top_k=5, filter_by_goal=None) -> dict
  def ingest(self, title: str, content: str, *, source_type="obsidian", tags=None, author="noetic") -> dict
def client_for(cfg) -> LiminalClient | None        # None when not configured
```
Any `URLError`, timeout, non-200, or bad JSON -> `LiminalError` with a one-line message. No retries here (callers decide).

### D3. `noetic/knowledge/recall.py` (new)

`recall(cfg, question: str) -> dict` returns **one shape always**: `{"source": "liminal"|"vault-grep", "status": "GROUNDED"|"REFUSED_INSUFFICIENT_CONTEXT"|"UNGROUNDED", "answer": str, "citations": [str], "note": str}`.
- Liminal configured and reachable: map response 1:1; `citations` = `cited_nodes[].entity_name`. **If Liminal says REFUSED, return REFUSED with its text; never fall back to grep to manufacture an answer.**
- Not configured, or `LiminalError`: fall back to `noetic.knowledge.context.search(cfg, terms)` (`context.py:82`, already private-aware), `source="vault-grep"`, `status="UNGROUNDED"`, `answer` = the matched passages text, `note` = why Liminal was skipped (e.g. `liminal unreachable: <msg>`).

### D4. Librarian push (opt-in)

In `workflows/fleet/librarian.py` add `push_to_liminal(cfg, client) -> dict` and a `--liminal` flag on the `librarian` command and pipeline: for each inbox note that is not private (`context.is_private`) and not empty, `client.ingest(title=stem, content=body, source_type="obsidian")`. Idempotence: keep `{content_sha1: document_id}` in `<state_dir>/liminal.json`; skip notes whose hash is already there. A `LiminalError` on one note is recorded and the loop continues; digest gets a line `Liminal: N pushed, M skipped, K failed`. **Never** send anything under `private_paths` or the overmind profile folder. Digest note stays `pending_review`.

### D5. Surfaces

- CLI `noetic recall "<question>" [--json]` and `noetic liminal` (prints health or "not configured").
- MCP tool `recall(question: str)` returning the D3 dict.
- Tool registry: `@tool("recall", needs_cfg=True)` in `noetic/tools/builtin.py`.
- Add `recall` to the `tools:` list of the `sensei` spec? **No.** Keep Sensei deterministic about tools until the owner asks.

### D6. Tests (`tests/test_liminal.py`, 9). Use a real local `http.server.ThreadingHTTPServer` on port 0 serving canned JSON, not mocks of urllib.

health OK; query GROUNDED mapping; query REFUSED passes through and recall does **not** grep; unreachable port -> recall falls back with `source == "vault-grep"` and a `note`; non-200 raises LiminalError; unconfigured -> `client_for` None; librarian push posts once and a second run skips by hash; private note is never posted (assert server received zero requests for it); malformed JSON from server -> LiminalError.

### D7. Acceptance and honesty

`python -m pytest -q` green. State in docs: tested against a **fake HTTP server shaped like Liminal's source**, not a live Liminal (needs Neo4j + Qdrant). A live check is listed under "Not verified" in VISUAL_REFERENCE until someone runs `docker compose up` in `liminalfinal` and `noetic liminal` returns healthy. Commit: `feat: optional Liminal sidecar client (recall, librarian push)`.

---

## Part E: documentation sweep (do last, one commit: `docs: align docs with agent spec, loop, taste gate, Liminal`)

Update every file below; check each box by re-reading the diff.

| File | Change |
|---|---|
| `docs/VISUAL_REFERENCE.md` | Section 1 diagram: add Liminal sidecar box and `.noetic/` in the vault. Section 2: add `agents spec`, `tools registry`, `loop`, `taste` to the layer boxes; add `sensei`, `capture` workflows. Section 4: rows for `noetic agents`, `agent`, `fire`, `tools`, `focus`, `park`, `clip`, `think`, `recall`, `liminal`, `taste-check`/`taste-show`, MCP `check_taste`, `recall`. Section 5: replace "Let an agent plan open-endedly: fixed steps only" with "Let an agent loop without a budget: loops are bounded by `run_loop`". Section 6: remove the "Phase 1 tools live in the vault" gap except `web` (still vault-only); add gaps: no LLM taste judge, Liminal not tested live, `web` view not packaged. Section 7: update counts (CLI commands, MCP tools, pipelines, slash commands, test count) **by running the commands, not by estimating**. |
| `ARCHITECTURE.md` | Replace "Agents are steps, not planners... never an open-ended loop" with the bounded-loop rule; add sections: Agent spec, Tool registry, Taste gate, Liminal sidecar (with the D0 table); fix the layer table (`knowledge/`, `tools/` paths now `noetic/knowledge`, `noetic/tools`); remove `taste-engine.config.json`/`.taste-engine` mentions (grep for them). |
| `README.md` | Quick start uses `noetic.config.json`/`.noetic/`; add a short "Agents" and "Taste" and "Liminal (optional)" section; mention `noetic migrate`. |
| `docs/HOW_TO_USE.md` | Add how-tos: set a focus and let Sensei park tangents (`noetic focus`, `noetic run think`, `noetic fire off-focus`), write taste rules, point at a Liminal instance, migrate an old vault. |
| `ROADMAP.md` | Phase 1 -> mark `clip/think/focus` packaged, `web` still in vault; add Phase 6 "Agent spec + loop + taste + Liminal" with checkboxes and true statuses; keep "NOT verified" lines. |
| `docs/threat-model.md` | Add: Liminal client sends vault text to a user-configured URL (opt-in, private paths excluded, no auth in Liminal source); taste rules are local files. Fix `.taste-engine` mentions. |
| `noetic/orchestration/__init__.py`, `noetic/knowledge/__init__.py`, `noetic/tools/__init__.py` | Module docstrings: mention `loop.py`, `liminal.py`/`recall.py`/`migrate.py`, `registry.py`/`builtin.py`. |
| Vault (outside the repo; `<VAULT>` = the owner's vault root, kept out of this public repo) | Append one dated line to `OverMind/wiki/log/2026-10.md` per the vault `CLAUDE.md` ("You write the log"), and update `OverMind/ROADMAP.md` to match the repo roadmap. Do **not** touch `the private profile folder under <overmind>/wiki/`. |

Also append to `~/.claude/skills/noetic-builder/knowledge/preferences.md` (curated section only) one dated line per new owner preference you were told in the session, with the evidence. Never edit the GENERATED block.

---

## Final verification (Definition of done)

Run, in this order, and paste the real output into the final report:

```
cd "C:/External Apps/overmind-taste-engine"
python -m pytest -q
python -m build            # then: twine check dist/*
python -m venv "$SCRATCH/venv" && "$SCRATCH/venv/Scripts/pip" install dist/noetic_cli-*.whl
"$SCRATCH/venv/Scripts/noetic" --help
"$SCRATCH/venv/Scripts/noetic" agents
git log --oneline | head -8
```
`$SCRATCH` is the session scratchpad directory, never the repo. Report separately what was **not** verified: real agent CLIs end to end, a live Liminal, PyPI, GitHub Actions, Linux/macOS.

## Cross-reference index (anchors verified 2026-10-09; line numbers drift, re-grep if off)

| Thing | Where |
|---|---|
| Agent call / retry / fallback | `noetic/orchestration/steps.py` `agent_step` (validation line: `problems = check(...)`) |
| Run state + caching | `noetic/orchestration/run.py` `Run.step` |
| Pipeline decorator | `noetic/orchestration/registry.py` `pipeline`, `arg`, `discover` |
| Workflow discovery | `noetic/orchestration/loader.py` `load_workflows`, `resource_dirs`, `find_resource` |
| Prompt rendering | `noetic/tools/prompts.py` `render_raw`, `fill`, `contract` |
| Vault config / names | `noetic/knowledge/config.py` `config_file`, `state_dir_for`, `Config` |
| Private-aware reading | `noetic/knowledge/context.py` `iter_notes`, `is_private`, `search` |
| Frontmatter parse | `noetic/knowledge/registry.py` `split_frontmatter` |
| Delegate loop to refactor | `workflows/fleet/delegate.py` `delegate` |
| Librarian | `workflows/fleet/librarian.py` `scan`, `run_librarian` |
| MCP tools pattern | `noetic/mcp/server.py` `@server.tool()` blocks |
| CLI command pattern | `noetic/cli.py` `@app.command()` |
| Workflow `register` pattern | `workflows/fleet/workflow.py`, `workflows/briefing/workflow.py` |
| Mock-agent test pattern | `tests/test_fleet.py` (`steps_mod.run_agent` monkeypatch, `AgentResult`) |
| Drift test | `tests/test_visual_reference.py` |
| Vault harness to port | `<VAULT>/OverMind/harness/{focus,think,state,context}.py` |
| Liminal source | the `liminalfinal` repo, `backend/app/` |

## Stop conditions (ask the owner instead of guessing)

- A test outside the listed ones starts failing and the cause is not obvious in 10 minutes.
- Liminal's source no longer matches section D0.
- A step seems to require reading `the private profile folder under <overmind>/wiki/`, posting externally, committing inside a target repo, or `--no-verify`.
- The pre-commit hook (`tools/check_private.py`) blocks a commit: genericize the text; do not bypass it.
