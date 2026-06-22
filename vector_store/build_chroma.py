import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer
from utils.config import DB_PATH, CHROMA_DIR, EMBEDDING_MODEL_NAME


COLLECTION_NAME = "bmw_ai_ceo_chunks"


def load_chunks_from_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
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
        FROM chunks
        WHERE chunk_text IS NOT NULL
        AND LENGTH(chunk_text) > 0
        """
    )

    chunks = cursor.fetchall()
    conn.close()

    return chunks


def build_chroma_vector_store():
    print("Loading chunks from SQLite database...")
    chunks = load_chunks_from_database()

    if not chunks:
        print("No chunks found. Run this first:")
        print("python -m data_processing.chunk_documents_char")
        return

    print(f"Chunks loaded: {len(chunks)}")

    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    documents = []
    ids = []
    metadatas = []

    for chunk in chunks:
        chunk_id = chunk["id"]

        documents.append(chunk["chunk_text"])
        ids.append(f"chunk_{chunk_id}")

        metadatas.append(
            {
                "chunk_id": chunk["id"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "title": chunk["title"] or "",
                "source": chunk["source"] or "",
                "source_type": chunk["source_type"] or "",
                "url": chunk["url"] or "",
                "company": chunk["company"] or "",
                "category": chunk["category"] or "",
                "word_count": chunk["word_count"] or 0,
            }
        )

    print("Generating embeddings...")
    embeddings = model.encode(
        documents,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    embeddings = embeddings.tolist()

    print(f"Creating ChromaDB at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete old collection if it exists
    existing_collections = [collection.name for collection in client.list_collections()]

    if COLLECTION_NAME in existing_collections:
        print("Old Chroma collection found. Deleting it...")
        client.delete_collection(name=COLLECTION_NAME)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    print("Adding chunks and embeddings to ChromaDB...")

    batch_size = 100

    for start in range(0, len(documents), batch_size):
        end = start + batch_size

        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end]
        )

        print(f"Stored chunks {start + 1} to {min(end, len(documents))}")

    print("\nChromaDB build completed.")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Total stored chunks: {collection.count()}")


if __name__ == "__main__":
    build_chroma_vector_store()
