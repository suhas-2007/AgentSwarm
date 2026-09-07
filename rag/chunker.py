import re


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into individual sentences.
    """

    text = text.replace("\n", " ")

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
    """
    Combine complete sentences into chunks.

    Each chunk targets approximately 500 characters.
    Approximately 100 characters of context are retained
    between neighboring chunks.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    sentences = split_into_sentences(text)

    chunks = []
    current_sentences = []
    current_length = 0

    for sentence in sentences:

        sentence_length = len(sentence)

        # Add the sentence to the current chunk
        # if it does not exceed the target size.
        if (
            not current_sentences
            or current_length + sentence_length + 1
            <= chunk_size
        ):
            current_sentences.append(sentence)
            current_length += sentence_length + 1

        else:
            # Save the current chunk.
            chunks.append(
                " ".join(current_sentences)
            )

            # Find sentences to carry into the next chunk.
            overlap_sentences = []
            overlap_length = 0

            for previous_sentence in reversed(
                current_sentences
            ):

                overlap_sentences.insert(
                    0,
                    previous_sentence
                )

                overlap_length += (
                    len(previous_sentence) + 1
                )

                if overlap_length >= overlap:
                    break

            current_sentences = overlap_sentences

            current_length = sum(
                len(item) + 1
                for item in current_sentences
            )

            # Add the new sentence.
            current_sentences.append(sentence)

            current_length += (
                len(sentence) + 1
            )

    # Store the final chunk.
    if current_sentences:
        chunks.append(
            " ".join(current_sentences)
        )

    return chunks