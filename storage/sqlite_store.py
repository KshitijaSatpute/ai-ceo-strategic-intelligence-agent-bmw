import sqlite3
from datetime import datetime
from utils.config import DB_PATH, DATA_DIR


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        source TEXT,
        source_type TEXT,
        url TEXT UNIQUE,
        published_date TEXT,
        collected_at TEXT,
        company TEXT,
        category TEXT,
        content TEXT,
        word_count INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        chunk_index INTEGER,
        chunk_text TEXT,
        source TEXT,
        url TEXT,
        company TEXT,
        category TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        strategic_action TEXT,
        priority TEXT,
        expected_impact TEXT,
        risk_level TEXT,
        confidence_score REAL,
        reasoning TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_document(title, source, source_type, url, published_date, company, category, content):
    conn = get_connection()
    cursor = conn.cursor()

    word_count = len(content.split()) if content else 0

    try:
        cursor.execute("""
        INSERT INTO documents (
            title, source, source_type, url, published_date,
            collected_at, company, category, content, word_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            source,
            source_type,
            url,
            published_date,
            datetime.now().isoformat(timespec="seconds"),
            company,
            category,
            content,
            word_count
        ))

        conn.commit()
        inserted = True

    except sqlite3.IntegrityError:
        inserted = False

    conn.close()
    return inserted


def update_document_content(document_id, cleaned_content):
    conn = get_connection()
    cursor = conn.cursor()

    word_count = len(cleaned_content.split()) if cleaned_content else 0

    cursor.execute("""
    UPDATE documents
    SET content = ?, word_count = ?
    WHERE id = ?
    """, (cleaned_content, word_count, document_id))

    conn.commit()
    conn.close()


def get_document_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT source) FROM documents")
    unique_publishers = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(collected_at) FROM documents")
    last_update = cursor.fetchone()[0]

    conn.close()

    return {
        "total_documents": total_docs,
        "unique_publishers": unique_publishers,
        "last_update": last_update or "Not collected yet"
    }


def get_source_type_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT source_type) FROM documents")
    source_type_count = cursor.fetchone()[0]

    conn.close()
    return source_type_count


def get_recent_documents(limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT title, source, source_type, company, category, url, word_count
    FROM documents
    ORDER BY collected_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    documents = []

    for row in rows:
        documents.append({
            "title": row[0],
            "source": row[1],
            "source_type": row[2],
            "company": row[3],
            "category": row[4],
            "url": row[5],
            "word_count": row[6]
        })

    return documents


def get_source_type_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT source_type, COUNT(*) AS count
    FROM documents
    GROUP BY source_type
    ORDER BY count DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"source_type": row[0], "count": row[1]} for row in rows]


def get_category_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT category, COUNT(*) AS count
    FROM documents
    GROUP BY category
    ORDER BY count DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [{"category": row[0], "count": row[1]} for row in rows]


def get_all_documents():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, source, source_type, url, published_date, company, category, content, word_count
    FROM documents
    ORDER BY id
    """)

    rows = cursor.fetchall()
    conn.close()

    documents = []

    for row in rows:
        documents.append({
            "id": row[0],
            "title": row[1],
            "source": row[2],
            "source_type": row[3],
            "url": row[4],
            "published_date": row[5],
            "company": row[6],
            "category": row[7],
            "content": row[8],
            "word_count": row[9]
        })

    return documents


def clear_chunks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chunks")

    conn.commit()
    conn.close()


def insert_chunk(document_id, chunk_index, chunk_text, source, url, company, category):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chunks (
        document_id, chunk_index, chunk_text, source, url, company, category
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        chunk_index,
        chunk_text,
        source,
        url,
        company,
        category
    ))

    conn.commit()
    conn.close()


def get_chunk_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM chunks")
    total_chunks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT document_id) FROM chunks")
    documents_chunked = cursor.fetchone()[0]

    cursor.execute("""
    SELECT 
        MIN(LENGTH(chunk_text)) AS min_chars,
        AVG(LENGTH(chunk_text)) AS avg_chars,
        MAX(LENGTH(chunk_text)) AS max_chars
    FROM chunks
    """)

    row = cursor.fetchone()

    conn.close()

    return {
        "total_chunks": total_chunks,
        "documents_chunked": documents_chunked,
        "min_chars": row[0],
        "avg_chars": row[1],
        "max_chars": row[2]
    }


def get_all_chunks():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        c.id,
        c.document_id,
        c.chunk_index,
        c.chunk_text,
        c.source,
        c.url,
        c.company,
        c.category,
        d.title,
        d.source_type,
        d.published_date
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    ORDER BY c.id
    """)

    rows = cursor.fetchall()
    conn.close()

    chunks = []

    for row in rows:
        chunks.append({
            "chunk_id": row[0],
            "document_id": row[1],
            "chunk_index": row[2],
            "chunk_text": row[3],
            "source": row[4],
            "url": row[5],
            "company": row[6],
            "category": row[7],
            "title": row[8],
            "source_type": row[9],
            "published_date": row[10]
        })

    return chunks


if __name__ == "__main__":
    create_tables()
    print(f"Database initialized at: {DB_PATH}")