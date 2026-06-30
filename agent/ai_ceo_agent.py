from agent.planner import AgentPlanner
from agent.memory import AgentMemory
from tools.strategic_tools import StrategicTools


class StrategicAgent:
    def __init__(self, top_k=5, use_llm=False):
        self.planner = AgentPlanner()
        self.tools = StrategicTools(top_k=top_k, use_llm=True)
        self.memory = AgentMemory()

    def run(self, user_goal):
        plan = self.planner.create_plan(user_goal)
        goal_type = plan["goal_type"]
        selected_tools = plan["selected_tools"]

        execution_trace = []
        agent_decisions = []

        agent_decisions.append(
            f"User goal received and classified as {goal_type}."
        )

        execution_trace.append("Planner created a controlled execution plan.")
        execution_trace.append(f"Selected tools: {', '.join(selected_tools)}")

        evidence_items = self.tools.retrieve_evidence_tool(user_goal)
        execution_trace.append(
            f"retrieve_evidence_tool returned {len(evidence_items)} evidence chunks."
        )

        analysis_results = {
            "risks": [],
            "opportunities": [],
            "trends": [],
            "competitors": []
        }

        if "analyze_risks_tool" in selected_tools:
            analysis_results["risks"] = self.tools.analyze_risks_tool(evidence_items)
            execution_trace.append("analyze_risks_tool executed.")

        if "analyze_opportunities_tool" in selected_tools:
            analysis_results["opportunities"] = self.tools.analyze_opportunities_tool(evidence_items)
            execution_trace.append("analyze_opportunities_tool executed.")

        if "analyze_trends_tool" in selected_tools:
            analysis_results["trends"] = self.tools.analyze_trends_tool(evidence_items)
            execution_trace.append("analyze_trends_tool executed.")

        if "analyze_competitors_tool" in selected_tools:
            analysis_results["competitors"] = self.tools.analyze_competitors_tool(evidence_items)
            execution_trace.append("analyze_competitors_tool executed.")

        sentiment = self.tools.sentiment_tool(evidence_items)
        execution_trace.append("sentiment_tool executed for evidence tone.")

        recommendation_result = self.tools.generate_recommendation_tool(
            user_goal=user_goal,
            goal_type=goal_type,
            evidence_items=evidence_items,
            analysis_results=analysis_results,
            sentiment=sentiment
        )

        execution_trace.append("generate_recommendation_tool executed.")

        validation = self.tools.validate_recommendation_tool(recommendation_result)
        execution_trace.append("validate_recommendation_tool executed.")

        recommendation_result["validation"] = validation
        recommendation_result["tools_used"] = selected_tools

        memory_result = self.memory.save_run(recommendation_result)
        execution_trace.append("save_memory_tool executed.")

        recommendation_result["memory"] = memory_result

        if validation.get("approved"):
            agent_decisions.append("Validation passed. Recommendation approved.")
        else:
            agent_decisions.append("Validation failed. Recommendation needs review.")

        agent_trace = {
            "goal": user_goal,
            "goal_type": goal_type,
            "plan_steps": plan["plan_steps"],
            "selected_tools": selected_tools,
            "execution_trace": execution_trace,
            "agent_decisions": agent_decisions,
            "validation_result": validation,
            "memory_updated": memory_result
        }

        recommendation_result["agent_trace"] = agent_trace

        return recommendation_result

    def ask(self, question):
        result = self.run(question)
        result["sources"] = result.get("evidence", [])
        return result

    def print_result(self, result):
        print("\nAI CEO Agent Result")
        print("Goal:", result.get("user_goal"))
        print("Goal Type:", result.get("goal_type"))
        print("Priority:", result.get("priority"))
        print("Confidence:", result.get("confidence"))
        print("\nAnswer:")
        print(result.get("answer"))


AICEOAgent = StrategicAgent


if __name__ == "__main__":
    agent = StrategicAgent(top_k=5, use_llm=False)

    question = "What are BMW's biggest risks in the EV market?"
    result = agent.run(question)

    agent.print_result(result)

    print("\nSelected Tools:")
    for tool in result["agent_trace"]["selected_tools"]:
        print("-", tool)

    print("\nValidation:")
    print(result["validation"])