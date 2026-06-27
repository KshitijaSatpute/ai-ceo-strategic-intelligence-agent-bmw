from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from intelligence.strategic_analyzer import CEORecommendationEngine
from agent.validator import AgentValidator


class StrategicTools:
    def __init__(self, top_k=8, use_llm=True):
        self.engine = CEORecommendationEngine(top_k=top_k, use_llm=use_llm)
        self.validator = AgentValidator()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.top_k = top_k
        self.use_llm = use_llm

    def search_evidence_tool(self, question):
        raw_evidence = self.engine.retriever.retrieve(question, top_k=self.top_k)
        evidence_items = self.engine.filter_evidence(raw_evidence)
        return evidence_items

    def analysis_tool(self, evidence_items):
        risks = self.engine.generate_supported_risks(evidence_items)
        opportunities = self.engine.generate_supported_opportunities(evidence_items)
        trends = self.engine.generate_supported_trends(evidence_items)

        return {
            "risks": risks,
            "opportunities": opportunities,
            "trends": trends
        }

    def sentiment_tool(self, evidence_items):
        combined_text = self.engine.combine_evidence_text(evidence_items)

        if not combined_text.strip():
            return {
                "label": "Neutral",
                "compound": 0.0,
                "reason": "No evidence text available for sentiment analysis."
            }

        score = self.sentiment_analyzer.polarity_scores(combined_text)
        compound = score["compound"]

        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "label": label,
            "compound": round(compound, 4),
            "reason": "Sentiment is calculated from retrieved evidence using VADER compound score."
        }

    def recommendation_tool(self, question, evidence_items, analysis, sentiment):
        risks = analysis["risks"]
        opportunities = analysis["opportunities"]
        trends = analysis["trends"]

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
            "sentiment": sentiment,
            "actions": actions,
            "final_briefing": final_briefing,
            "evidence": self.engine.build_evidence_summary(evidence_items),
            "generation_mode": generation_mode
        }

    def validation_tool(self, result):
        return self.validator.validate(result)


if __name__ == "__main__":
    tools = StrategicTools(top_k=5, use_llm=False)

    question = "What are BMW's biggest risks in the EV market?"

    evidence = tools.search_evidence_tool(question)
    analysis = tools.analysis_tool(evidence)
    sentiment = tools.sentiment_tool(evidence)

    result = tools.recommendation_tool(
        question,
        evidence,
        analysis,
        sentiment
    )

    validation = tools.validation_tool(result)

    print("Question:", result["question"])
    print("Priority:", result["priority"])
    print("Confidence:", result["confidence"])
    print("Sentiment:", result["sentiment"])

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