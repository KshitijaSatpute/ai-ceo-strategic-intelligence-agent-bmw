from intelligence_engine.recommendation_engine import CEORecommendationEngine


class AICEOAgent:
    def __init__(self, top_k=8, use_llm=True):
        self.engine = CEORecommendationEngine(
            top_k=top_k,
            use_llm=use_llm
        )

    def ask(self, question):
        result = self.engine.generate_recommendation(question)

        final_answer = {
            "question": result["question"],
            "priority": result["priority"],
            "confidence": result["confidence"],
            "generation_mode": result["generation_mode"],
            "final_briefing": result["final_briefing"],
            "risks": result["risks"],
            "opportunities": result["opportunities"],
            "trends": result["trends"],
            "actions": result["actions"],
            "evidence": result["evidence"],
        }

        return final_answer

    def print_answer(self, result):
        print("\n" + "=" * 90)
        print("AI CEO STRATEGIC INTELLIGENCE AGENT")
        print("=" * 90)

        print("\nQuestion:")
        print(result["question"])

        print("\nPriority:")
        print(result["priority"])

        print("\nConfidence:")
        print(result["confidence"])

        print("\nGeneration mode:")
        print(result["generation_mode"])

        print("\nCEO Briefing:")
        print(result["final_briefing"])

        print("\nRisks:")
        for risk in result["risks"]:
            print(
                f"- {risk['title']} | "
                f"Severity: {risk['severity']} | "
                f"Category: {risk['category']}"
            )

        print("\nOpportunities:")
        for opportunity in result["opportunities"]:
            print(
                f"- {opportunity['title']} | "
                f"Impact: {opportunity['impact']}"
            )

        print("\nTrends:")
        for trend in result["trends"]:
            print(f"- {trend}")

        print("\nRecommended Actions:")
        for index, action in enumerate(result["actions"], start=1):
            print(f"{index}. {action}")

        print("\nSupporting Evidence:")
        for item in result["evidence"]:
            print("-" * 90)
            print(f"Rank: {item['rank']}")
            print(f"Similarity: {item['similarity']}")
            print(f"Source: {item['source']}")
            print(f"Category: {item['category']}")
            print(f"Title: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"Preview: {item['preview']}...")


def ask_ceo_agent(question, top_k=8, use_llm=True):
    agent = AICEOAgent(
        top_k=top_k,
        use_llm=use_llm
    )

    result = agent.ask(question)
    return result


if __name__ == "__main__":
    agent = AICEOAgent(top_k=8, use_llm=True)

    question = "What should BMW do next in EV strategy?"

    result = agent.ask(question)
    agent.print_answer(result)