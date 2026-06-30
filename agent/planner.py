class AgentPlanner:
    def __init__(self):
        self.goal_types = [
            "strategic_decision",
            "risk_analysis",
            "opportunity_analysis",
            "trend_analysis",
            "competitor_analysis"
        ]

    def create_plan(self, user_goal):
        goal_type = self.detect_goal_type(user_goal)
        selected_tools = self.select_tools(goal_type)

        return {
            "user_goal": user_goal,
            "goal_type": goal_type,
            "selected_tools": selected_tools,
            "plan_steps": [
                "Receive the CEO-level user goal",
                "Detect the goal type",
                "Select tools based on the detected goal type",
                "Retrieve supporting evidence from the vector database",
                "Analyze the retrieved evidence using selected analysis tools",
                "Generate a CEO-level recommendation using retrieved evidence",
                "Validate the recommendation before approval",
                "Save the agent run in memory",
                "Return the result with trace and evidence"
            ]
        }

    def detect_goal_type(self, user_goal):
        query = user_goal.lower()

        strategic_phrases = [
            "what should", "what strategic", "what actions", "what should bmw do",
            "do next", "next steps", "recommend", "recommendation",
            "strategy", "strategic", "prioritize", "position", "roadmap",
            "future strategy", "decision", "ceo"
        ]

        risk_phrases = [
            "risk", "risks", "threat", "threats", "challenge", "challenges",
            "problem", "problems", "weak demand", "slowdown", "profitability risk",
            "margin pressure", "cost pressure"
        ]

        opportunity_phrases = [
            "opportunity", "opportunities", "growth opportunity",
            "growth opportunities", "investment opportunity", "market expansion",
            "strongest growth", "where can bmw grow"
        ]

        trend_phrases = [
            "trend", "trends", "market trends", "technology trends",
            "monitor", "watch", "future trends", "industry trends"
        ]

        competitor_phrases = [
            "competitor", "competitors", "competition", "compete",
            "respond to competition", "tesla", "byd", "chinese ev makers",
            "mercedes", "audi", "volkswagen"
        ]

        product_strategy_phrases = [
            "neue klasse", "platform", "product strategy", "position",
            "positioning", "product roadmap"
        ]

        has_strategic = self._contains_any(query, strategic_phrases)
        has_risk = self._contains_any(query, risk_phrases)
        has_opportunity = self._contains_any(query, opportunity_phrases)
        has_trend = self._contains_any(query, trend_phrases)
        has_competitor = self._contains_any(query, competitor_phrases)
        has_product_strategy = self._contains_any(query, product_strategy_phrases)

        signal_count = sum([
            has_risk,
            has_opportunity,
            has_trend,
            has_competitor,
            has_product_strategy
        ])

        if has_strategic and signal_count >= 2:
            return "strategic_decision"

        if has_product_strategy and has_strategic:
            return "strategic_decision"

        if has_trend and not has_competitor and not has_risk:
            return "trend_analysis"

        if has_competitor and not has_strategic:
            return "competitor_analysis"

        if has_competitor and "respond" in query:
            return "competitor_analysis"

        if has_risk and not has_strategic:
            return "risk_analysis"

        if has_opportunity and not has_strategic:
            return "opportunity_analysis"

        if has_trend:
            return "trend_analysis"

        if has_product_strategy:
            return "strategic_decision"

        if has_strategic:
            return "strategic_decision"

        return "strategic_decision"

    def select_tools(self, goal_type):
        tools = ["retrieve_evidence_tool"]

        if goal_type == "risk_analysis":
            tools.extend([
                "analyze_risks_tool",
                "analyze_trends_tool"
            ])

        elif goal_type == "opportunity_analysis":
            tools.extend([
                "analyze_opportunities_tool",
                "analyze_trends_tool"
            ])

        elif goal_type == "trend_analysis":
            tools.extend([
                "analyze_trends_tool",
                "analyze_opportunities_tool"
            ])

        elif goal_type == "competitor_analysis":
            tools.extend([
                "analyze_competitors_tool",
                "analyze_risks_tool"
            ])

        else:
            tools.extend([
                "analyze_risks_tool",
                "analyze_opportunities_tool",
                "analyze_trends_tool",
                "analyze_competitors_tool"
            ])

        tools.extend([
            "generate_recommendation_tool",
            "validate_recommendation_tool",
            "save_memory_tool"
        ])

        return tools

    def _contains_any(self, text, phrases):
        for phrase in phrases:
            if phrase in text:
                return True

        return False


if __name__ == "__main__":
    planner = AgentPlanner()

    test_queries = [
        "What EV market and technology trends should BMW monitor for its future strategy?",
        "How should BMW position the Neue Klasse platform in its future EV strategy?",
        "What should BMW do next in its EV strategy considering competition from Chinese EV makers, Neue Klasse innovation, customer demand, and profitability risks?",
        "How should BMW respond to competition from Tesla, BYD, Mercedes, Audi, and Volkswagen in the EV market?",
        "What are the biggest strategic risks BMW faces in the EV market?",
        "What are the strongest growth opportunities for BMW in electric vehicles?"
    ]

    for query in test_queries:
        plan = planner.create_plan(query)
        print()
        print("Query:", query)
        print("Goal Type:", plan["goal_type"])
        print("Tools:", plan["selected_tools"])