import re


def clean_text(text: str) -> str:
    # Remove control characters
    text = re.sub(r'[\x00-\x1F\x7F]+', '', text)

    # Collapse multiple line breaks to max 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Collapse multiple spaces/tabs
    text = re.sub(r'[ \t]+', ' ', text)

    # Strip leading/trailing whitespace on each line
    text = '\n'.join([line.strip() for line in text.split('\n')])

    # Strip overall text
    return text.strip()

