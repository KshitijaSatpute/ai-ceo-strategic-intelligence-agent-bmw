class TrendDetector:
    """
    Detects high-level EV market and BMW strategy trends from retrieved evidence.

    This detector is used to make the intelligence engine easier to explain.
    It returns short trend statements that can support CEO briefing and recommendations.
    """

    def __init__(self):
        self.trend_rules = [
            {
                "keywords": ["ev sales", "electric vehicle sales", "registrations", "demand"],
                "trend": "EV demand and market adoption are continuing to shape automotive strategy."
            },
            {
                "keywords": ["charging", "fast charger", "800v", "charging station"],
                "trend": "Charging speed and charging infrastructure are becoming important EV competition factors."
            },
            {
                "keywords": ["battery", "solid-state", "lfp", "range"],
                "trend": "Battery technology and driving range are becoming key areas of EV differentiation."
            },
            {
                "keywords": ["tesla", "byd", "hyundai", "kia", "ford", "rivian"],
                "trend": "Competition in the EV market is increasing from both legacy automakers and EV-focused companies."
            },
            {
                "keywords": ["china", "europe", "eu", "policy", "mandate"],
                "trend": "Regional market conditions and policy changes are influencing EV strategy decisions."
            },
            {
                "keywords": ["neue klasse", "ix3", "i3", "electric m"],
                "trend": "BMW is using new EV products and platforms to strengthen its future electric vehicle positioning."
            }
        ]

    def detect_trends(self, evidence_items):
        detected_trends = []
        seen_trends = set()

        for item in evidence_items:
            text = self._get_combined_text(item)

            for rule in self.trend_rules:
                if self._has_keyword(text, rule["keywords"]):
                    if rule["trend"] in seen_trends:
                        continue

                    detected_trends.append(rule["trend"])
                    seen_trends.add(rule["trend"])

        if not detected_trends:
            detected_trends.append(
                "The retrieved evidence shows ongoing strategic movement in the EV market."
            )

        return detected_trends

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
            "title": "BMW iX3 range and charging performance improves",
            "source": "Electrek",
            "preview": "BMW improves EV range and charging capability."
        }
    ]

    detector = TrendDetector()
    trends = detector.detect_trends(sample_evidence)

    for trend in trends:
        print(trend)