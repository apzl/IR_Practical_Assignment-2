"""Simple text-based UI for the Information Retrieval system."""

import os
import re

from document import Document
from ir_module import (
    load_collection_from_url,
    linear_boolean_search,
    remove_stop_words,
    remove_stop_words_by_frequency,
)

# Holds the currently loaded document collection
collection: list[Document] = []


# ---------------------------------------------------------------------------
# Preset source configurations
# ---------------------------------------------------------------------------

SOURCES = {
    "1": {
        "label": "Aesop's Fables",
        "url": "https://www.gutenberg.org/files/21/21-0.txt",
        "author": "Aesop",
        "origin": "Aesop's Fables",
        "start_line": 39,
        "end_line": 4777,
        "pattern": re.compile(
            r"([^\n]+)\n\n(.*?)(?=\n{5}(?=[^\n]+\n\n)|$)", re.DOTALL
        ),
    },
    "2": {
        "label": "Grimm's Fairy Tales",
        "url": "https://www.gutenberg.org/files/2591/2591-0.txt",
        "author": "Jacob and Wilhelm Grimm",
        "origin": "Grimms' Fairy Tales",
        "start_line": 123,
        "end_line": 9239,
        "pattern": re.compile(
            r"([A-Z0-9 ,.'!?-]+)\n{3}(.*?)(?=\n{5}|$)", re.DOTALL
        ),
    },
}


# ---------------------------------------------------------------------------
# Menu handlers
# ---------------------------------------------------------------------------

def menu_load_collection():
    """Download and parse a story collection from a URL."""
    global collection

    print("\n--- Load Collection ---")
    print("Choose a preset source or enter a custom URL:")
    for key, src in SOURCES.items():
        print(f"  {key}. {src['label']}")
    print("  c. Custom URL")

    choice = input("Choice: ").strip().lower()

    if choice in SOURCES:
        src = SOURCES[choice]
        url = src["url"]
        author = src["author"]
        origin = src["origin"]
        start_line = src["start_line"]
        end_line = src["end_line"]
        pattern = src["pattern"]
    elif choice == "c":
        url = input("URL: ").strip()
        author = input("Author: ").strip()
        origin = input("Origin/Title: ").strip()
        start_line = int(input("Start line (1-based): ").strip())
        end_line_raw = input("End line (leave blank for EOF): ").strip()
        end_line = int(end_line_raw) if end_line_raw else None
        title_text_sep = input(
            "Title/text separator regex (leave blank for default '\\n\\n'): "
        ).strip() or r"\n\n"
        story_sep = input(
            "Story separator regex (leave blank for default '\\n{5}'): "
        ).strip() or r"\n{5}"
        pattern = re.compile(
            rf"([^\n]+){title_text_sep}(.*?)(?={story_sep}|$)", re.DOTALL
        )
    else:
        print("Invalid choice.")
        return

    print(f"\nDownloading from {url} …")
    try:
        collection = load_collection_from_url(
            url, pattern, start_line, end_line, author, origin
        )
        print(f"Loaded {len(collection)} documents.")
    except Exception as exc:
        print(f"Error loading collection: {exc}")


def menu_search():
    """Search for documents using a single Boolean keyword query."""
    if not collection:
        print("No collection loaded. Please load a collection first.")
        return

    print("\n--- Boolean Search ---")
    term = input("Enter search term: ").strip()
    if not term:
        print("Empty search term.")
        return

    use_filtered = input("Use stop-word filtered terms? (y/N): ").strip().lower() == "y"
    results = linear_boolean_search(term, collection, stopword_filtered=use_filtered)
    matching = [(score, doc) for score, doc in results if score == 1]

    print(f"\nFound {len(matching)} result(s) for '{term}':")
    for score, doc in matching:
        print(f"  [{doc.document_id}] {doc.title}")


def menu_apply_stopwords():
    """Apply stop word removal to the loaded collection."""
    if not collection:
        print("No collection loaded. Please load a collection first.")
        return

    print("\n--- Stop Word Removal ---")
    print("  1. List-based (load from file)")
    print("  2. Frequency-based (Crouch's method)")
    method = input("Method: ").strip()

    if method == "1":
        default_path = os.path.join("public_tests", "englishST.txt")
        path = input(f"Stop word file path [{default_path}]: ").strip() or default_path
        try:
            with open(path, "r", encoding="utf-8") as f:
                stopwords = set(line.strip().replace(" ", "") for line in f)
        except FileNotFoundError:
            print(f"File not found: {path}")
            return

        for doc in collection:
            doc._filtered_terms = remove_stop_words(doc.terms, stopwords)

        print(f"Applied list-based stop word removal to {len(collection)} documents.")

    elif method == "2":
        try:
            high = float(input("Common-frequency threshold (e.g. 0.9): ").strip())
            low = float(input("Rare-frequency threshold (e.g. 0.1): ").strip())
        except ValueError:
            print("Invalid threshold value.")
            return

        for doc in collection:
            doc._filtered_terms = remove_stop_words_by_frequency(
                doc.terms, collection, low_freq=low, high_freq=high
            )

        print(f"Applied frequency-based stop word removal to {len(collection)} documents.")
    else:
        print("Invalid choice.")


def menu_show_collection():
    """Display a summary of the loaded collection."""
    if not collection:
        print("No collection loaded.")
        return
    print(f"\n{len(collection)} documents loaded:")
    for doc in collection[:20]:
        print(f"  {doc}")
    if len(collection) > 20:
        print(f"  … and {len(collection) - 20} more.")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print("=== Information Retrieval System – PR02 ===")
    menu = {
        "1": ("Load collection from URL", menu_load_collection),
        "2": ("Search documents (Boolean)", menu_search),
        "3": ("Apply stop word removal", menu_apply_stopwords),
        "4": ("Show loaded collection", menu_show_collection),
        "q": ("Quit", None),
    }

    while True:
        print("\n--- Main Menu ---")
        for key, (label, _) in menu.items():
            print(f"  {key}. {label}")

        choice = input("Choice: ").strip().lower()
        if choice == "q":
            print("Goodbye.")
            break
        if choice in menu and menu[choice][1]:
            menu[choice][1]()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
