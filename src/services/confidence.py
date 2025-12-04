def compute_confidence(full_text):
    if not full_text or not full_text.pages:
        return None

    confidences = []
    for page in full_text.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    # word.confidence is a float between 0 and 1
                    confidences.append(word.confidence)

    if not confidences:
        return None

    return round(sum(confidences) / len(confidences), 3)
