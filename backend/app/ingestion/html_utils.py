from __future__ import annotations

import re
from bs4 import BeautifulSoup


NOISE_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "img",
    "picture",
    "video",
    "audio",
    "iframe",
    "form",
    "button",
    "input",
    "footer",
    "nav",
    "aside",
}


def strip_noise(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    for tag in soup.find_all(attrs={"aria-hidden": "true"}):
        tag.decompose()

    for tag in soup.find_all(class_=True):
        classes = " ".join(tag.get("class", [])).lower()
        if any(
            word in classes
            for word in [
                "nav",
                "menu",
                "footer",
                "header",
                "sidebar",
                "breadcrumb",
                "share",
                "social",
                "cookie",
                "popup",
                "modal",
                "advert",
                "ad-",
            ]
        ):
            tag.decompose()


def pick_main_container(soup: BeautifulSoup):
    candidates = []

    semantic_candidates = soup.select("main, article, [role='main']")
    for node in semantic_candidates:
        text = node.get_text(" ", strip=True)
        candidates.append((len(text), node))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    block_candidates = soup.find_all(["div", "section"])
    scored = []
    for node in block_candidates:
        text = node.get_text(" ", strip=True)
        score = len(text)
        if score > 300:
            scored.append((score, node))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    return soup.body or soup


def extract_text_blocks_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    strip_noise(soup)

    container = pick_main_container(soup)
    if container is None:
        return []

    blocks: list[str] = []

    for node in container.find_all(["h1", "h2", "h3", "h4", "p", "li", "div"]):
        text = node.get_text(" ", strip=True)
        if not text:
            continue

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 2:
            continue

        blocks.append(text)

    deduped: list[str] = []
    seen = set()

    for block in blocks:
        key = block.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(block)

    return deduped


def html_to_readable_text(html: str) -> str:
    blocks = extract_text_blocks_from_html(html)
    return "\n\n".join(blocks).strip()
