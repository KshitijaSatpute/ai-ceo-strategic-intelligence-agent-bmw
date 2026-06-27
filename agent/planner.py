class AgentPlanner:
    def classify_question(self, question):
        question_lower = question.lower()

        if "risk" in question_lower or "threat" in question_lower or "challenge" in question_lower:
            return "risk_analysis"

        if "opportunity" in question_lower or "growth" in question_lower or "neue klasse" in question_lower:
            return "opportunity_analysis"

        if "tesla" in question_lower or "byd" in question_lower or "competition" in question_lower or "competitor" in question_lower:
            return "competition_analysis"

        if "sentiment" in question_lower or "public opinion" in question_lower or "market reaction" in question_lower:
            return "sentiment_analysis"

        return "full_strategy"

    def create_plan(self, question):
        query_type = self.classify_question(question)

        return {
            "goal": question,
            "query_type": query_type,
            "steps": [
                "Understand the CEO question",
                "Retrieve relevant BMW EV evidence",
                "Analyze risk, opportunity, and trend signals",
                "Check evidence sentiment",
                "Generate CEO-level recommendation",
                "Validate the recommendation",
                "Save the agent run in memory"
            ],
            "tools": [
                "search_evidence_tool",
                "analysis_tool",
                "sentiment_tool",
                "recommendation_tool",
                "validation_tool"
            ]
        }


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