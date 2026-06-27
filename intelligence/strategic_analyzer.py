from retrieval.semantic_retriever import BMWStrategicRetriever
from llm.ollama_client import OllamaClient


class CEORecommendationEngine:
    def __init__(self, top_k=8, use_llm=True):
        self.top_k = top_k
        self.use_llm = use_llm

        self.retriever = BMWStrategicRetriever()
        self.llm = OllamaClient()

        self.weak_title_terms = [
            "quick charge",
            "podcast",
            "newsletter",
            "subscribe",
            "comments",
        ]

        self.unsafe_output_terms = [
            "bmw's existing models like the ioniq",
            "bmw’s existing models like the ioniq",
            "bmw's existing models like the mustang",
            "bmw’s existing models like the mustang",
            "market ioniq",
            "market mustang mach-e",
            "toyota partnership",
            "partner with toyota",
            "partnerships with toyota",
            "strategic partnership with toyota",
            "not explicitly stated",
            "implied by industry trends",
            "bmw m5",
            "m5 ev",
        ]

    def clean_evidence_text(self, text):
        if not text:
            return ""

        text = text.replace("\n", " ").strip()

        cut_phrases = [
            "Top comment",
            "Subscribe to",
            "Listen to a recap",
            "New episodes",
            "Subscribe to our podcast",
        ]

        for phrase in cut_phrases:
            if phrase.lower() in text.lower():
                index = text.lower().find(phrase.lower())
                text = text[:index].strip()

        return text

    def is_weak_evidence(self, item):
        title = item.get("title", "").lower()
        text = item.get("text", "").lower()

        for term in self.weak_title_terms:
            if term in title:
                return True

        if len(text.split()) < 60:
            return True

        return False

    def filter_evidence(self, evidence_items):
        filtered = []

        for item in evidence_items:
            if self.is_weak_evidence(item):
                continue

            cleaned_text = self.clean_evidence_text(item["text"])

            if len(cleaned_text.split()) < 60:
                continue

            item_copy = item.copy()
            item_copy["text"] = cleaned_text
            filtered.append(item_copy)

        if not filtered:
            return evidence_items[:5]

        return filtered[:5]

    def combine_evidence_text(self, evidence_items):
        combined = ""

        for item in evidence_items:
            combined += " " + item.get("title", "")
            combined += " " + item.get("text", "")

        return combined.lower()

    def evidence_contains_any(self, evidence_text, keywords):
        for keyword in keywords:
            if keyword.lower() in evidence_text:
                return True
        return False

    def generate_supported_risks(self, evidence_items):
        evidence_text = self.combine_evidence_text(evidence_items)
        risks = []

        if self.evidence_contains_any(
            evidence_text,
            ["china", "sales drop", "profit guidance", "profit", "market conditions", "downturn"]
        ):
            risks.append(
                {
                    "title": "China sales and profit pressure",
                    "category": "Market / Financial Risk",
                    "severity": "High",
                    "reason": (
                        "Retrieved evidence mentions China-related weakness, profit pressure, "
                        "or difficult market conditions."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["tesla", "byd", "mercedes", "audi", "rivian", "lucid", "porsche", "genesis"]
        ):
            risks.append(
                {
                    "title": "Premium EV competitive pressure",
                    "category": "Competitive Risk",
                    "severity": "High",
                    "reason": (
                        "Retrieved evidence mentions several EV competitors and rival luxury EV models."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["cheaper", "price", "pricing", "affordable", "cost less", "starts at"]
        ):
            risks.append(
                {
                    "title": "Pricing pressure in the premium EV segment",
                    "category": "Pricing Risk",
                    "severity": "Medium",
                    "reason": (
                        "Retrieved evidence discusses EV prices and price comparison with rival models."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["combustion", "diesel", "gasoline", "engine", "powertrain", "emissions"]
        ):
            risks.append(
                {
                    "title": "ICE transition and regulatory pressure",
                    "category": "Transition Risk",
                    "severity": "Medium",
                    "reason": (
                        "Retrieved evidence mentions combustion engines, emissions, or transition away from ICE powertrains."
                    ),
                }
            )

        if not risks:
            risks.append(
                {
                    "title": "Insufficient strong risk evidence",
                    "category": "Evidence Limitation",
                    "severity": "Low",
                    "reason": "The retrieved evidence does not strongly support a specific risk theme.",
                }
            )

        return risks[:3]

    def generate_supported_opportunities(self, evidence_items):
        evidence_text = self.combine_evidence_text(evidence_items)
        opportunities = []

        if self.evidence_contains_any(
            evidence_text,
            ["neue klasse", "ix3", "i3", "new class"]
        ):
            opportunities.append(
                {
                    "title": "Accelerate Neue Klasse product momentum",
                    "impact": "High",
                    "reason": (
                        "Retrieved evidence repeatedly mentions Neue Klasse, iX3, or i3 as important BMW EV products."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["800v", "800-volt", "fast charging", "range", "miles", "battery"]
        ):
            opportunities.append(
                {
                    "title": "Use range, battery and fast charging as differentiators",
                    "impact": "High",
                    "reason": (
                        "Retrieved evidence mentions range, charging speed, 800V architecture, or battery improvements."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["electric m3", "m concept", "m series", "performance ev", "quad-motor"]
        ):
            opportunities.append(
                {
                    "title": "Strengthen BMW’s performance EV positioning",
                    "impact": "Medium",
                    "reason": (
                        "Retrieved evidence mentions electric M models or BMW performance EV development."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["luxury", "premium", "suv", "g74", "off-roader", "flagship"]
        ):
            opportunities.append(
                {
                    "title": "Expand premium electric SUV positioning",
                    "impact": "Medium",
                    "reason": (
                        "Retrieved evidence mentions luxury SUVs, premium EV positioning, or BMW's future SUV strategy."
                    ),
                }
            )

        if self.evidence_contains_any(
            evidence_text,
            ["supercharger", "nacs", "charging network"]
        ):
            opportunities.append(
                {
                    "title": "Improve charging access and ownership convenience",
                    "impact": "Medium",
                    "reason": (
                        "Retrieved evidence mentions charging network access, Supercharger access, or NACS-related charging themes."
                    ),
                }
            )

        if not opportunities:
            opportunities.append(
                {
                    "title": "Insufficient strong opportunity evidence",
                    "impact": "Low",
                    "reason": "The retrieved evidence does not strongly support a specific opportunity theme.",
                }
            )

        return opportunities[:3]

    def generate_supported_trends(self, evidence_items):
        evidence_text = self.combine_evidence_text(evidence_items)
        trends = []

        if self.evidence_contains_any(
            evidence_text,
            ["bev", "electric vehicle", "ev market", "electrification", "registrations"]
        ):
            trends.append("EV adoption and electrification continue to shape the market.")

        if self.evidence_contains_any(
            evidence_text,
            ["range", "charging", "battery", "800v", "800-volt"]
        ):
            trends.append("Range, battery performance and fast charging are key EV purchase factors.")

        if self.evidence_contains_any(
            evidence_text,
            ["tesla", "mercedes", "audi", "byd", "rivian", "lucid"]
        ):
            trends.append("Premium EV competition is intensifying.")

        if self.evidence_contains_any(
            evidence_text,
            ["china", "europe", "eu", "germany"]
        ):
            trends.append("Europe and China remain important strategic markets for BMW.")

        if not trends:
            trends.append("The retrieved evidence shows general EV market transformation.")

        return trends[:3]

    def generate_supported_actions(self, risks, opportunities, evidence_items):
        evidence_text = self.combine_evidence_text(evidence_items)
        actions = []

        opportunity_titles = " ".join([item["title"] for item in opportunities]).lower()
        risk_titles = " ".join([item["title"] for item in risks]).lower()

        if "neue klasse" in opportunity_titles:
            actions.append(
                "Accelerate Neue Klasse rollout and use iX3/i3 as core EV proof points."
            )

        if "range" in opportunity_titles or "charging" in opportunity_titles:
            actions.append(
                "Make battery range, 800V architecture, and fast charging central to BMW's EV positioning."
            )

        if "performance" in opportunity_titles:
            actions.append(
                "Use electric M models as a performance halo for BMW's EV transition."
            )

        if "premium electric suv" in opportunity_titles:
            actions.append(
                "Evaluate premium electric SUV segments where BMW can defend luxury positioning."
            )

        if "competitive" in risk_titles or self.evidence_contains_any(
            evidence_text,
            ["tesla", "byd", "mercedes", "audi", "rivian", "lucid"]
        ):
            actions.append(
                "Monitor premium EV competitors closely and defend BMW's positioning through product quality, technology and pricing discipline."
            )

        if "china" in risk_titles or "profit" in risk_titles:
            actions.append(
                "Treat China sales weakness and profit pressure as strategic constraints when prioritizing EV investments."
            )

        if "ice transition" in risk_titles:
            actions.append(
                "Manage the transition from combustion powertrains while protecting cash flow for electrification."
            )

        # Remove duplicates while keeping order
        unique_actions = []
        for action in actions:
            if action not in unique_actions:
                unique_actions.append(action)

        if not unique_actions:
            unique_actions.append(
                "Prioritize BMW EV decisions only where retrieved evidence provides clear support."
            )

        return unique_actions[:4]

    def decide_priority(self, risks, opportunities):
        high_risks = [risk for risk in risks if risk.get("severity") == "High"]
        high_opportunities = [opp for opp in opportunities if opp.get("impact") == "High"]

        if high_risks or high_opportunities:
            return "High"

        if len(risks) >= 2 or len(opportunities) >= 2:
            return "Medium"

        return "Low"

    def decide_confidence(self, evidence_items):
        if not evidence_items:
            return "Low"

        avg_similarity = sum(
            item["similarity_score"] for item in evidence_items
        ) / len(evidence_items)

        if avg_similarity >= 0.63:
            return "High"
        elif avg_similarity >= 0.56:
            return "Medium"
        else:
            return "Low"

    def build_evidence_summary(self, evidence_items):
        evidence_lines = []

        for index, item in enumerate(evidence_items, start=1):
            evidence_lines.append(
                {
                    "rank": index,
                    "source": item["source"],
                    "category": item["category"],
                    "title": item["title"],
                    "url": item["url"],
                    "similarity": round(item["similarity_score"], 4),
                    "preview": item["text"][:350],
                }
            )

        return evidence_lines

    def build_rule_based_briefing(self, question, risks, opportunities, trends, actions, priority, confidence, evidence_items):
        lines = []

        lines.append("1. Executive recommendation")
        lines.append(
            f"Based on the retrieved evidence, BMW should focus on {opportunities[0]['title'].lower()} "
            f"while actively managing {risks[0]['title'].lower()}."
        )
        lines.append(
            "The recommendation is grounded in retrieved BMW EV, competitor, product, and market evidence."
        )

        lines.append("\n2. Why this matters")
        for trend in trends:
            lines.append(f"- {trend}")

        lines.append("\n3. Key risks")
        for risk in risks:
            lines.append(
                f"- {risk['title']} ({risk['severity']}): {risk['reason']}"
            )

        lines.append("\n4. Key opportunities")
        for opportunity in opportunities:
            lines.append(
                f"- {opportunity['title']} ({opportunity['impact']} impact): {opportunity['reason']}"
            )

        lines.append("\n5. Evidence-based action plan")
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {action}")

        lines.append("\n6. Confidence")
        lines.append(
            f"Confidence: {confidence}. This is based on the similarity of retrieved evidence and the number of directly supported themes."
        )

        return "\n".join(lines)

    def build_llm_prompt(self, question, risks, opportunities, trends, actions, priority, confidence, evidence_items):
        evidence_text = ""

        for index, item in enumerate(evidence_items, start=1):
            evidence_text += f"\nEvidence {index}\n"
            evidence_text += f"Source: {item['source']}\n"
            evidence_text += f"Category: {item['category']}\n"
            evidence_text += f"Title: {item['title']}\n"
            evidence_text += f"Text: {item['text'][:450]}\n"

        risk_text = "\n".join(
            [f"- {risk['title']}: {risk['reason']}" for risk in risks]
        )

        opportunity_text = "\n".join(
            [f"- {opp['title']}: {opp['reason']}" for opp in opportunities]
        )

        trend_text = "\n".join(
            [f"- {trend}" for trend in trends]
        )

        action_text = "\n".join(
            [f"- {action}" for action in actions]
        )

        prompt = f"""
You are a careful CEO strategy writing assistant for BMW.

Important:
You are NOT allowed to create new facts, new companies, new partnerships, or new vehicle models.
Your task is only to rewrite the supported points below into professional CEO briefing language.

Strict rules:
- Use only the supported risks, opportunities, trends, actions, and evidence below.
- Do not add Toyota partnership.
- Do not say IONIQ 5 or Mustang Mach-E are BMW models.
- Do not mention BMW M5.
- Do not add unsupported future dates.
- Do not use phrases like "as soon as possible" unless the supported action explicitly says so.
- Do not write "not explicitly stated" or "implied by industry trends".
- If a point is not supported, omit it.
- Keep the answer concise.
- Do not add new recommendations beyond the supported action list.

User question:
{question}

Priority:
{priority}

Confidence:
{confidence}

Supported risks:
{risk_text}

Supported opportunities:
{opportunity_text}

Supported trends:
{trend_text}

Supported actions:
{action_text}

Retrieved evidence for reference:
{evidence_text}

Write the final answer in this exact format:

1. Executive recommendation
2. Why this matters
3. Key risks
4. Key opportunities
5. Evidence-based action plan
6. Confidence
"""

        return prompt

    def is_unsafe_output(self, output):
        output_lower = output.lower()

        for term in self.unsafe_output_terms:
            if term in output_lower:
                return True

        if "partnership" in output_lower and "toyota" in output_lower:
            return True

        return False

    def generate_llm_briefing(self, question, risks, opportunities, trends, actions, priority, confidence, evidence_items):
        prompt = self.build_llm_prompt(
            question,
            risks,
            opportunities,
            trends,
            actions,
            priority,
            confidence,
            evidence_items
        )

        llm_output = self.llm.generate(prompt, temperature=0.0)

        if "Ollama is not running" in llm_output:
            return None

        if "Ollama generation failed" in llm_output:
            return None

        if self.is_unsafe_output(llm_output):
            return None

        return llm_output

    def generate_recommendation(self, question):
        raw_evidence = self.retriever.retrieve(question, top_k=self.top_k)
        evidence_items = self.filter_evidence(raw_evidence)

        risks = self.generate_supported_risks(evidence_items)
        opportunities = self.generate_supported_opportunities(evidence_items)
        trends = self.generate_supported_trends(evidence_items)
        actions = self.generate_supported_actions(risks, opportunities, evidence_items)

        priority = self.decide_priority(risks, opportunities)
        confidence = self.decide_confidence(evidence_items)

        fallback_briefing = self.build_rule_based_briefing(
            question,
            risks,
            opportunities,
            trends,
            actions,
            priority,
            confidence,
            evidence_items
        )

        if self.use_llm:
            llm_briefing = self.generate_llm_briefing(
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
                generation_mode = "LLM rewritten from rule-based supported points"
            else:
                final_briefing = fallback_briefing
                generation_mode = "Rule-based fallback used because LLM output was unsafe or unavailable"
        else:
            final_briefing = fallback_briefing
            generation_mode = "Rule-based only"

        return {
            "question": question,
            "priority": priority,
            "confidence": confidence,
            "risks": risks,
            "opportunities": opportunities,
            "trends": trends,
            "actions": actions,
            "final_briefing": final_briefing,
            "evidence": self.build_evidence_summary(evidence_items),
            "generation_mode": generation_mode,
        }

    def print_result(self, result):
        print("\n" + "=" * 90)
        print("CEO STRATEGIC RECOMMENDATION - SAFE VERSION")
        print("=" * 90)

        print("\nQuestion:")
        print(result["question"])

        print("\nPriority:")
        print(result["priority"])

        print("\nConfidence:")
        print(result["confidence"])

        print("\nGeneration mode:")
        print(result["generation_mode"])

        print("\nFinal CEO briefing:")
        print(result["final_briefing"])

        print("\nSupported risks:")
        for risk in result["risks"]:
            print(f"- {risk['title']} | {risk['severity']} | {risk['category']}")

        print("\nSupported opportunities:")
        for opportunity in result["opportunities"]:
            print(f"- {opportunity['title']} | {opportunity['impact']} impact")

        print("\nSupported actions:")
        for action in result["actions"]:
            print(f"- {action}")

        print("\nSupporting evidence:")
        for item in result["evidence"]:
            print("-" * 90)
            print(f"Rank: {item['rank']}")
            print(f"Similarity: {item['similarity']}")
            print(f"Source: {item['source']}")
            print(f"Category: {item['category']}")
            print(f"Title: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"Preview: {item['preview']}...")


if __name__ == "__main__":
    engine = CEORecommendationEngine(top_k=8, use_llm=True)

    question = "What should BMW do next in EV strategy?"

    result = engine.generate_recommendation(question)
    engine.print_result(result)
