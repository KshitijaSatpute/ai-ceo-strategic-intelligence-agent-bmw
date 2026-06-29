class AgentPlanner:
    def __init__(self):
        self.goal_types = [
            "strategic_decision",
            "risk_analysis",
            "opportunity_analysis",
            "trend_analysis",
            "competitor_analysis"
        ]

    def detect_goal_type(self, user_goal):
        goal = user_goal.lower()

        risk_words = [
            "risk", "risks", "threat", "threats", "challenge",
            "problem", "weakness", "barrier", "limit", "decline"
        ]

        opportunity_words = [
            "opportunity", "opportunities", "growth", "expand",
            "increase", "advantage", "potential", "market"
        ]

        trend_words = [
            "trend", "trends", "emerging", "future", "technology",
            "innovation", "shift", "monitor"
        ]

        competitor_words = [
            "competitor", "competition", "rival", "tesla", "byd",
            "mercedes", "audi", "volkswagen", "market share"
        ]

        strategic_words = [
            "what should", "next", "strategy", "strategic",
            "prioritize", "recommend", "decision", "ceo"
        ]

        if any(word in goal for word in competitor_words):
            return "competitor_analysis"

        if any(word in goal for word in risk_words):
            return "risk_analysis"

        if any(word in goal for word in opportunity_words):
            return "opportunity_analysis"

        if any(word in goal for word in trend_words):
            return "trend_analysis"

        if any(word in goal for word in strategic_words):
            return "strategic_decision"

        return "strategic_decision"

    def select_tools(self, goal_type):
        common_start = ["retrieve_evidence_tool"]
        common_end = [
            "generate_recommendation_tool",
            "validate_recommendation_tool",
            "save_memory_tool"
        ]

        if goal_type == "risk_analysis":
            analysis_tools = [
                "analyze_risks_tool",
                "analyze_trends_tool"
            ]

        elif goal_type == "opportunity_analysis":
            analysis_tools = [
                "analyze_opportunities_tool",
                "analyze_trends_tool"
            ]

        elif goal_type == "trend_analysis":
            analysis_tools = [
                "analyze_trends_tool"
            ]

        elif goal_type == "competitor_analysis":
            analysis_tools = [
                "analyze_competitors_tool",
                "analyze_risks_tool"
            ]

        else:
            analysis_tools = [
                "analyze_opportunities_tool",
                "analyze_risks_tool",
                "analyze_trends_tool"
            ]

        return common_start + analysis_tools + common_end

    def create_plan(self, user_goal):
        goal_type = self.detect_goal_type(user_goal)
        selected_tools = self.select_tools(goal_type)

        plan_steps = [
            "Receive the CEO-level user goal",
            "Detect the goal type",
            "Select tools based on the detected goal type",
            "Retrieve supporting evidence from the vector database",
            "Analyze the retrieved evidence using selected analysis tools",
            "Generate a CEO-level recommendation",
            "Validate the recommendation before approval",
            "Save the agent run in memory",
            "Return the result with trace and evidence"
        ]

        return {
            "user_goal": user_goal,
            "goal_type": goal_type,
            "selected_tools": selected_tools,
            "plan_steps": plan_steps
        }


if __name__ == "__main__":
    planner = AgentPlanner()

    test_goals = [
        "What should BMW do next in EV strategy?",
        "What are BMW's biggest risks in the EV market?",
        "What opportunities does BMW have in electric vehicles?",
        "Which EV trends should BMW monitor?",
        "How should BMW respond to Tesla and BYD?"
    ]

    for goal in test_goals:
        plan = planner.create_plan(goal)
        print("\nGoal:", goal)
        print("Goal type:", plan["goal_type"])
        print("Selected tools:", plan["selected_tools"])