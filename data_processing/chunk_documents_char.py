import sqlite3
from datetime import datetime
from pathlib import Path
import shutil

from utils.config import DB_PATH


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MIN_CHUNK_LENGTH = 150


def get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def pick_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def clean_text_for_chunking(text):
    text = str(text)
    text = " ".join(text.split())
    return text.strip()


def create_character_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = clean_text_for_chunking(text)

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()

        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def main():
    db_path = Path(DB_PATH)

    backup_path = db_path.with_name(
        f"{db_path.stem}_backup_auto_before_char_chunking{db_path.suffix}"
    )

    shutil.copy2(db_path, backup_path)
    print(f"Database backup created: {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    document_columns = get_columns(cursor, "documents")
    chunk_columns = get_columns(cursor, "chunks")

    document_text_column = pick_column(
        document_columns,
        ["clean_text", "content", "text", "article_text", "full_text"]
    )

    chunk_text_column = pick_column(
        chunk_columns,
        ["chunk_text", "content", "text"]
    )

    if document_text_column is None:
        raise ValueError(
            "No document text column found. Expected one of: clean_text, content, text, article_text, full_text"
        )

    if chunk_text_column is None:
        raise ValueError(
            "No chunk text column found. Expected one of: chunk_text, content, text"
        )

    cursor.execute(
        f"""
        SELECT *
        FROM documents
        WHERE {document_text_column} IS NOT NULL
        AND TRIM({document_text_column}) != ''
        """
    )

    documents = cursor.fetchall()

    print(f"Documents found for chunking: {len(documents)}")

    cursor.execute("DELETE FROM chunks")

    total_chunks = 0

    for document in documents:
        article_text = document[document_text_column]
        chunks = create_character_chunks(article_text)

        for chunk_index, chunk in enumerate(chunks):
            values = {}

            def add_value(column_name, value):
                if column_name in chunk_columns:
                    values[column_name] = value

            if "id" in document_columns:
                add_value("document_id", document["id"])

            if "title" in document_columns:
                add_value("title", document["title"])

            if "source" in document_columns:
                add_value("source", document["source"])

            if "source_type" in document_columns:
                add_value("source_type", document["source_type"])

            if "company" in document_columns:
                add_value("company", document["company"])

            if "category" in document_columns:
                add_value("category", document["category"])

            if "url" in document_columns:
                add_value("url", document["url"])

            add_value(chunk_text_column, chunk)
            add_value("chunk_index", chunk_index)
            add_value("word_count", len(chunk.split()))
            add_value("char_count", len(chunk))
            add_value("created_at", datetime.now().isoformat(timespec="seconds"))

            columns = list(values.keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)

            cursor.execute(
                f"INSERT INTO chunks ({column_names}) VALUES ({placeholders})",
                [values[column] for column in columns]
            )

            total_chunks += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM chunks")
    final_chunk_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(word_count), MIN(word_count), MAX(word_count) FROM chunks")
    avg_words, min_words, max_words = cursor.fetchone()

    print("\nCharacter-based chunking completed.")
    print(f"Total chunks created: {final_chunk_count}")
    print(f"Average words per chunk: {avg_words:.2f}")
    print(f"Minimum words per chunk: {min_words}")
    print(f"Maximum words per chunk: {max_words}")
    print(f"Chunk size used: {CHUNK_SIZE} characters")
    print(f"Chunk overlap used: {CHUNK_OVERLAP} characters")

    conn.close()


if __name__ == "__main__":
    main()