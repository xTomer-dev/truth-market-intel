import re


def split_speaker_blocks(text: str):
    pattern = r"\n([A-Z][A-Za-z .'-]+):"

    parts = re.split(pattern, text)

    blocks = []

    if len(parts) < 2:
        return []

    for i in range(1, len(parts), 2):
        speaker = parts[i].strip()
        speech = parts[i + 1].strip()

        blocks.append({
            "speaker": speaker,
            "text": speech
        })

    return blocks
