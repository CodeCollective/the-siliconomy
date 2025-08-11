#!/usr/bin/env python3
import sys, os, re
import requests
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse
from datetime import datetime

# Optional: better "main content" detection if installed: pip install readability-lxml lxml
try:
    from readability import Document  # type: ignore
    HAVE_READABILITY = True
except Exception:
    HAVE_READABILITY = False

BLOCK_TAGS = {
    "article","section","nav","aside","header","footer","main",
    "p","div","li","ul","ol","blockquote","pre","figure","figcaption",
    "table","thead","tbody","tr","td","th",
    "h1","h2","h3","h4","h5","h6"
}

DROP_TAGS = {"script","style","noscript","template","svg","canvas","iframe","form","input"}

def fetch(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TextExtractor/1.0; +https://example.com/bot)"
    }
    r = requests.get(url, headers=headers, timeout=25)
    # Use server-provided encoding; if missing, lean on requests’ guess
    if not r.encoding or r.encoding.lower() == "ISO-8859-1".lower():
        r.encoding = r.apparent_encoding or "utf-8"
    r.raise_for_status()
    return r.text

def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml") if BeautifulSoup is not None else BeautifulSoup(html, "html.parser")

def clean_dom(soup: BeautifulSoup) -> None:
    # Remove junk containers
    for t in soup.find_all(DROP_TAGS):
        t.decompose()
    # Convert <br> to line breaks we’ll respect inside paragraphs
    for br in soup.find_all("br"):
        br.replace_with("\n")

def extract_main_html(html: str) -> str:
    if not HAVE_READABILITY:
        return html
    try:
        doc = Document(html)
        return doc.summary(html_partial=True)  # returns an <article>-ish HTML
    except Exception:
        return html

def node_to_paragraphs(node) -> list[str]:
    """
    Walks the DOM and returns a list of clean paragraphs,
    keeping block-level boundaries and avoiding choppy mid-sentence breaks.
    """
    paras = []

    def emit(text: str):
        # Collapse internal whitespace, preserve intentional linebreaks inside pre/code
        text = re.sub(r"[ \t\f\v]+", " ", text)
        text = re.sub(r"\s*\n\s*", "\n", text)
        text = text.strip()
        if text:
            paras.append(text)

    def walk(el):
        # If it's a string node:
        if isinstance(el, NavigableString):
            return str(el)

        # If it's a block element, gather text from children as one unit
        name = el.name.lower() if el.name else ""
        if name in BLOCK_TAGS:
            buf = []
            for child in el.children:
                buf.append(walk(child))
            text = " ".join(s for s in buf if s is not None)
            # For <pre> and code-like blocks, respect internal newlines more
            if name in {"pre"}:
                text = re.sub(r"\r\n?", "\n", el.get_text())
            emit(text)
            return None  # we already emitted as a paragraph

        # Inline or unknown: concatenate children
        buf = []
        for child in el.children:
            buf.append(walk(child))
        return " ".join(s for s in buf if s is not None)

    walk(node)
    return paras

def html_to_text(html: str) -> str:
    soup = soup_from_html(html)
    clean_dom(soup)

    # Prefer article/main if present, else body
    root = soup.find(["article","main"]) or soup.body or soup
    paragraphs = extract_from_root(root)

    # Normalize paragraph spacing
    text = "\n\n".join(paragraphs)
    # Remove 3+ blank lines -> 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_from_root(root) -> list[str]:
    # Collect paragraphs from headings, paragraphs, list items, tables, etc.
    collected = []
    # If the root is tiny, just do a whole-walk
    whole = node_to_paragraphs(root)
    # Heuristic: filter out very short nav-like lines
    for p in whole:
        # Drop obvious navigation crumbs
        if len(p) < 2:
            continue
        if re.search(r"^\s*(©|copyright)\b", p, re.I):
            continue
        collected.append(p)
    return collected

def slugify(text: str, fallback: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback

def make_filename(url: str, soup_title: str | None) -> str:
    domain = urlparse(url).netloc.replace(":", "_")
    title_slug = slugify(soup_title or "", domain)
    date = datetime.now().strftime("%Y%m%d")
    return f"{title_slug}-{date}.txt"

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <URL> [OUTPUT.txt]")
        sys.exit(1)

    url = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else None

    html = fetch(url)

    # Try to reduce boilerplate by using Readability if available
    main_html = extract_main_html(html)

    # We still want the page title for filename
    title_soup = soup_from_html(html)
    page_title = (title_soup.title.string if title_soup.title else "").strip() if title_soup else ""

    text = html_to_text(main_html)

    if not out_path:
        out_path = make_filename(url, page_title)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text + "\n")

    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
