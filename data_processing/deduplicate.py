import sqlite3
import pandas as pd
import re
from utils.config import DB_PATH, PROCESSED_DIR


def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()


def backup_documents_before_dedup():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM documents", conn)
    conn.close()

    backup_path = PROCESSED_DIR / "documents_before_dedup.csv"
    df.to_csv(backup_path, index=False, encoding="utf-8")

    print(f"Backup exported to: {backup_path}")


def remove_duplicates():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM documents ORDER BY word_count DESC")
    documents = cursor.fetchall()

    print("Starting duplicate removal...")
    print(f"Documents before deduplication: {len(documents)}")

    seen_titles = set()
    seen_content_starts = set()
    duplicate_ids = []

    for doc in documents:
        document_id = doc["id"]
        title = doc["title"]
        content = doc["content"] or ""

        normalized_title = normalize_text(title)

        # Use first 400 characters as a rough content fingerprint
        normalized_content_start = normalize_text(content[:400])

        is_duplicate = False

        if normalized_title in seen_titles:
            is_duplicate = True

        if normalized_content_start in seen_content_starts:
            is_duplicate = True

        if is_duplicate:
            duplicate_ids.append(document_id)
        else:
            seen_titles.add(normalized_title)
            seen_content_starts.add(normalized_content_start)

    for duplicate_id in duplicate_ids:
        cursor.execute("DELETE FROM documents WHERE id = ?", (duplicate_id,))

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM documents")
    after_count = cursor.fetchone()[0]

    conn.close()

    print("\nDuplicate removal completed.")
    print(f"Duplicates removed: {len(duplicate_ids)}")
    print(f"Documents after deduplication: {after_count}")


if __name__ == "__main__":
    backup_documents_before_dedup()
    remove_duplicates()