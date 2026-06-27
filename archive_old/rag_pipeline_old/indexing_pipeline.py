import runpy


def run_indexing_pipeline():
    """
    Step 1: Build or rebuild the vector database.

    This runs the existing vector_store.build_chroma module.
    It reads chunks from SQLite, generates embeddings, and stores them in ChromaDB.
    """

    print("Starting RAG indexing pipeline...")
    print("Step 1: Loading chunks from SQLite")
    print("Step 2: Generating embeddings")
    print("Step 3: Storing vectors in ChromaDB")

    runpy.run_module("vector_store.build_chroma", run_name="__main__")

    print("RAG indexing pipeline completed.")


if __name__ == "__main__":
    run_indexing_pipeline()