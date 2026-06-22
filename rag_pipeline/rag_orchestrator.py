from rag_pipeline.query_pipeline import run_query_pipeline, print_query_result


def run_full_rag_pipeline(question):
    """
    Complete runtime RAG pipeline.

    Flow:
    User question
        -> semantic retrieval from ChromaDB
        -> evidence extraction
        -> risks, opportunities, trends, actions
        -> CEO-level recommendation output
    """

    print("Running complete RAG pipeline...")
    print(f"Input question: {question}")

    result = run_query_pipeline(
        question=question,
        top_k=8,
        use_llm=True
    )

    print_query_result(result)

    return result


if __name__ == "__main__":
    question = "What are BMW's biggest risks in the electric vehicle market?"
    run_full_rag_pipeline(question)