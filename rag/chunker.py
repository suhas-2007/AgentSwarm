import re


def split_into_sentences(
    text: str
) -> list[str]:
    # split text by punctuation

    text = text.replace(
        "\n",
        " "
    )

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> list[str]:
    # chunks text into groups of sentences with overlap

    if chunk_size <= 0:

        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0 or overlap >= chunk_size:

        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    if not isinstance(text, str):

        raise TypeError(
            "text must be a string"
        )

    sentences = split_into_sentences(
        text
    )

    chunks = []

    current_sentences = []
    current_length = 0

    for sentence in sentences:

        sentence_length = len(
            sentence
        )

        separator_length = (
            1
            if current_sentences
            else 0
        )

        # fits in current chunk
        if (
            not current_sentences
            or current_length
            + separator_length
            + sentence_length
            <= chunk_size
        ):

            current_sentences.append(
                sentence
            )

            current_length += (
                separator_length
                + sentence_length
            )

            continue

        # save current chunk
        chunks.append(
            " ".join(
                current_sentences
            )
        )

        # carry over overlap sentences
        overlap_sentences = []
        overlap_length = 0

        for previous_sentence in reversed(
            current_sentences
        ):

            previous_length = len(
                previous_sentence
            )

            separator_length = (
                1
                if overlap_sentences
                else 0
            )

            candidate_length = (
                overlap_length
                + separator_length
                + previous_length
            )

            if (
                overlap_sentences
                and candidate_length > overlap
            ):
                break

            overlap_sentences.insert(
                0,
                previous_sentence
            )

            overlap_length = candidate_length

            if overlap_length >= overlap:
                break

        # trim overlap if too long
        while (
            overlap_sentences
            and (
                overlap_length
                + 1
                + sentence_length
                > chunk_size
            )
        ):

            removed_sentence = (
                overlap_sentences.pop(0)
            )

            overlap_length -= (
                len(removed_sentence)
                + (
                    1
                    if overlap_sentences
                    else 0
                )
            )

        current_sentences = (
            overlap_sentences
        )

        current_length = sum(
            len(item) + 1
            for item in current_sentences
        )

        if current_sentences:

            current_length -= 1

        # add next sentence
        separator_length = (
            1
            if current_sentences
            else 0
        )

        current_sentences.append(
            sentence
        )

        current_length += (
            separator_length
            + sentence_length
        )

    # last chunk
    if current_sentences:

        chunks.append(
            " ".join(
                current_sentences
            )
        )

    return chunks