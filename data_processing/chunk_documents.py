import sqlite3
from utils.config import DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP


def create_chunks_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            chunk_index INTEGER,
            chunk_text TEXT,
            title TEXT,
            source TEXT,
            source_type TEXT,
            url TEXT,
            company TEXT,
            category TEXT,
            word_count INTEGER,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
        """
    )


def clear_old_chunks(cursor):
    cursor.execute("DELETE FROM chunks")


def split_into_word_chunks(text, chunk_size=500, overlap=80):
    words = text.split()

    if len(words) <= chunk_size:
        return [" ".join(words)]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        if len(chunk_words) > 30:
            chunks.append(chunk_text)

        start = end - overlap

        if start < 0:
            start = 0

        if start >= len(words):
            break

    return chunks


def chunk_documents():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    create_chunks_table(cursor)
    clear_old_chunks(cursor)

    cursor.execute(
        """
        SELECT id, title, source, source_type, url, company, category, content
        FROM documents
        WHERE content IS NOT NULL
        AND LENGTH(content) > 0
        """
    )

    documents = cursor.fetchall()

    print("Starting document chunking...")
    print(f"Documents found: {len(documents)}")
    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Chunk overlap: {CHUNK_OVERLAP}")

    total_chunks = 0

    for doc in documents:
        document_id = doc["id"]
        title = doc["title"]
        source = doc["source"]
        source_type = doc["source_type"]
        url = doc["url"]
        company = doc["company"]
        category = doc["category"]
        content = doc["content"]

        chunks = split_into_word_chunks(
            content,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )

        for index, chunk_text in enumerate(chunks):
            word_count = len(chunk_text.split())

            cursor.execute(
                """
                INSERT INTO chunks (
                    document_id,
                    chunk_index,
                    chunk_text,
                    title,
                    source,
                    source_type,
                    url,
                    company,
                    category,
                    word_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    index,
                    chunk_text,
                    title,
                    source,
                    source_type,
                    url,
                    company,
                    category,
                    word_count
                )
            )

            total_chunks += 1

    conn.commit()
    conn.close()

    print("\nChunking completed.")
    print(f"Total chunks created: {total_chunks}")


if __name__ == "__main__":
    chunk_documents()