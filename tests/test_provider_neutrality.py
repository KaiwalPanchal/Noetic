"""The canonical agent/prompt/command files must be provider-neutral."""

from pathlib import Path
import re

ENGINE = Path(__file__).resolve().parents[1] / "noetic"
CANONICAL = ("prompts", "commands", "agents", "templates")
BANNED = re.compile(r"claude|codex|gemini|antigravity|anthropic|openai|\bagy\b|WebFetch|WebSearch|slash[- ]command", re.I)

# {relative posix path: set of lowercase terms allowed in that file}. Keep empty unless justified.
ALLOWLIST: dict[str, set[str]] = {}


def test_canonical_dirs_have_no_provider_specific_wording():
  offenders = []
  for d in CANONICAL:
    for f in sorted((ENGINE / d).rglob("*.md")):
      rel = f.relative_to(ENGINE).as_posix()
      allowed = ALLOWLIST.get(rel, set())
      for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        for m in BANNED.finditer(line):
          if m.group(0).lower() not in allowed:
            offenders.append(f"{rel}:{n}: {m.group(0)}")
  assert not offenders, "provider-specific wording:\n" + "\n".join(offenders)


def test_agent_contracts_have_required_frontmatter():
  import yaml
  for name in ("overmind", "architect"):
    text = (ENGINE / "agents" / f"{name}.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    fm = yaml.safe_load(text.split("---", 2)[1])
    for key in ("name", "role", "reads", "writes", "gates", "tools"):
      assert key in fm, f"{name}.md missing {key}"
    assert fm["name"] == name


def test_overmind_contract_is_generic_and_gated():
  text = (ENGINE / "agents" / "overmind.md").read_text(encoding="utf-8")
  low = text.lower()
  assert "pending_review" in text and "14 days" in low and "persona" in low
  assert "never read" in low and "profile" in low
  from tests.conftest import private_terms
  assert not [t for t in private_terms() if t in low]


def test_architect_has_no_life_accountability_directive():
  low = (ENGINE / "agents" / "architect.md").read_text(encoding="utf-8").lower()
  assert "life they declared" not in low and "anti-abandonment" not in low
  assert "taxonomy lock" in low
