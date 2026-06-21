import sqlite3
import pandas as pd
from utils.config import DB_PATH

conn = sqlite3.connect(DB_PATH)

print("\nDOCUMENT COUNT")
print(pd.read_sql_query("SELECT COUNT(*) AS total_documents FROM documents", conn))

print("\nSOURCE COUNT")
print(pd.read_sql_query("""
SELECT source, source_type, COUNT(*) AS count
FROM documents
GROUP BY source, source_type
ORDER BY count DESC
""", conn))

print("\nCATEGORY COUNT")
print(pd.read_sql_query("""
SELECT category, COUNT(*) AS count
FROM documents
GROUP BY category
ORDER BY count DESC
""", conn))

print("\nWORD COUNT STATS")
print(pd.read_sql_query("""
SELECT 
    MIN(word_count) AS min_words,
    AVG(word_count) AS avg_words,
    MAX(word_count) AS max_words
FROM documents
""", conn))

print("\nSAMPLE DOCUMENTS")
df = pd.read_sql_query("""
SELECT title, source, source_type, company, category, word_count
FROM documents
ORDER BY id DESC
LIMIT 10
""", conn)

print(df.to_string(index=False))

conn.close()