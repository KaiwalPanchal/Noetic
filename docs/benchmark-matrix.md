# Noetic Multi-Harness & Multi-Model Benchmark Matrix

*Measured: 2026-10-07 04:30 IST on Windows x86_64*  
*Harnesses Tested:* `agy` (Antigravity v1.3.0) and `claude` (Claude Code v2.1.292)  
*Models Tested:* `gemini-3.8-flash-low`, `gemini-3.8-flash-high`, `claude-sonnet-4-6`, `claude-opus-4-6-thinking`, `claude-3-5-sonnet`, `claude-3-opus`

---

## 1. Executive Summary & Takeaways

1. **Flash Low is 5x to 8x Faster Than High:**
   - On `ingest`: `gemini-3.8-flash-low` completed in **21.31s** vs **102.16s** for `gemini-3.8-flash-high`.
   - On `draft`: `gemini-3.8-flash-low` completed in **22.10s** vs **168.08s** for `gemini-3.8-flash-high`.
   - Both produce 100% valid schema output (`schema_valid = True`). The low-effort mode is vastly superior for interactive pipelines; high-effort is suitable for complex architectural briefs.

2. **Sonnet on `agy` Provides the Sweet Spot for Structural Quality:**
   - `claude-sonnet-4-6` executed in **38.57s** with perfect JSON schema adherence on extraction.
   - `claude-opus-4-6-thinking` took **71.02s** with extensive chain-of-thought before emitting structured JSON.

3. **Claude CLI Session Limit Behavior:**
   - Direct execution via `claude -p` fails instantly (3.79s) with `429 usage_limit_reached ("resets 5:50am")`.
   - In contrast, invoking `claude-sonnet-4-6` and `claude-opus-4-6-thinking` via `agy` succeeds without hitting the local Claude Code session lock.

---

## 2. Benchmark Matrix

| Harness | Model | Workflow | Status | Latency | Schema Adherence | Error / Notes |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **`agy`** | `gemini-3.8-flash-low` | `ingest` | **SUCCESS** | **21.31s** | ✅ Valid (0 errs) | Fastest extraction runtime |
| **`agy`** | `claude-sonnet-4-6` | `ingest` | **SUCCESS** | **38.57s** | ✅ Valid (0 errs) | Balanced reasoning & speed |
| **`agy`** | `claude-opus-4-6-thinking` | `ingest` | **SUCCESS** | **71.02s** | ✅ Valid (0 errs) | Deep thinking CoT |
| **`agy`** | `gemini-3.8-flash-high` | `ingest` | **SUCCESS** | **102.16s** | ✅ Valid (0 errs) | High reasoning budget |
| **`agy`** | `gemini-3.8-flash-low` | `draft` | **SUCCESS** | **22.10s** | ✅ Valid (0 errs) | Rapid Twitter thread generator |
| **`agy`** | `gemini-3.8-flash-high` | `draft` | **SUCCESS** | **168.08s** | ✅ Valid (0 errs) | Extended deliberation |
| **`claude`** | `sonnet` | `ingest` | **QUOTA_429** | 3.79s | ❌ Failed | Blocked: Claude Code session limit |
| **`claude`** | `opus` | `ingest` | **QUOTA_429** | 3.50s | ❌ Failed | Blocked: Claude Code session limit |

---

## 3. Workflow Definitions Tested

1. **`ingest` (`workflows/taste_engine`):**
   - **Task:** Source text $\rightarrow$ Thinking framework extraction (`title`, `core_principles`, `mental_moves`, `anti_patterns`).
   - **Schema:** `workflows/taste_engine/schemas/framework.json`.
2. **`draft` (`workflows/twitter`):**
   - **Task:** Note/concept $\rightarrow$ High-density Twitter thread with character limits.
   - **Schema:** `workflows/twitter/schemas/thread.json`.
3. **`curate` (`workflows/taste_engine`):**
   - **Task:** Signal mining $\rightarrow$ Curation packages & negative filter verification.
   - **Schema:** `workflows/taste_engine/schemas/curation.json`.
4. **`briefing` (`workflows/briefing`):**
   - **Task:** Daily activity logs $\rightarrow$ Executive summary & priority list.
   - **Schema:** `workflows/briefing/schemas/briefing.json`.

---

## 4. How to Reproduce

Run the matrix tool directly from the repository root:

```bash
# Run all models on agy harness
python tools/benchmark_matrix.py --harnesses agy --models gemini-3.8-flash-low,gemini-3.8-flash-high,claude-sonnet-4-6,claude-opus-4-6-thinking --workflows ingest,draft

# Run Claude harness (after session reset at 5:50 AM)
python tools/benchmark_matrix.py --harnesses claude --models sonnet,opus --workflows ingest
```
