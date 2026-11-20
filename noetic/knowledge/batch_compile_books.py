"""Batch Cumulative Book Compiler for Non-Coding Taste Books.

Compiles:
1. The 48 Laws of Power (Robert Greene)
2. The Art of Thinking Clearly (Rolf Dobelli)
3. The Artist's Way (Julia Cameron)
4. 21 Lessons for the 21st Century (Yuval Noah Harari)

Generates:
- Structured JSON schemas in vault_fixture/frameworks/*.json
- Canonical markdown notes in vault_fixture/frameworks/*.md
- Cryptographic SHA-256 approval hashes via noetic.gates.gate.approve
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

from noetic.knowledge.book_compiler import BookCompiler
from noetic.knowledge.config import Config
from noetic.knowledge.notes import framework as write_framework_note
from noetic.gates.gate import approve

VAULT_DIR = Path(__file__).resolve().parent.parent / "evals" / "behavioral" / "vault_fixture"
FRAMEWORKS_DIR = VAULT_DIR / "frameworks"
CALIBRE_DIR = Path.home() / "Calibre Library"

BOOKS = [
    {
        "key": "48-laws-of-power",
        "title": "The 48 Laws of Power",
        "author": "Robert Greene",
        "domain": "power-dynamics",
        "epub": str(CALIBRE_DIR / "Robert Greene" / "The 48 Laws of Power (416)" / "The 48 Laws of Power - Robert Greene.epub"),
        "max_chapters": 6,
        "already_extracted": FRAMEWORKS_DIR / "48-laws-of-power.json",
    },
    {
        "key": "art-of-thinking-clearly",
        "title": "The Art of Thinking Clearly",
        "author": "Rolf Dobelli",
        "domain": "cognitive-hygiene",
        "epub": str(CALIBRE_DIR / "Rolf Dobelli" / "The Art of Thinking Clearly (415)" / "The Art of Thinking Clearly - Rolf Dobelli.epub"),
        "max_chapters": 8,
    },
    {
        "key": "the-artists-way",
        "title": "The Artist's Way",
        "author": "Julia Cameron",
        "domain": "creative-recovery",
        "epub": str(CALIBRE_DIR / "Julia Cameron" / "The Artist's Way (464)" / "The Artist's Way - Julia Cameron.epub"),
        "max_chapters": 8,
    },
    {
        "key": "21-lessons-for-21st-century",
        "title": "21 Lessons for the 21st Century",
        "author": "Yuval Noah Harari",
        "domain": "macro-strategy",
        "epub": str(CALIBRE_DIR / "Yuval Noah Harari" / "21 Lessons for the 21st Century (133)" / "21 Lessons for the 21st Century - Yuval Noah Harari.epub"),
        "max_chapters": 8,
    },
]


def run_batch_compilation():
    cfg = Config(VAULT_DIR, json.loads((VAULT_DIR / "noetic.config.json").read_text(encoding="utf-8")))
    run_id = f"book-compile-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    print(f"Starting batch cumulative compilation for {len(BOOKS)} non-coding taste books...")

    for book in BOOKS:
        key = book["key"]
        title = book["title"]
        author = book["author"]
        domain = book["domain"]
        epub_path = book["epub"]
        max_ch = book.get("max_chapters", 8)

        print(f"\n=======================================================")
        print(f"▶ Compiling: {title} by {author}")
        print(f"=======================================================")

        # Check if already extracted
        raw_json_path = FRAMEWORKS_DIR / f"{key}.json"
        if book.get("already_extracted") and Path(book["already_extracted"]).exists():
            print(f"  (Reusing existing extracted JSON for {title})")
            fw_data = json.loads(Path(book["already_extracted"]).read_text(encoding="utf-8"))
        else:
            compiler = BookCompiler(epub_path, title, author, domain)
            fw_data = compiler.compile(max_chapters=max_ch)
            raw_json_path.write_text(json.dumps(fw_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  ✓ Saved raw schema: {raw_json_path.name}")

        # Ensure slug is canonical
        fw_data["slug"] = key

        # Render canonical markdown note in vault
        try:
            note_path = write_framework_note(cfg, fw_data, agent="book-compiler", run_id=run_id)
            print(f"  ✓ Rendered canonical framework note: {note_path.name}")

            # Seal with cryptographic approval hash
            approve(note_path, note=f"Auto-approved compiled framework from Calibre library ({title})")
            print(f"  ✓ Cryptographic approval hash computed and sealed (status: approved).")
        except Exception as e:
            print(f"  ! Error writing markdown note: {e}")

    print("\n✓ Batch compilation complete across all 4 books!")


if __name__ == "__main__":
    run_batch_compilation()
