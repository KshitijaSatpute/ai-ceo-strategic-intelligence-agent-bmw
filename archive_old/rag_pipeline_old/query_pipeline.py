from agents.ceo_agent import AICEOAgent


def run_query_pipeline(question, top_k=5, use_llm=True):
    """
    Step 2: Run the RAG query pipeline.

    This function sends a CEO-level question to the AI CEO Agent.
    The agent retrieves relevant evidence from ChromaDB and generates
    strategic intelligence using the recommendation engine.
    """

    agent = AICEOAgent(
        top_k=top_k,
        use_llm=use_llm
    )

    result = agent.ask(question)

    return result


def print_query_result(result):
    print("\nQuestion:")
    print(result.get("question", "N/A"))

    print("\nPriority:")
    print(result.get("priority", "N/A"))

    print("\nConfidence:")
    print(result.get("confidence", "N/A"))

    print("\nGeneration mode:")
    print(result.get("generation_mode", "N/A"))

    print("\nTop Evidence:")
    for index, item in enumerate(result.get("evidence", [])[:3], start=1):
        print(f"{index}. {item.get('title', 'Unknown title')} ({item.get('source', 'Unknown source')})")

    print("\nRecommended Actions:")
    for index, action in enumerate(result.get("actions", [])[:5], start=1):
        print(f"{index}. {action}")


if __name__ == "__main__":
    sample_question = "What should BMW do next in EV strategy?"
    output = run_query_pipeline(sample_question)
    print_query_result(output)