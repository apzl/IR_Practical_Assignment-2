import urllib.request
from document import Document

# Structural/front-matter headings that may appear as pseudo-"documents" before
# the actual stories in a Project Gutenberg book. They are skipped while
# auto-detecting where the real content region begins, so the loader stays
# robust to source files that grow extra front matter over time.
FRONT_MATTER_HEADINGS = frozenset({
    "PREFACE",
    "INTRODUCTION",
    "CONTENTS",
    "INDEX",
    "ILLUSTRATIONS",
    "LIFE OF AESOP",
    "AESOP'S FABLES",
    "AESOP’S FABLES",  # variant with a typographic apostrophe
})


def _is_front_matter(title):
    """True if a parsed title is a structural heading rather than a real story."""
    return title.strip().upper() in FRONT_MATTER_HEADINGS


def load_collection_from_url(url, search_pattern, start_line, end_line, author, origin):
    """Download a .txt file from a URL and extract Document objects using a regex pattern.

    The pattern must have two capture groups: group 1 = title, group 2 = body text.
    Line numbers are 1-based and inclusive. Leading front-matter headings (table of
    contents, preface, etc.) are skipped so the first returned document is the first
    real story regardless of how much front matter the source file contains.
    """
    with urllib.request.urlopen(url) as response:
        raw_bytes = response.read()

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1")

    lines = content.splitlines()
    selected = lines[start_line - 1: end_line] if end_line is not None else lines[start_line - 1:]
    text = "\n".join(selected)

    matches = search_pattern.findall(text)

    # Auto-detect the start of the story region: drop leading front-matter
    # headings so document #0 is the first actual story.
    start = 0
    while start < len(matches) and _is_front_matter(matches[start][0]):
        start += 1

    documents = []
    for doc_id, (title, body) in enumerate(matches[start:]):
        raw_text = " ".join(body.split())  # collapse all whitespace to single spaces
        documents.append(Document(
            document_id=doc_id,
            title=title.strip(),
            raw_text=raw_text,
            terms=raw_text.split(),
            author=author,
            origin=origin,
        ))

    return documents


def linear_boolean_search(term, collection, stopword_filtered=False):
    """Return a list of (score, doc) tuples for every document in the collection.

    Score is 1 if the term is found, 0 otherwise. Matching is case-insensitive.
    When stopword_filtered is True, the search uses each document's filtered_terms
    instead of its full term list.
    """
    term_lower = term.lower()
    results = []
    for doc in collection:
        if stopword_filtered:
            # filtered_terms can be either a bound method or a plain list
            # (tests set it as a list attribute directly on the instance)
            ft = doc.filtered_terms
            terms = ft if isinstance(ft, list) else ft()
        else:
            terms = doc.terms

        score = 1 if any(t.lower() == term_lower for t in terms) else 0
        results.append((score, doc))

    return results


def remove_stop_words(terms, stopwords):
    """Filter stop words from a term list (case-insensitive) and return lowercased terms.

    Parameters:
        terms: list of strings
        stopwords: set of lowercase stop word strings
    """
    return [t.lower() for t in terms if t.lower() not in stopwords]


def remove_stop_words_by_frequency(terms, collection, low_freq=0.1, high_freq=0.9):
    """Remove stop words based on Crouch's document-frequency method.

    A term is treated as a stop word if it appears in:
      - >= high_freq fraction of documents (too common), or
      - <= low_freq  fraction of documents (too rare).

    Parameters:
        terms: list of strings to filter
        collection: list of Document objects used as the reference corpus
        low_freq: lower frequency threshold (inclusive)
        high_freq: upper frequency threshold (inclusive)
    """
    n = len(collection)
    if n == 0:
        return list(terms)

    # Count how many documents contain each term (case-insensitive)
    doc_freq: dict[str, int] = {}
    for doc in collection:
        for term in set(t.lower() for t in doc.terms):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    # Identify stop words that fall outside the acceptable frequency band
    stop_words = {
        term for term, freq in doc_freq.items()
        if (freq / n) >= high_freq or (freq / n) <= low_freq
    }

    return [t for t in terms if t.lower() not in stop_words]
