from intelligence.strategic_analyzer import CEORecommendationEngine
from agent.validator import AgentValidator


class StrategicTools:
    def __init__(self, top_k=8, use_llm=True):
        self.engine = CEORecommendationEngine(top_k=top_k, use_llm=use_llm)
        self.validator = AgentValidator()
        self.top_k = top_k
        self.use_llm = use_llm

    def search_evidence_tool(self, question):
        raw_evidence = self.engine.retriever.retrieve(question, top_k=self.top_k)
        evidence_items = self.engine.filter_evidence(raw_evidence)
        return evidence_items

    def risk_analysis_tool(self, evidence_items):
        return self.engine.generate_supported_risks(evidence_items)

    def opportunity_analysis_tool(self, evidence_items):
        return self.engine.generate_supported_opportunities(evidence_items)

    def trend_analysis_tool(self, evidence_items):
        return self.engine.generate_supported_trends(evidence_items)

    def recommendation_tool(self, question, evidence_items, risks, opportunities, trends):
        actions = self.engine.generate_supported_actions(
            risks,
            opportunities,
            evidence_items
        )

        priority = self.engine.decide_priority(risks, opportunities)
        confidence = self.engine.decide_confidence(evidence_items)

        fallback_briefing = self.engine.build_rule_based_briefing(
            question,
            risks,
            opportunities,
            trends,
            actions,
            priority,
            confidence,
            evidence_items
        )

        final_briefing = fallback_briefing
        generation_mode = "Rule-based recommendation from agent tools"

        if self.use_llm:
            llm_briefing = self.engine.generate_llm_briefing(
                question,
                risks,
                opportunities,
                trends,
                actions,
                priority,
                confidence,
                evidence_items
            )

            if llm_briefing:
                final_briefing = llm_briefing
                generation_mode = "LLM rewritten after agent tool execution"

        return {
            "question": question,
            "priority": priority,
            "confidence": confidence,
            "risks": risks,
            "opportunities": opportunities,
            "trends": trends,
            "actions": actions,
            "final_briefing": final_briefing,
            "evidence": self.engine.build_evidence_summary(evidence_items),
            "generation_mode": generation_mode,
        }

    def validation_tool(self, result):
        return self.validator.validate(result)


if __name__ == "__main__":
    tools = StrategicTools(top_k=5, use_llm=False)

    question = "What are BMW's biggest risks in the EV market?"

    evidence = tools.search_evidence_tool(question)
    risks = tools.risk_analysis_tool(evidence)
    opportunities = tools.opportunity_analysis_tool(evidence)
    trends = tools.trend_analysis_tool(evidence)

    result = tools.recommendation_tool(
        question,
        evidence,
        risks,
        opportunities,
        trends
    )

    validation = tools.validation_tool(result)

    print("Question:", result["question"])
    print("Priority:", result["priority"])
    print("Confidence:", result["confidence"])

    print("\nRisks:")
    for risk in result["risks"]:
        print("-", risk["title"])

    print("\nOpportunities:")
    for opportunity in result["opportunities"]:
        print("-", opportunity["title"])

    print("\nTrends:")
    for trend in result["trends"]:
        print("-", trend)

    print("\nValidation:")
    print(validation)