import re
import sqlite3
from utils.config import DB_PATH


def clean_text(text):
    if text is None:
        return ""

    text = str(text)

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", " ", text)

    # Remove email-like patterns
    text = re.sub(r"\S+@\S+", " ", text)

    # Remove repeated whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove repeated punctuation
    text = re.sub(r"([.!?]){2,}", r"\1", text)

    # Remove very strange characters but keep normal punctuation
    text = re.sub(r"[^A-Za-z0-9.,!?;:'\"()/%€$£+\-\s]", " ", text)

    # Final whitespace clean
    text = re.sub(r"\s+", " ", text).strip()

    return text


def count_words(text):
    if not text:
        return 0
    return len(text.split())


def clean_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content FROM documents")
    documents = cursor.fetchall()

    print("Starting text cleaning...")
    print(f"Total documents found: {len(documents)}")

    cleaned_count = 0
    skipped_count = 0

    for doc in documents:
        document_id = doc["id"]
        title = doc["title"]
        content = doc["content"]

        cleaned_content = clean_text(content)
        word_count = count_words(cleaned_content)

        if word_count < 50:
            skipped_count += 1
            print(f"Skipped short document ID {document_id}: {title}")
            continue

        cursor.execute(
            """
            UPDATE documents
            SET content = ?, word_count = ?
            WHERE id = ?
            """,
            (cleaned_content, word_count, document_id)
        )

        cleaned_count += 1

    conn.commit()
    conn.close()

    print("\nText cleaning completed.")
    print(f"Cleaned documents: {cleaned_count}")
    print(f"Skipped short documents: {skipped_count}")


if __name__ == "__main__":
    clean_documents()