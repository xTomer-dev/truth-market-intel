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

    body = soup.body or soup
    return body


def extract_text_blocks_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    strip_noise(soup)

    container = pick_main_container(soup)
    if container is None:
        return []

    blocks: list[str] = []

    primary_nodes = container.find_all(["h1", "h2", "h3", "h4", "p", "li"])
    fallback_nodes = container.find_all(["div"])

    nodes = primary_nodes if len(primary_nodes) >= 10 else primary_nodes + fallback_nodes

    for node in nodes:
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

    if not blocks:
        return ""

    text = "\n\n".join(blocks).strip()
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text
