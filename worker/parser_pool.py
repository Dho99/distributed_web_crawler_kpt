from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from shared.urlnorm import normalize_url

SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {
    "p",
    "div",
    "br",
    "li",
    "tr",
    "h1",
    "h2",
    "h3",
    "h4",
    "section",
    "article",
    "header",
    "footer",
}
_WS = re.compile(r"\s+")


class _Extractor(HTMLParser):
    def __init__(self, base_url: str, max_links: int) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.max_links = max_links
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self._seen: set[str] = set()
        self._skip_depth = 0
        self._in_title = False
        self._in_body = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        name = tag.lower()
        if name in SKIP_TAGS:
            self._skip_depth += 1
            return
        if name == "title":
            self._in_title = True
        if name == "body":
            self._in_body = True
        if name in BLOCK_TAGS:
            self.text_parts.append("\n")
        if name == "a":
            href = dict(attrs).get("href")
            if href and len(self.links) < self.max_links:
                absolute = normalize_url(urljoin(self.base_url, href))
                if absolute and absolute not in self._seen:
                    self._seen.add(absolute)
                    self.links.append(absolute)

    def handle_endtag(self, tag: str) -> None:
        name = tag.lower()
        if name in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if name == "title":
            self._in_title = False
        if name in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = _WS.sub(" ", data).strip()
        if not cleaned:
            return
        if self._in_title:
            self.title_parts.append(cleaned)
        else:
            self.text_parts.append(cleaned + " ")


def parse_document(payload: dict) -> dict:
    """CPU-bound HTML parsing executed inside the worker process pool."""
    html = payload.get("html") or ""
    base_url = payload.get("final_url") or payload.get("url") or ""
    max_links = int(payload.get("max_links") or 50)

    extractor = _Extractor(base_url, max_links)
    try:
        extractor.feed(html)
        extractor.close()
    except Exception:  # noqa: BLE001 - malformed HTML must not kill the pool worker
        pass

    title = _WS.sub(" ", " ".join(extractor.title_parts)).strip()[:300]
    text = _WS.sub(" ", " ".join(extractor.text_parts)).strip()
    if len(text) > 20_000:
        text = text[:20_000]
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    return {
        "url": payload.get("url", ""),
        "final_url": base_url,
        "title": title,
        "text": text,
        "links": extractor.links,
        "content_hash": digest,
    }
