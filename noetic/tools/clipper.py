"""Tools layer: Web Clipper.

A pure, stateless Tool for clipping web articles, documentation, and threads
into clean structured data and Noetic Knowledge Base signal notes.

Tools rule: plain functions with no control flow, swappable, no persistent state.
Outputs clean Markdown notes ready for `02-signals/web/` or `/ingest`.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import urllib.request
import urllib.parse
from typing import Any


def clean_html_to_markdown(html_content: str) -> str:
    """Basic stateless converter removing scripts/styles and converting tags to readable text."""
    # Remove script and style elements
    text = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Convert headings
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n# \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n## \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n### \1\n", text, flags=re.IGNORECASE)
    # Convert links
    text = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE)
    # Convert paragraphs and breaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode basic entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_metadata(html_content: str, default_url: str = "") -> dict[str, str]:
    """Extract page title, description, and author from HTML meta tags."""
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Untitled Clip"

    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
    desc = desc_match.group(1).strip() if desc_match else ""

    author_match = re.search(r'<meta[^>]*name=["\']author["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
    author = author_match.group(1).strip() if author_match else "Unknown"

    return {
        "title": title,
        "description": desc,
        "author": author,
        "url": default_url,
    }


def parse_clip(html_content: str, url: str = "", custom_title: str | None = None) -> dict[str, Any]:
    """Parse raw HTML content into a structured clip object."""
    meta = extract_metadata(html_content, default_url=url)
    if custom_title:
        meta["title"] = custom_title
    
    clean_text = clean_html_to_markdown(html_content)
    
    return {
        "title": meta["title"],
        "url": url,
        "author": meta["author"],
        "description": meta["description"],
        "content": clean_text,
        "clipped_at": datetime.now().isoformat(),
    }


def clip_url(url: str, timeout: int = 15, user_agent: str | None = None) -> dict[str, Any]:
    """Statelessly fetch a webpage and return a structured clip."""
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Noetic-Clipper/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        html_bytes = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"
        html_text = html_bytes.decode(encoding, errors="replace")
    
    return parse_clip(html_text, url=url)


def format_as_signal_note(clip: dict[str, Any], tags: list[str] | None = None) -> str:
    """Format a clip into an Noetic Knowledge Base markdown signal note."""
    tag_list = tags or ["signal", "web-clip"]
    tag_str = " ".join(f"#{t.strip('#')}" for t in tag_list)
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "---",
        "author: web-clipper",
        f"source_url: '{clip.get('url', '')}'",
        f"clipped_at: {clip.get('clipped_at', today)}",
        "status: raw",
        "tags:",
    ]
    for t in tag_list:
        lines.append(f"  - {t.strip('#')}")
    lines.extend([
        "---",
        f"> [!NOTE] Clipped via Noetic Web Clipper Tool. Raw signal awaiting discernment or `/ingest`.",
        "",
        f"# {clip.get('title', 'Untitled')}",
        "",
        f"- **Source:** {clip.get('url', 'N/A')}",
        f"- **Author:** {clip.get('author', 'Unknown')}",
        f"- **Description:** {clip.get('description', 'No description')}",
        f"- **Tags:** {tag_str}",
        "",
        "---",
        "",
        "## Content",
        "",
        clip.get("content", ""),
        "",
    ])
    return "\n".join(lines)
