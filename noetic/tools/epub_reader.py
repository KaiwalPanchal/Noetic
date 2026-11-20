"""EPUB Book Reader and Semantic Chapter Unpacker.

Extracts structured chapters, table of contents, and clean plain text from EPUB
e-books natively using Python's standard zipfile and xml libraries.
"""

from __future__ import annotations

import html
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


def clean_html(raw_html: str) -> str:
    """Strips HTML tags and converts markup into clean, readable text."""
    # Remove script, style, head
    text = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Headings to markdown style
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.DOTALL | re.IGNORECASE)
    # Paragraphs and linebreaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class EpubReader:
    """Reads and parses EPUB containers, spine order, and chapter content."""

    def __init__(self, epub_path: Path | str):
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {self.epub_path}")

    def inspect_chapters(self) -> list[dict[str, Any]]:
        """Extracts ordered chapters with title, path, word count, and text body."""
        chapters = []
        with zipfile.ZipFile(self.epub_path, "r") as z:
            namelist = z.namelist()

            # 1. Locate rootfile from META-INF/container.xml
            opf_path = "OEBPS/content.opf"
            if "META-INF/container.xml" in namelist:
                c_xml = z.read("META-INF/container.xml").decode("utf-8", errors="replace")
                m = re.search(r'full-path=["\']([^"\']+)["\']', c_xml)
                if m:
                    opf_path = m.group(1)

            opf_dir = Path(opf_path).parent.as_posix()
            if opf_dir == ".":
                opf_dir = ""

            # 2. Parse OPF to get manifest and spine
            opf_content = z.read(opf_path).decode("utf-8", errors="replace")
            # Remove XML namespaces for easier regex/ET parsing
            clean_opf = re.sub(r'\sxmlns="[^"]+"', "", opf_content)
            root = ET.fromstring(clean_opf)

            # Map manifest items: id -> href
            manifest = {}
            for item in root.findall(".//manifest/item"):
                item_id = item.get("id")
                href = item.get("href")
                if item_id and href:
                    full_href = f"{opf_dir}/{href}".lstrip("/") if opf_dir else href
                    manifest[item_id] = full_href

            # Map spine itemrefs to ordered file paths
            spine_ids = [itemref.get("idref") for itemref in root.findall(".//spine/itemref")]
            spine_files = [manifest[sid] for sid in spine_ids if sid in manifest]

            # If spine empty, fallback to namelist html files
            if not spine_files:
                spine_files = sorted([f for f in namelist if f.endswith((".html", ".xhtml"))])

            # 3. Read chapter files in spine order
            for idx, file_key in enumerate(spine_files):
                if file_key not in namelist:
                    # try resolving relative
                    candidates = [f for f in namelist if f.endswith(Path(file_key).name)]
                    if candidates:
                        file_key = candidates[0]
                    else:
                        continue

                raw_bytes = z.read(file_key)
                text_content = raw_bytes.decode("utf-8", errors="replace")
                plain_body = clean_html(text_content)

                # Skip trivial/empty files (covers, copyright stubs < 100 words)
                word_count = len(plain_body.split())
                if word_count < 80:
                    continue

                # Extract first heading or fallback title
                title_match = re.search(r"^#+\s+(.+)$", plain_body, re.MULTILINE)
                if title_match:
                    chapter_title = title_match.group(1).strip()
                else:
                    first_line = plain_body.splitlines()[0] if plain_body.splitlines() else f"Chapter {idx+1}"
                    chapter_title = first_line[:60].strip()

                chapters.append({
                    "index": len(chapters) + 1,
                    "title": chapter_title,
                    "file": file_key,
                    "word_count": word_count,
                    "text": plain_body,
                })

        return chapters


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        reader = EpubReader(test_path)
        chaps = reader.inspect_chapters()
        print(f"Extracted {len(chaps)} valid chapters from {Path(test_path).name}")
        for c in chaps[:10]:
            print(f"  [{c['index']:02d}] {c['title'][:50]:<50} ({c['word_count']} words)")
    else:
        print("Usage: python epub_reader.py <path_to_epub>")
