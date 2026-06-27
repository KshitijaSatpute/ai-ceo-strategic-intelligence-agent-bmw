class AgentPlanner:
    def create_plan(self, question):
        question_lower = question.lower()

        plan = {
            "goal": question,
            "query_type": "general_strategy",
            "steps": [],
            "tools": []
        }

        if "risk" in question_lower or "threat" in question_lower:
            plan["query_type"] = "risk_analysis"
            plan["steps"] = [
                "Retrieve relevant BMW EV evidence",
                "Analyze risk signals",
                "Analyze market trends",
                "Generate CEO recommendation",
                "Validate recommendation",
                "Save agent memory"
            ]
            plan["tools"] = [
                "search_evidence_tool",
                "risk_analysis_tool",
                "trend_analysis_tool",
                "recommendation_tool",
                "validation_tool",
                "memory_tool"
            ]

        elif "opportunity" in question_lower or "neue klasse" in question_lower:
            plan["query_type"] = "opportunity_analysis"
            plan["steps"] = [
                "Retrieve relevant BMW EV evidence",
                "Analyze opportunity signals",
                "Analyze market trends",
                "Generate CEO recommendation",
                "Validate recommendation",
                "Save agent memory"
            ]
            plan["tools"] = [
                "search_evidence_tool",
                "opportunity_analysis_tool",
                "trend_analysis_tool",
                "recommendation_tool",
                "validation_tool",
                "memory_tool"
            ]

        elif "sentiment" in question_lower:
            plan["query_type"] = "sentiment_analysis"
            plan["steps"] = [
                "Retrieve relevant BMW EV evidence",
                "Analyze sentiment",
                "Generate summary",
                "Validate output",
                "Save agent memory"
            ]
            plan["tools"] = [
                "search_evidence_tool",
                "sentiment_analysis_tool",
                "validation_tool",
                "memory_tool"
            ]

        else:
            plan["query_type"] = "full_strategy"
            plan["steps"] = [
                "Retrieve relevant BMW EV evidence",
                "Analyze risks",
                "Analyze opportunities",
                "Analyze trends",
                "Generate CEO recommendation",
                "Validate recommendation",
                "Save agent memory"
            ]
            plan["tools"] = [
                "search_evidence_tool",
                "risk_analysis_tool",
                "opportunity_analysis_tool",
                "trend_analysis_tool",
                "recommendation_tool",
                "validation_tool",
                "memory_tool"
            ]

        return plan


if __name__ == "__main__":
    planner = AgentPlanner()

    question = "What are BMW's biggest risks in the EV market?"
    plan = planner.create_plan(question)

    print("Goal:", plan["goal"])
    print("Query type:", plan["query_type"])

    print("\nPlan:")
    for step in plan["steps"]:
        print("-", step)

    print("\nSelected tools:")
    for tool in plan["tools"]:
        print("-", tool)