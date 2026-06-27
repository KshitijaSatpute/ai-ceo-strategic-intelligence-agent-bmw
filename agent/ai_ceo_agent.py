from agent.planner import AgentPlanner
from tools.strategic_tools import StrategicTools
from agent.memory import AgentMemory


class StrategicAgent:
    def __init__(self, top_k=8, use_llm=True):
        self.planner = AgentPlanner()
        self.tools = StrategicTools(top_k=top_k, use_llm=use_llm)
        self.memory = AgentMemory()

    def run(self, question):
        plan = self.planner.create_plan(question)

        trace = {
            "goal": question,
            "query_type": plan["query_type"],
            "plan_steps": plan["steps"],
            "selected_tools": plan["tools"].copy(),
            "executed_tools": [],
            "decisions": [],
            "validation": {}
        }

        trace["decisions"].append(
            f"Agent classified the question as: {plan['query_type']}"
        )

        evidence = self.tools.search_evidence_tool(question)
        trace["executed_tools"].append("search_evidence_tool")
        trace["decisions"].append(
            f"Retrieved {len(evidence)} evidence items from ChromaDB."
        )

        risks = []
        opportunities = []
        trends = []

        if "risk_analysis_tool" in trace["selected_tools"]:
            risks = self.tools.risk_analysis_tool(evidence)
            trace["executed_tools"].append("risk_analysis_tool")

        if "opportunity_analysis_tool" not in trace["selected_tools"]:
            trace["selected_tools"].append("opportunity_analysis_tool")
            trace["decisions"].append(
                "Agent added opportunity_analysis_tool because recommendation needs opportunity context."
            )

        opportunities = self.tools.opportunity_analysis_tool(evidence)
        trace["executed_tools"].append("opportunity_analysis_tool")

        if "trend_analysis_tool" in trace["selected_tools"]:
            trends = self.tools.trend_analysis_tool(evidence)
            trace["executed_tools"].append("trend_analysis_tool")

        if not risks:
            risks = self.tools.risk_analysis_tool(evidence)
            trace["executed_tools"].append("risk_analysis_tool")
            trace["decisions"].append(
                "Agent added risk_analysis_tool because recommendation needs risk context."
            )

        if not trends:
            trends = self.tools.trend_analysis_tool(evidence)
            trace["executed_tools"].append("trend_analysis_tool")
            trace["decisions"].append(
                "Agent added trend_analysis_tool because recommendation needs trend context."
            )

        result = self.tools.recommendation_tool(
            question,
            evidence,
            risks,
            opportunities,
            trends
        )
        trace["executed_tools"].append("recommendation_tool")

        validation = self.tools.validation_tool(result)
        trace["executed_tools"].append("validation_tool")
        trace["validation"] = validation

        if validation["status"] == "passed":
            trace["decisions"].append(
                "Recommendation passed validation and is ready for dashboard output."
            )
        else:
            trace["decisions"].append(
                "Recommendation failed validation or needs review."
            )

        result["agent_trace"] = trace
        result["validation"] = validation

        memory_id = self.memory.save_run(result)
        trace["executed_tools"].append("memory_tool")
        trace["decisions"].append(
            f"Agent run saved to memory with ID: {memory_id}"
        )

        result["agent_trace"] = trace

        return result

    def print_result(self, result):
        print("\n" + "=" * 90)
        print("AI CEO STRATEGIC AGENT")
        print("=" * 90)

        trace = result["agent_trace"]

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

        print("\nFinal briefing:")
        print(result["final_briefing"])

        print("\nSupporting evidence:")
        for item in result["evidence"]:
            print("-" * 70)
            print(f"Rank: {item['rank']}")
            print(f"Source: {item['source']}")
            print(f"Title: {item['title']}")
            print(f"Similarity: {item['similarity']}")


if __name__ == "__main__":
    agent = StrategicAgent(top_k=5, use_llm=False)

    question = "What are BMW's biggest risks in the EV market?"

    result = agent.run(question)
    agent.print_result(result)