class AgentValidator:
    def validate(self, result):
        validation = {
            "status": "passed",
            "checks": [],
            "warnings": []
        }

        evidence = result.get("evidence", [])
        actions = result.get("actions", [])
        confidence = result.get("confidence", "")
        final_briefing = result.get("final_briefing", "")

        if evidence:
            validation["checks"].append("Supporting evidence is available.")
        else:
            validation["status"] = "failed"
            validation["warnings"].append("No supporting evidence found.")

        if actions:
            validation["checks"].append("Recommended actions are available.")
        else:
            validation["status"] = "failed"
            validation["warnings"].append("No recommended actions generated.")

        if confidence in ["High", "Medium"]:
            validation["checks"].append("Confidence is acceptable.")
        else:
            validation["warnings"].append("Confidence is low.")

        if len(final_briefing.strip()) > 100:
            validation["checks"].append("Final briefing is generated.")
        else:
            validation["status"] = "failed"
            validation["warnings"].append("Final briefing is too short or missing.")

        unsafe_terms = [
            "not explicitly stated",
            "implied by industry trends",
            "toyota partnership",
            "bmw's existing models like the ioniq",
            "bmw’s existing models like the ioniq",
            "mustang mach-e are bmw models"
        ]

        briefing_lower = final_briefing.lower()

        for term in unsafe_terms:
            if term in briefing_lower:
                validation["status"] = "failed"
                validation["warnings"].append(f"Unsafe unsupported phrase found: {term}")

        return validation


if __name__ == "__main__":
    validator = AgentValidator()

    sample_result = {
        "evidence": [{"title": "sample evidence"}],
        "actions": ["sample action"],
        "confidence": "High",
        "final_briefing": "This is a sample evidence-supported CEO briefing for validation testing."
    }

    print(validator.validate(sample_result))