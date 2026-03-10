import re


def split_speaker_blocks(text: str) -> list[dict]:
    pattern = r"\n([A-Z][A-Za-z .'\-]+):"
    parts = re.split(pattern, "\n" + text.strip())

    blocks: list[dict] = []

    if len(parts) < 3:
        return blocks

    for i in range(1, len(parts), 2):
        speaker = parts[i].strip()
        body = parts[i + 1].strip()

        if not body:
            continue

        blocks.append(
            {
                "speaker": speaker,
                "text": body,
            }
        )

    return blocks
