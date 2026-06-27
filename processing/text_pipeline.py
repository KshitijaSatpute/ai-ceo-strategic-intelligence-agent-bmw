import argparse
import re
import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ai_ceo.db"


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def choose_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def create_chunks(text, chunk_size=1000, overlap=150):
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": min(end, len(text)),
                "word_count": len(chunk_text.split())
            })

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def get_table_columns(conn, table_name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))

    if cursor.fetchone() is None:
        return []

    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()

    return [row[1] for row in rows]


def get_document_count(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='documents'
    """)

    if cursor.fetchone() is None:
        return 0

    cursor.execute("SELECT COUNT(*) FROM documents")
    return cursor.fetchone()[0]


def get_chunk_count(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='chunks'
    """)

    if cursor.fetchone() is None:
        return 0

    cursor.execute("SELECT COUNT(*) FROM chunks")
    return cursor.fetchone()[0]


def show_pipeline_status():
    if not DB_PATH.exists():
        print("Database not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)

    document_count = get_document_count(conn)
    chunk_count = get_chunk_count(conn)

    print("Text Pipeline Status")
    print("Database:", DB_PATH)
    print("Documents:", document_count)
    print("Chunks:", chunk_count)

    conn.close()


def create_chunks_table(conn):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS chunks")

    cursor.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            chunk_text TEXT,
            text TEXT,
            title TEXT,
            source TEXT,
            category TEXT,
            url TEXT,
            published_date TEXT,
            char_start INTEGER,
            char_end INTEGER,
            word_count INTEGER,
            created_at TEXT
        )
    """)

    conn.commit()


def load_documents(conn):
    columns = get_table_columns(conn, "documents")

    id_column = choose_column(columns, ["id", "document_id"])
    text_column = choose_column(
        columns,
        [
            "clean_text",
            "content",
            "text",
            "article_text",
            "raw_text",
            "full_text",
            "body",
            "summary"
        ]
    )
    title_column = choose_column(columns, ["title", "headline", "name"])
    source_column = choose_column(columns, ["source", "publisher", "source_name"])
    category_column = choose_column(columns, ["category", "source_type", "topic"])
    url_column = choose_column(columns, ["url", "link"])
    date_column = choose_column(
        columns,
        ["published_date", "published_at", "collected_at", "created_at", "date"]
    )

    if id_column is None:
        raise ValueError("No document id column found in documents table.")

    if text_column is None:
        raise ValueError("No text/content column found in documents table.")

    selected_columns = [id_column, text_column]

    for column in [title_column, source_column, category_column, url_column, date_column]:
        if column and column not in selected_columns:
            selected_columns.append(column)

    query = f"""
        SELECT {", ".join(selected_columns)}
        FROM documents
        WHERE {text_column} IS NOT NULL
    """

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

    documents = []

    for row in rows:
        row_dict = dict(zip(selected_columns, row))

        documents.append({
            "document_id": row_dict.get(id_column),
            "text": row_dict.get(text_column, ""),
            "title": row_dict.get(title_column, "Untitled") if title_column else "Untitled",
            "source": row_dict.get(source_column, "Unknown") if source_column else "Unknown",
            "category": row_dict.get(category_column, "Unknown") if category_column else "Unknown",
            "url": row_dict.get(url_column, "") if url_column else "",
            "published_date": row_dict.get(date_column, "") if date_column else ""
        })

    return documents


def run_text_pipeline(chunk_size=1000, overlap=150):
    if not DB_PATH.exists():
        print("Database not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    document_count = get_document_count(conn)

    if document_count == 0:
        print("No documents found. Run data collection first.")
        conn.close()
        return

    documents = load_documents(conn)
    create_chunks_table(conn)

    seen_documents = set()
    total_chunks = 0
    processed_documents = 0
    skipped_duplicates = 0

    for document in documents:
        cleaned_text = clean_text(document["text"])

        if not cleaned_text:
            continue

        dedup_key = (
            clean_text(document["title"]).lower(),
            clean_text(document["source"]).lower(),
            cleaned_text[:300].lower()
        )

        if dedup_key in seen_documents:
            skipped_duplicates += 1
            continue

        seen_documents.add(dedup_key)

        chunks = create_chunks(
            cleaned_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk_index, chunk in enumerate(chunks):
            cursor.execute("""
                INSERT INTO chunks (
                    document_id,
                    chunk_index,
                    chunk_text,
                    text,
                    title,
                    source,
                    category,
                    url,
                    published_date,
                    char_start,
                    char_end,
                    word_count,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document["document_id"],
                chunk_index,
                chunk["text"],
                chunk["text"],
                document["title"],
                document["source"],
                document["category"],
                document["url"],
                document["published_date"],
                chunk["start"],
                chunk["end"],
                chunk["word_count"],
                datetime.now().isoformat(timespec="seconds")
            ))

            total_chunks += 1

        processed_documents += 1

    conn.commit()
    conn.close()

    print("Text preprocessing and chunking completed.")
    print("Documents found:", document_count)
    print("Documents processed:", processed_documents)
    print("Duplicate documents skipped:", skipped_duplicates)
    print("Chunks created:", total_chunks)
    print("Chunk size:", chunk_size)
    print("Chunk overlap:", overlap)


def show_sample_chunks(limit=5):
    if not DB_PATH.exists():
        print("Database not found:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    columns = get_table_columns(conn, "chunks")

    if not columns:
        print("Chunks table not found.")
        conn.close()
        return

    id_column = choose_column(columns, ["chunk_id", "id"])
    text_column = choose_column(columns, ["chunk_text", "text", "content"])
    title_column = choose_column(columns, ["title", "headline", "name"])
    source_column = choose_column(columns, ["source", "publisher", "source_name"])
    category_column = choose_column(columns, ["category", "source_type", "topic"])
    word_count_column = choose_column(columns, ["word_count", "words"])

    selected_columns = []

    for column in [
        id_column,
        title_column,
        source_column,
        category_column,
        word_count_column,
        text_column
    ]:
        if column and column not in selected_columns:
            selected_columns.append(column)

    if not selected_columns:
        print("No readable columns found in chunks table.")
        conn.close()
        return

    query = f"""
        SELECT {", ".join(selected_columns)}
        FROM chunks
        LIMIT ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.close()

    print("Sample chunks:")

    for row in rows:
        row_dict = dict(zip(selected_columns, row))

        print("-" * 80)

        if id_column:
            print("Chunk ID:", row_dict.get(id_column))

        if title_column:
            print("Title:", row_dict.get(title_column))

        if source_column:
            print("Source:", row_dict.get(source_column))

        if category_column:
            print("Category:", row_dict.get(category_column))

        if word_count_column:
            print("Word count:", row_dict.get(word_count_column))

        if text_column:
            text_preview = clean_text(row_dict.get(text_column, ""))[:250]
            print("Text:", text_preview)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Text preprocessing and chunking pipeline"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current document and chunk counts"
    )

    parser.add_argument(
        "--sample",
        action="store_true",
        help="Show sample chunks"
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild chunks from documents"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Chunk size in characters"
    )

    parser.add_argument(
        "--overlap",
        type=int,
        default=150,
        help="Chunk overlap in characters"
    )

    args = parser.parse_args()

    if args.status:
        show_pipeline_status()
    elif args.sample:
        show_sample_chunks()
    elif args.rebuild:
        run_text_pipeline(
            chunk_size=args.chunk_size,
            overlap=args.overlap
        )
    else:
        show_pipeline_status()