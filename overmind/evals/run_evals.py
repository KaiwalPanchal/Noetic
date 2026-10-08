"""Eval harness: grades a pluggable extractor against a labelled golden dataset.

What this is: a grading harness plus a deterministic baseline extractor. It
computes accuracy / precision / recall / F1 / Cohen's kappa for the
approve-vs-reject decision, and can act as a regression gate for whichever
extractor you plug in.

What this is NOT: an evaluation of the LLM extraction pipeline. No LLM is called
here. The shipped default extractor is a rule-based baseline whose rules were
written after reading this 30-case set, so its score is in-sample. To evaluate a
real extractor, pass ``--extractor module:callable`` (see ``extractors.py``).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
  sys.stderr.reconfigure(encoding="utf-8")

from .extractors import Extractor, RuleBasedExtractor, load_extractor
from .graders import DeterministicGrader, JudgeEvaluator

DATASET_PATH = Path(__file__).resolve().parent / "golden_dataset.json"
HELDOUT_PATH = Path(__file__).resolve().parent / "heldout_dataset.json"
# Regression floor for the shipped rule-based baseline (set below its measured F1).
# A different extractor should be gated with its own --threshold.
F1_REGRESSION_THRESHOLD = 0.80


def _extractor_name(extractor: Extractor) -> str:
  return getattr(extractor, "name", None) or getattr(extractor, "__name__", None) or type(extractor).__name__


def run_evaluations(
    extractor: Extractor | None = None,
    quiet: bool = False,
    output: Path | str | None = None,
    threshold: float = F1_REGRESSION_THRESHOLD,
    dataset_path: Path | str | None = None,
) -> tuple[dict, bool]:
  """Grade ``extractor`` on a labelled dataset. Returns (metrics, passes_gate)."""
  dataset_path = Path(dataset_path) if dataset_path else DATASET_PATH
  if not dataset_path.exists():
    raise FileNotFoundError(f"Dataset not found at {dataset_path}")

  extractor = extractor or RuleBasedExtractor()
  name = _extractor_name(extractor)
  dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
  evaluator = JudgeEvaluator()
  results_log = []
  total_start = time.time()

  for item in dataset:
    t0 = time.time()
    extracted = extractor(item["source_text"])  # text only: no category/label leak
    latency_ms = (time.time() - t0) * 1000.0
    if not isinstance(extracted, dict):
      raise TypeError(f"Extractor {name!r} must return a dict, got {type(extracted).__name__}")

    schema_res = DeterministicGrader.grade_schema(extracted)
    full_text = " ".join(
        [extracted.get("title", "")]
        + list(extracted.get("core_principles", []))
        + list(extracted.get("anti_patterns", []))
    )
    entities_res = DeterministicGrader.grade_entities(full_text, item["ground_truth"]["required_entities"])
    buzzwords_res = DeterministicGrader.grade_buzzwords(full_text, item["ground_truth"]["forbidden_buzzwords"])
    injection_res = DeterministicGrader.grade_injection_resistance(full_text)

    # Decision rule: approve if the candidate was not rejected, has a valid schema,
    # adequate required-entity recall, low forbidden-buzzword penalty, no injection leak.
    rejected = extracted.get("rejected", False)
    has_entities = entities_res["recall"] >= 0.5 or not item["ground_truth"]["required_entities"]
    predicted_pass = (
        injection_res["resisted"]
        and not rejected
        and schema_res["valid"]
        and has_entities
        and buzzwords_res["penalty"] < 0.4
    )
    actual_pass = item["should_pass"]
    evaluator.record(predicted_pass, actual_pass)

    results_log.append({
        "id": item["id"],
        "category": item["category"],
        "predicted_pass": predicted_pass,
        "actual_pass": actual_pass,
        "latency_ms": round(latency_ms, 2),
        "entity_recall": entities_res["recall"],
        "buzzword_penalty": buzzwords_res["penalty"],
        "injection_resisted": injection_res["resisted"],
    })

  total_duration = time.time() - total_start
  metrics = evaluator.metrics()
  metrics["total_duration_s"] = round(total_duration, 2)
  metrics["avg_latency_ms"] = round(total_duration / len(dataset) * 1000.0, 2)
  metrics.update({"tp": evaluator.tp, "fp": evaluator.fp, "tn": evaluator.tn, "fn": evaluator.fn})

  if not quiet:
    print("\n" + "=" * 70)
    print(" OVERMIND EVAL HARNESS (grades a pluggable extractor) ")
    print("=" * 70)
    print(f"Extractor: {name}")
    print(f"Dataset: {dataset_path.name}  ({metrics['total']} cases)")
    print(f"TP: {evaluator.tp} | FP: {evaluator.fp} | TN: {evaluator.tn} | FN: {evaluator.fn}")
    print("-" * 70)
    print(f"{'Accuracy':<25} | {metrics['accuracy'] * 100:.1f}%")
    print(f"{'Precision':<25} | {metrics['precision'] * 100:.1f}%")
    print(f"{'Recall (TPR)':<25} | {metrics['recall'] * 100:.1f}%")
    print(f"{'Specificity (TNR)':<25} | {metrics['tnr'] * 100:.1f}%")
    print(f"{'F1 Score':<25} | {metrics['f1']:.3f}")
    print(f"{'Cohen kappa':<25} | {metrics['kappa']:.3f}")
    print("=" * 70)

  if output is not None:
    summary = {
        "extractor": name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "metrics": metrics,
        "details": results_log,
    }
    Path(output).write_text(json.dumps(summary, indent=2), encoding="utf-8")

  return metrics, metrics["f1"] >= threshold


def main(argv: list[str] | None = None) -> None:
  import argparse

  ap = argparse.ArgumentParser(description="Grade an extractor on the golden dataset.")
  ap.add_argument("--extractor", help="module:callable (default: built-in rule-based baseline)")
  ap.add_argument("--threshold", type=float, default=F1_REGRESSION_THRESHOLD, help="F1 gate")
  ap.add_argument("--dataset", default="golden", help="golden | heldout | path to a JSON file")
  ap.add_argument("--output", help="write JSON results to this path")
  args = ap.parse_args(argv)

  extractor = load_extractor(args.extractor) if args.extractor else None
  dataset = {"golden": DATASET_PATH, "heldout": HELDOUT_PATH}.get(args.dataset, args.dataset)
  metrics, passed = run_evaluations(
      extractor=extractor, output=args.output, threshold=args.threshold, dataset_path=dataset)
  if not passed:
    print(f"\n[GATE FAILED] F1 {metrics['f1']} < threshold {args.threshold}", file=sys.stderr)
    sys.exit(1)
  print(f"\n[GATE PASSED] F1 {metrics['f1']} >= threshold {args.threshold}")


if __name__ == "__main__":
  main()
