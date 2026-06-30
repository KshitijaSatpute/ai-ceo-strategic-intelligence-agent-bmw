import json
import re
from pathlib import Path

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from agent.validator import AgentValidator
from intelligence.strategic_analyzer import CEORecommendationEngine


class StrategicTools:
    def __init__(self, top_k=5, use_llm=True, ollama_model="qwen2.5:3b"):
        self.top_k = top_k
        self.use_llm = use_llm
        self.ollama_model = ollama_model

        self.engine = CEORecommendationEngine(top_k=top_k, use_llm=False)
        self.validator = AgentValidator()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.db_path = Path(__file__).resolve().parents[1] / "data" / "ai_ceo.db"

    def retrieve_evidence_tool(self, user_goal):
        retrieved_items = self.engine.retriever.retrieve(
            user_goal,
            top_k=self.top_k
        )

        evidence_items = []

        for index, item in enumerate(retrieved_items, start=1):
            evidence_items.append({
                "evidence_id": f"E{index}",
                "rank": index,
                "title": item.get("title", "Untitled"),
                "source": item.get("source", "Unknown"),
                "category": item.get("category", "Unknown"),
                "url": item.get("url", ""),
                "text": item.get("text", item.get("chunk_text", "")),
                "similarity": item.get("similarity", item.get("score", 0.0))
            })

        return evidence_items

    def analyze_risks_tool(self, evidence_items):
        risk_themes = {
            "Competition / Market Pressure": [
                "competition", "competitor", "competitive", "rival", "tesla", "byd",
                "mercedes", "audi", "volkswagen", "market share", "price war",
                "pricing pressure"
            ],
            "Regulation / Policy Risk": [
                "regulation", "regulatory", "emissions", "ban", "policy",
                "compliance", "tariff", "law", "subsidy cut", "incentive cut"
            ],
            "Supply Chain / Production Risk": [
                "supply chain", "shortage", "production delay", "supplier",
                "raw material", "battery supply", "semiconductor", "factory",
                "manufacturing", "delivery delay"
            ],
            "Demand / Adoption Risk": [
                "weak demand", "slow demand", "slowdown", "sales decline",
                "sales drop", "slump", "customer hesitation", "affordability",
                "soft demand"
            ],
            "Technology / Execution Risk": [
                "battery issue", "charging issue", "range anxiety", "software issue",
                "recall", "delay", "technology risk", "execution risk",
                "reliability", "technical problem"
            ],
            "Financial / Cost Pressure": [
                "cost pressure", "margin pressure", "profit warning",
                "earnings pressure", "price cut", "loss", "financial pressure",
                "investment burden", "revenue decline"
            ]
        }

        signals = self._extract_signals(
            evidence_items=evidence_items,
            theme_keywords=risk_themes,
            signal_type="risk"
        )

        for signal in signals:
            signal["category"] = signal.pop("theme")
            signal["severity"] = self._level_from_score(signal["score"])

        return signals

    def analyze_opportunities_tool(self, evidence_items):
        opportunity_themes = {
            "Product / Innovation Opportunity": [
                "new product", "launch", "platform", "innovation", "technology",
                "software", "battery", "charging", "range", "next-generation",
                "neue klasse", "new model", "product launch", "electric platform"
            ],
            "Market Growth Opportunity": [
                "growth", "market expansion", "sales growth", "demand growth",
                "customer demand", "global market", "new market", "increase",
                "strong demand", "market opportunity"
            ],
            "Partnership / Ecosystem Opportunity": [
                "partnership", "partner", "collaboration", "joint venture",
                "alliance", "ecosystem", "supplier partnership", "charging partner"
            ],
            "Competitive Positioning Opportunity": [
                "advantage", "differentiation", "premium", "leadership",
                "market position", "competitive edge", "brand strength",
                "luxury", "performance", "premium segment"
            ],
            "Regulation / Policy Opportunity": [
                "subsidy", "incentive", "policy support", "tax credit",
                "government support", "emissions target", "regulatory support"
            ],
            "Customer / Adoption Opportunity": [
                "customer", "consumer adoption", "affordability", "user experience",
                "charging convenience", "range improvement", "customer interest",
                "adoption growth"
            ]
        }

        signals = self._extract_signals(
            evidence_items=evidence_items,
            theme_keywords=opportunity_themes,
            signal_type="opportunity"
        )

        for signal in signals:
            signal["impact"] = self._level_from_score(signal["score"])

        return signals

    def analyze_trends_tool(self, evidence_items):
        trend_themes = {
            "EV Market Trend": [
                "electric vehicle", "battery electric", "sales growth",
                "market growth", "market slowdown", "adoption", "demand"
            ],
            "Battery / Charging Trend": [
                "battery", "charging", "range", "fast charging",
                "charging network", "battery technology"
            ],
            "Software / Digital Vehicle Trend": [
                "software", "digital", "connected car", "operating system",
                "infotainment", "autonomous", "driver assistance"
            ],
            "China / Global Market Trend": [
                "china", "europe", "us market", "global", "new market",
                "international", "market expansion"
            ],
            "Cost / Pricing Trend": [
                "price", "cost", "margin", "affordability", "discount",
                "price cut", "premium pricing"
            ]
        }

        signals = self._extract_signals(
            evidence_items=evidence_items,
            theme_keywords=trend_themes,
            signal_type="trend"
        )

        for signal in signals:
            signal["type"] = signal.pop("theme")

        return signals

    def analyze_competitors_tool(self, evidence_items):
        competitor_themes = {
            "Tesla Competitive Signal": [
                "tesla", "model y", "model 3", "supercharger"
            ],
            "BYD Competitive Signal": [
                "byd", "china ev", "chinese ev", "seal", "atto"
            ],
            "German Premium Competitor Signal": [
                "mercedes", "audi", "volkswagen", "porsche"
            ],
            "US / Global Competitor Signal": [
                "rivian", "lucid", "ford", "gm", "hyundai", "kia"
            ],
            "Price Competition Signal": [
                "price war", "price cut", "discount", "pricing pressure",
                "cheaper", "affordable"
            ]
        }

        signals = self._extract_signals(
            evidence_items=evidence_items,
            theme_keywords=competitor_themes,
            signal_type="competitor"
        )

        for signal in signals:
            signal["category"] = signal.pop("theme")

        return signals

    def sentiment_tool(self, evidence_items):
        combined_text = " ".join(
            item.get("text", "") for item in evidence_items
        )

        if not combined_text.strip():
            return {
                "label": "Neutral",
                "compound": 0.0,
                "positive": 0.0,
                "neutral": 1.0,
                "negative": 0.0,
                "reason": "No evidence text was available for sentiment analysis."
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
            "positive": round(score["pos"], 4),
            "neutral": round(score["neu"], 4),
            "negative": round(score["neg"], 4),
            "reason": "Sentiment is calculated from retrieved evidence using VADER."
        }

    def generate_recommendation_tool(
        self,
        user_goal,
        goal_type,
        evidence_items,
        analysis_results,
        sentiment
    ):
        risks = analysis_results.get("risks", [])
        opportunities = analysis_results.get("opportunities", [])
        trends = analysis_results.get("trends", [])
        competitors = analysis_results.get("competitors", [])

        actions = self._build_actions(
            goal_type=goal_type,
            risks=risks,
            opportunities=opportunities,
            trends=trends,
            competitors=competitors
        )

        priority = self._decide_priority(
            goal_type=goal_type,
            risks=risks,
            opportunities=opportunities,
            trends=trends,
            competitors=competitors
        )

        confidence = self._decide_confidence(
            evidence_items=evidence_items,
            risks=risks,
            opportunities=opportunities,
            trends=trends,
            competitors=competitors
        )

        prompt = self._build_llm_prompt(
            user_goal=user_goal,
            goal_type=goal_type,
            evidence_items=evidence_items,
            risks=risks,
            opportunities=opportunities,
            trends=trends,
            competitors=competitors,
            sentiment=sentiment,
            priority=priority,
            confidence=confidence
        )

        llm_briefing = ""

        if self.use_llm:
            llm_briefing = self._call_ollama(prompt)

        if llm_briefing:
            final_briefing = llm_briefing
            generation_mode = "retrieval_augmented_local_llm"
        else:
            final_briefing = self._build_rule_based_briefing(
                user_goal=user_goal,
                goal_type=goal_type,
                risks=risks,
                opportunities=opportunities,
                trends=trends,
                competitors=competitors,
                actions=actions,
                sentiment=sentiment,
                priority=priority,
                confidence=confidence
            )
            generation_mode = "rule_based_fallback"

        used_evidence_ids = [
            item["evidence_id"]
            for item in evidence_items[:3]
            if "evidence_id" in item
        ]

        return {
            "user_goal": user_goal,
            "question": user_goal,
            "goal_type": goal_type,
            "answer": final_briefing,
            "final_briefing": final_briefing,
            "recommendation": actions[0] if actions else "Review retrieved evidence before making a decision.",
            "actions": actions,
            "priority": priority,
            "confidence": confidence,
            "risks": risks,
            "opportunities": opportunities,
            "trends": trends,
            "competitors": competitors,
            "sentiment": sentiment,
            "evidence": evidence_items,
            "used_evidence_ids": used_evidence_ids,
            "generation_mode": generation_mode
        }

    def validate_recommendation_tool(self, result):
        return self.validator.validate(result)

    def _build_llm_prompt(
        self,
        user_goal,
        goal_type,
        evidence_items,
        risks,
        opportunities,
        trends,
        competitors,
        sentiment,
        priority,
        confidence
    ):
        evidence_text = self._format_evidence_for_prompt(evidence_items)

        prompt = f"""
You are an AI CEO Strategic Intelligence Agent for BMW EV strategy.

Your task is to generate a concise CEO-level executive briefing using only the provided evidence.

User goal:
{user_goal}

Detected goal type:
{goal_type}

Priority:
{priority}

Confidence:
{confidence}

Evidence sentiment:
{sentiment.get("label", "Unknown")}

Retrieved evidence:
{evidence_text}

Extracted risk signals:
{json.dumps(risks, indent=2)}

Extracted opportunity signals:
{json.dumps(opportunities, indent=2)}

Extracted trend signals:
{json.dumps(trends, indent=2)}

Extracted competitor signals:
{json.dumps(competitors, indent=2)}

Rules:
- Use only the retrieved evidence and extracted signals.
- Do not invent facts.
- Do not mention unsupported claims.
- Write like a CEO strategy briefing, not like debug output.
- Give a specific recommendation for BMW.
- Mention evidence IDs when supporting important points.
- Keep the answer clear and professional.

Required structure:

Executive Recommendation:
Write 2 to 3 sentences with the main strategic recommendation.

Why this matters:
Explain the business reason in 2 to 3 sentences.

Key Evidence:
List 3 to 5 evidence-supported points with evidence IDs.

Main Risks:
List the strongest risks.

Main Opportunities:
List the strongest opportunities.

Recommended Next Actions:
List 3 concrete actions BMW should take.

Final Priority:
State priority and confidence.
"""
        return prompt.strip()

    def _format_evidence_for_prompt(self, evidence_items):
        lines = []

        for item in evidence_items:
            evidence_id = item.get("evidence_id", "")
            title = item.get("title", "Untitled")
            source = item.get("source", "Unknown")
            category = item.get("category", "Unknown")
            similarity = item.get("similarity", "")
            text = self._clean_text(item.get("text", ""))

            if len(text) > 900:
                text = text[:900] + "..."

            lines.append(
                f"""
Evidence ID: {evidence_id}
Title: {title}
Source: {source}
Category: {category}
Similarity: {similarity}
Text: {text}
"""
            )

        return "\n".join(lines)

    def _call_ollama(self, prompt):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                return ""

            data = response.json()
            return data.get("response", "").strip()

        except Exception:
            return ""

    def _extract_signals(self, evidence_items, theme_keywords, signal_type, max_items=3):
        signals = []

        for item in evidence_items:
            text = self._clean_text(item.get("text", ""))
            title = self._clean_text(item.get("title", "Untitled"))
            source = item.get("source", "Unknown")
            evidence_id = item.get("evidence_id", "")
            combined_text = f"{title} {text}".lower()

            if not text:
                continue

            for theme, keywords in theme_keywords.items():
                matched_keywords = [
                    keyword
                    for keyword in keywords
                    if self._keyword_in_text(keyword, combined_text)
                ]

                if not matched_keywords:
                    continue

                phrase_hits = sum(1 for keyword in matched_keywords if " " in keyword)
                title_hits = sum(
                    1 for keyword in matched_keywords
                    if self._keyword_in_text(keyword, title.lower())
                )

                score = (
                    len(matched_keywords) * 1.0
                    + phrase_hits * 0.8
                    + title_hits * 0.6
                )

                signals.append({
                    "title": theme,
                    "theme": theme,
                    "reason": (
                        f"Matched {signal_type} indicators in retrieved evidence: "
                        f"{', '.join(matched_keywords)}."
                    ),
                    "matched_keywords": ", ".join(matched_keywords),
                    "evidence_preview": self._build_preview(text, matched_keywords),
                    "source": source,
                    "evidence_id": evidence_id,
                    "score": round(score, 2)
                })

        signals = self._deduplicate_signals(signals)
        signals = sorted(signals, key=lambda item: item["score"], reverse=True)

        return signals[:max_items]

    def _deduplicate_signals(self, signals):
        unique = {}

        for signal in signals:
            key = signal.get("theme", "")

            if key not in unique:
                unique[key] = signal
            elif signal["score"] > unique[key]["score"]:
                unique[key] = signal

        return list(unique.values())

    def _keyword_in_text(self, keyword, text):
        keyword = keyword.lower().strip()
        text = text.lower()

        if " " in keyword:
            return keyword in text

        pattern = r"\b" + re.escape(keyword) + r"\b"
        return re.search(pattern, text) is not None

    def _build_preview(self, text, matched_keywords, max_length=260):
        text = self._clean_text(text)

        if not text:
            return ""

        first_position = -1
        text_lower = text.lower()

        for keyword in matched_keywords:
            position = text_lower.find(keyword.lower())

            if position != -1:
                first_position = position
                break

        if first_position == -1:
            return text[:max_length]

        start = max(0, first_position - 80)
        end = min(len(text), first_position + max_length)

        preview = text[start:end].strip()

        if start > 0:
            preview = "..." + preview

        if end < len(text):
            preview = preview + "..."

        return preview

    def _level_from_score(self, score):
        if score >= 4.0:
            return "High"
        if score >= 2.0:
            return "Medium"
        return "Low"

    def _build_actions(self, goal_type, risks, opportunities, trends, competitors):
        actions = []

        if goal_type == "risk_analysis":
            actions.append("Prioritize mitigation for the strongest evidence-supported risks.")
        elif goal_type == "opportunity_analysis":
            actions.append("Prioritize investment in the strongest evidence-supported opportunities.")
        elif goal_type == "trend_analysis":
            actions.append("Track the strongest market and technology trends before changing strategy.")
        elif goal_type == "competitor_analysis":
            actions.append("Respond to competitor signals using product, pricing, and market positioning actions.")
        else:
            actions.append("Balance EV growth opportunities with risk mitigation before making a strategic decision.")

        if opportunities:
            top_opportunity = opportunities[0]
            actions.append(
                f"Use the opportunity signal '{top_opportunity.get('title', 'Opportunity')}' "
                "to guide product, market, or technology priorities."
            )

        if risks:
            top_risk = risks[0]
            actions.append(
                f"Prepare mitigation for the risk signal '{top_risk.get('title', 'Risk')}'."
            )

        if trends:
            top_trend = trends[0]
            actions.append(
                f"Monitor the trend '{top_trend.get('title', 'Trend')}' as new evidence is collected."
            )

        if competitors:
            top_competitor = competitors[0]
            actions.append(
                f"Track competitor movement related to '{top_competitor.get('title', 'Competitor signal')}'."
            )

        return actions

    def _decide_priority(self, goal_type, risks, opportunities, trends, competitors):
        if goal_type in ["risk_analysis", "competitor_analysis"] and (risks or competitors):
            return "High"

        if goal_type == "opportunity_analysis" and opportunities:
            return "High"

        if goal_type == "strategic_decision" and (risks or opportunities):
            return "High"

        if goal_type == "trend_analysis" and trends:
            return "Medium"

        return "Medium"

    def _decide_confidence(self, evidence_items, risks, opportunities, trends, competitors):
        evidence_count = len(evidence_items)
        signal_count = len(risks) + len(opportunities) + len(trends) + len(competitors)

        if evidence_count >= 5 and signal_count >= 4:
            return "High"

        if evidence_count >= 3 and signal_count >= 2:
            return "Medium"

        return "Low"

    def _build_rule_based_briefing(
        self,
        user_goal,
        goal_type,
        risks,
        opportunities,
        trends,
        competitors,
        actions,
        sentiment,
        priority,
        confidence
    ):
        lines = []

        lines.append(f"CEO Goal: {user_goal}")
        lines.append("")
        lines.append(f"Detected Goal Type: {goal_type}")
        lines.append("")
        lines.append("Executive Recommendation:")
        lines.append(actions[0] if actions else "Review retrieved evidence before making a decision.")
        lines.append("")
        lines.append("Why this matters:")
        lines.append(
            "The recommendation is grounded in retrieved evidence from the repository. "
            "The tools extract risk, opportunity, trend, and competitor signals from retrieved chunks."
        )
        lines.append("")

        lines.append("Risk Signals:")
        if risks:
            for risk in risks:
                lines.append(
                    f"- {risk.get('title', 'Risk')}: {risk.get('reason', '')} "
                    f"[Evidence: {risk.get('evidence_id', '')}]"
                )
        else:
            lines.append("- No strong risk signal was found in the retrieved evidence.")

        lines.append("")
        lines.append("Opportunity Signals:")
        if opportunities:
            for opportunity in opportunities:
                lines.append(
                    f"- {opportunity.get('title', 'Opportunity')}: {opportunity.get('reason', '')} "
                    f"[Evidence: {opportunity.get('evidence_id', '')}]"
                )
        else:
            lines.append("- No strong opportunity signal was found in the retrieved evidence.")

        lines.append("")
        lines.append("Trend Signals:")
        if trends:
            for trend in trends:
                lines.append(
                    f"- {trend.get('title', 'Trend')}: {trend.get('reason', '')} "
                    f"[Evidence: {trend.get('evidence_id', '')}]"
                )
        else:
            lines.append("- No strong trend signal was found in the retrieved evidence.")

        if competitors:
            lines.append("")
            lines.append("Competitive Signals:")
            for competitor in competitors:
                lines.append(
                    f"- {competitor.get('title', 'Competitive signal')}: {competitor.get('reason', '')} "
                    f"[Evidence: {competitor.get('evidence_id', '')}]"
                )

        lines.append("")
        lines.append("Recommended Actions:")
        for action in actions:
            lines.append(f"- {action}")

        lines.append("")
        lines.append(f"Priority: {priority}")
        lines.append(f"Confidence: {confidence}")
        lines.append(f"Evidence Sentiment: {sentiment.get('label', 'Unknown')}")

        return "\n".join(lines)

    def _clean_text(self, text):
        text = "" if text is None else str(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


if __name__ == "__main__":
    tools = StrategicTools(top_k=5, use_llm=True)

    goal = "What should BMW do next in its EV strategy?"

    evidence = tools.retrieve_evidence_tool(goal)

    analysis = {
        "risks": tools.analyze_risks_tool(evidence),
        "opportunities": tools.analyze_opportunities_tool(evidence),
        "trends": tools.analyze_trends_tool(evidence),
        "competitors": tools.analyze_competitors_tool(evidence)
    }

    sentiment = tools.sentiment_tool(evidence)

    result = tools.generate_recommendation_tool(
        user_goal=goal,
        goal_type="strategic_decision",
        evidence_items=evidence,
        analysis_results=analysis,
        sentiment=sentiment
    )

    print(result["final_briefing"])
    print("Generation mode:", result["generation_mode"])