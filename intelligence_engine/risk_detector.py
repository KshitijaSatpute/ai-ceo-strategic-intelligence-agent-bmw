class RiskDetector:
    """
    Detects strategic, financial, operational, and competitive risks
    from retrieved evidence chunks.

    This is a simple explainable detector used for the academic prototype.
    It uses keyword-based logic so that the result is easy to explain
    during viva and live coding.
    """

    def __init__(self):
        self.risk_rules = [
            {
                "keywords": ["china", "sales drop", "profit", "margin", "guidance"],
                "title": "China sales and profit pressure",
                "category": "Financial Risk",
                "severity": "High",
                "reason": "Weakness in China or profit pressure can directly affect BMW's financial performance."
            },
            {
                "keywords": ["tesla", "byd", "competition", "competitor", "price war", "pricing"],
                "title": "Competitive pressure from EV rivals",
                "category": "Strategic Risk",
                "severity": "High",
                "reason": "Strong EV competitors can pressure BMW's pricing, market share, and brand positioning."
            },
            {
                "keywords": ["battery", "charging", "range", "800v", "solid-state"],
                "title": "Battery and charging execution risk",
                "category": "Operational Risk",
                "severity": "Medium",
                "reason": "Battery performance, charging speed, and range are important customer decision factors in EVs."
            },
            {
                "keywords": ["combustion", "ice", "transition", "hybrid"],
                "title": "Transition risk from combustion to EVs",
                "category": "Strategic Risk",
                "severity": "Medium",
                "reason": "BMW must balance existing combustion demand while investing heavily in electric vehicles."
            },
            {
                "keywords": ["regulation", "mandate", "eu", "policy", "emission"],
                "title": "Regulatory and policy risk",
                "category": "Regulatory Risk",
                "severity": "Medium",
                "reason": "Changing EV policies, emissions rules, and mandates can affect BMW's product and market strategy."
            }
        ]

    def detect_risks(self, evidence_items):
        detected_risks = []
        seen_titles = set()

        for item in evidence_items:
            text = self._get_combined_text(item)

            for rule in self.risk_rules:
                if self._has_keyword(text, rule["keywords"]):
                    if rule["title"] in seen_titles:
                        continue

                    detected_risks.append({
                        "title": rule["title"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "reason": rule["reason"],
                        "evidence_title": item.get("title", "Unknown title"),
                        "evidence_source": item.get("source", "Unknown source")
                    })

                    seen_titles.add(rule["title"])

        if not detected_risks:
            detected_risks.append({
                "title": "General EV market uncertainty",
                "category": "Strategic Risk",
                "severity": "Medium",
                "reason": "The retrieved evidence indicates uncertainty in the EV market environment.",
                "evidence_title": "Retrieved evidence",
                "evidence_source": "Knowledge base"
            })

        return detected_risks

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
            "title": "BMW cuts profit guidance as China sales drop",
            "source": "BMWBlog",
            "preview": "BMW faces pressure in China and lower profit guidance."
        }
    ]

    detector = RiskDetector()
    risks = detector.detect_risks(sample_evidence)

    for risk in risks:
        print(risk)