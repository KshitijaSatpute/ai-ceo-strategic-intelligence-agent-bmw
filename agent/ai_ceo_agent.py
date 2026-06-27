from agent.planner import AgentPlanner
from tools.strategic_tools import StrategicTools
from agent.memory import AgentMemory


class StrategicAgent:
    def __init__(self, top_k=5, use_llm=False):
        self.planner = AgentPlanner()
        self.tools = StrategicTools(top_k=top_k, use_llm=use_llm)
        self.memory = AgentMemory()

    def run(self, question):
        plan = self.planner.create_plan(question)

        trace = {
            "goal": question,
            "query_type": plan["query_type"],
            "plan_steps": plan["steps"],
            "selected_tools": plan["tools"],
            "executed_tools": [],
            "decisions": [],
            "validation": {}
        }

        trace["decisions"].append(
            f"Agent classified the question as: {plan['query_type']}."
        )

        evidence_items = self.tools.search_evidence_tool(question)
        trace["executed_tools"].append("search_evidence_tool")
        trace["decisions"].append(
            f"Retrieved {len(evidence_items)} evidence items from ChromaDB using semantic search."
        )

        analysis = self.tools.analysis_tool(evidence_items)
        trace["executed_tools"].append("analysis_tool")
        trace["decisions"].append(
            "Analyzed retrieved evidence for risks, opportunities, and trends."
        )

        sentiment = self.tools.sentiment_tool(evidence_items)
        trace["executed_tools"].append("sentiment_tool")
        trace["decisions"].append(
            f"Calculated evidence sentiment as {sentiment['label']} with compound score {sentiment['compound']}."
        )

        result = self.tools.recommendation_tool(
            question,
            evidence_items,
            analysis,
            sentiment
        )

        trace["executed_tools"].append("recommendation_tool")
        trace["decisions"].append(
            "Generated CEO-level recommendation using retrieved evidence and strategic analysis."
        )

        validation = self.tools.validation_tool(result)
        trace["executed_tools"].append("validation_tool")
        trace["validation"] = validation

        if validation["status"] == "passed":
            trace["decisions"].append(
                "Recommendation passed validation and is ready for dashboard output."
            )
        else:
            trace["decisions"].append(
                "Recommendation needs review because validation found issues."
            )

        result["agent_trace"] = trace
        result["validation"] = validation

        memory_id = self.memory.save_run(result)
        trace["decisions"].append(
            f"Agent run saved to memory with ID: {memory_id}."
        )

        result["agent_trace"] = trace

        return result

    def ask(self, question):
        result = self.run(question)

        result["answer"] = result.get("final_briefing", "")
        result["sources"] = result.get("evidence", [])

        return result

    def print_result(self, result):
        trace = result["agent_trace"]

        print("\n" + "=" * 90)
        print("AI CEO AGENT")
        print("=" * 90)

        print("\nGoal:")
        print(trace["goal"])

        print("\nQuery type:")
        print(trace["query_type"])

        print("\nPlan:")
        for step in trace["plan_steps"]:
            print("-", step)

        print("\nSelected tools:")
        for tool in trace["selected_tools"]:
            print("-", tool)

        print("\nExecuted tools:")
        for tool in trace["executed_tools"]:
            print("-", tool)

        print("\nAgent decisions:")
        for decision in trace["decisions"]:
            print("-", decision)

        print("\nValidation:")
        print(trace["validation"])

        print("\nPriority:")
        print(result["priority"])

        print("\nConfidence:")
        print(result["confidence"])

        print("\nSentiment:")
        print(result["sentiment"])

        print("\nFinal briefing:")
        print(result["final_briefing"])

        print("\nSupporting evidence:")
        for item in result["evidence"]:
            print("-" * 70)
            print(f"Rank: {item['rank']}")
            print(f"Source: {item['source']}")
            print(f"Title: {item['title']}")
            print(f"Similarity: {item['similarity']}")


AICEOAgent = StrategicAgent


if __name__ == "__main__":
    agent = StrategicAgent(top_k=5, use_llm=False)

    question = "What are BMW's biggest risks in the EV market?"

    result = agent.run(question)
    agent.print_result(result)