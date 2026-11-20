"""Test driver for Cumulative Multi-Pass Book Compiler."""

from pathlib import Path
import json

from noetic.knowledge.book_compiler import BookCompiler

epub_path = Path.home() / "Calibre Library" / "Robert Greene" / "The 48 Laws of Power (416)" / "The 48 Laws of Power - Robert Greene.epub"

compiler = BookCompiler(
    epub_path=epub_path,
    title="The 48 Laws of Power",
    author="Robert Greene",
    domain="strategic-influence",
)

# Run Pass 1 -> Pass 2 (first 6 chapters) -> Pass 3
framework = compiler.compile(max_chapters=6)

print("\n=== SYNTHESIZED FRAMEWORK NOTE ===")
print("Framework Name:", framework.get("framework_name"))
print("Domain:", framework.get("ontology", {}).get("domain"))
print("Core Idea:", framework.get("core_idea"))
print("\nDirectional Heuristics:")
for i, h in enumerate(framework.get("directional_heuristics", []), 1):
    print(f"  {i}. When {h.get('when', 'applicable')}:")
    print(f"     Prioritize: {h.get('prioritize')}")
    print(f"     Over:       {h.get('over')}")
    print(f"     Because:    {h.get('because')}")

# Save to test output
out_file = Path(__file__).resolve().parent / "vault_fixture" / "frameworks" / "48-laws-of-power.json"
out_file.write_text(json.dumps(framework, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved raw compiled framework to {out_file}")
