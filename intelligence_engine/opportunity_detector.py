class OpportunityDetector:
    """
    Detects strategic opportunities from retrieved evidence chunks.

    The logic is intentionally simple and explainable for the academic prototype.
    It maps evidence keywords to BMW EV strategy opportunities.
    """

    def __init__(self):
        self.opportunity_rules = [
            {
                "keywords": ["neue klasse", "ix3", "i3"],
                "title": "Accelerate Neue Klasse EV momentum",
                "impact": "High",
                "reason": "Neue Klasse can strengthen BMW's next-generation EV positioning and product differentiation."
            },
            {
                "keywords": ["range", "500 miles", "charging", "800v", "battery"],
                "title": "Use range and charging as premium EV differentiators",
                "impact": "High",
                "reason": "Better range and faster charging can improve customer confidence and competitive positioning."
            },
            {
                "keywords": ["electric m", "performance", "m3", "sport"],
                "title": "Expand premium performance EV positioning",
                "impact": "Medium",
                "reason": "Performance EVs can protect BMW's brand identity in the electric vehicle transition."
            },
            {
                "keywords": ["smart home", "energy", "charging station", "home charging"],
                "title": "Connect EV strategy with smart charging and energy services",
                "impact": "Medium",
                "reason": "Charging and energy services can improve ownership experience and customer retention."
            },
            {
                "keywords": ["demand", "order", "preorder", "sales growth"],
                "title": "Convert early EV demand into market share growth",
                "impact": "High",
                "reason": "Strong demand signals can help BMW prioritize high-potential EV launches and production planning."
            }
        ]

    def detect_opportunities(self, evidence_items):
        detected_opportunities = []
        seen_titles = set()

        for item in evidence_items:
            text = self._get_combined_text(item)

            for rule in self.opportunity_rules:
                if self._has_keyword(text, rule["keywords"]):
                    if rule["title"] in seen_titles:
                        continue

                    detected_opportunities.append({
                        "title": rule["title"],
                        "impact": rule["impact"],
                        "reason": rule["reason"],
                        "evidence_title": item.get("title", "Unknown title"),
                        "evidence_source": item.get("source", "Unknown source")
                    })

                    seen_titles.add(rule["title"])

        if not detected_opportunities:
            detected_opportunities.append({
                "title": "Strengthen BMW's EV strategy using retrieved market signals",
                "impact": "Medium",
                "reason": "The retrieved evidence can support BMW's strategic planning in the EV market.",
                "evidence_title": "Retrieved evidence",
                "evidence_source": "Knowledge base"
            })

        return detected_opportunities

    def _get_combined_text(self, item):
        fields = [
            item.get("title", ""),
            item.get("preview", ""),
            item.get("text", ""),
            item.get("content", ""),
            item.get("category", "")
        ]

        return " ".join(str(field).lower() for field in fields)

    def _has_keyword(self, text, keywords):
        return any(keyword in text for keyword in keywords)


if __name__ == "__main__":
    sample_evidence = [
        {
            "title": "BMW iX3 drives 500 miles on a single charge",
            "source": "Electrek",
            "preview": "The new BMW iX3 shows strong range and charging potential."
        }
    ]

    detector = OpportunityDetector()
    opportunities = detector.detect_opportunities(sample_evidence)

    for opportunity in opportunities:
        print(opportunity)