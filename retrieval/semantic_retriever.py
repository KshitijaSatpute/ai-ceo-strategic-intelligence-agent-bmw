import chromadb
from sentence_transformers import SentenceTransformer
from utils.config import CHROMA_DIR, EMBEDDING_MODEL_NAME, TOP_K


COLLECTION_NAME = "bmw_ai_ceo_chunks"


class BMWStrategicRetriever:
    def __init__(self):
        print("Loading embedding model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        print("Connecting to ChromaDB...")
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        self.collection = self.client.get_collection(name=COLLECTION_NAME)

        print(f"Connected to collection: {COLLECTION_NAME}")
        print(f"Total chunks in collection: {self.collection.count()}")

    def retrieve(self, query, top_k=5):
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True
        ).tolist()[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_items = []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for index, document in enumerate(documents):
            metadata = metadatas[index]
            distance = distances[index]

            similarity_score = 1 - distance

            retrieved_items.append(
                {
                    "rank": index + 1,
                    "similarity_score": similarity_score,
                    "text": document,
                    "title": metadata.get("title", ""),
                    "source": metadata.get("source", ""),
                    "category": metadata.get("category", ""),
                    "url": metadata.get("url", ""),
                    "document_id": metadata.get("document_id", ""),
                    "chunk_id": metadata.get("chunk_id", "")
                }
            )

        return retrieved_items


def print_retrieval_results(query, results):
    print("\nQuery:")
    print(query)
    print("\nTop retrieved evidence:")

    for item in results:
        print("\n" + "=" * 80)
        print(f"Rank: {item['rank']}")
        print(f"Similarity score: {item['similarity_score']:.4f}")
        print(f"Source: {item['source']}")
        print(f"Category: {item['category']}")
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
        print("-" * 80)

        preview = item["text"][:800]
        print(preview)

        if len(item["text"]) > 800:
            print("...")


if __name__ == "__main__":
    retriever = BMWStrategicRetriever()

    test_queries = [
        "What are BMW's biggest risks in the electric vehicle market?",
        "What opportunities does BMW have in EV strategy?",
        "How are Tesla and BYD creating competition for BMW?",
        "What is the importance of Neue Klasse for BMW?",
        "What battery and charging trends matter for BMW?"
    ]

    for query in test_queries:
        results = retriever.retrieve(query, top_k=TOP_K)
        print_retrieval_results(query, results)