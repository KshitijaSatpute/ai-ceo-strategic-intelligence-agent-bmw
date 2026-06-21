import sqlite3
import pandas as pd
from utils.config import DB_PATH


def check_chunks():
    conn = sqlite3.connect(DB_PATH)

    chunk_count = pd.read_sql_query(
        "SELECT COUNT(*) AS total_chunks FROM chunks",
        conn
    )

    source_count = pd.read_sql_query(
        """
        SELECT source, COUNT(*) AS chunk_count
        FROM chunks
        GROUP BY source
        ORDER BY chunk_count DESC
        """,
        conn
    )

    category_count = pd.read_sql_query(
        """
        SELECT category, COUNT(*) AS chunk_count
        FROM chunks
        GROUP BY category
        ORDER BY chunk_count DESC
        """,
        conn
    )

    sample_chunks = pd.read_sql_query(
        """
        SELECT title, source, category, word_count
        FROM chunks
        LIMIT 10
        """,
        conn
    )

    conn.close()

    print("\nCHUNK COUNT")
    print(chunk_count)

    print("\nCHUNKS BY SOURCE")
    print(source_count)

    print("\nCHUNKS BY CATEGORY")
    print(category_count)

    print("\nSAMPLE CHUNKS")
    print(sample_chunks)


if __name__ == "__main__":
    check_chunks()