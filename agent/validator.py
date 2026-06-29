class AgentValidator:
    def validate(self, result):
        checks = []
        issues = []

        answer = result.get("answer") or result.get("final_briefing")
        evidence = result.get("evidence", [])
        used_evidence_ids = result.get("used_evidence_ids", [])

        if answer and len(answer.strip()) > 50:
            checks.append("Answer exists")
        else:
            issues.append("Answer is missing or too short")

        if evidence:
            checks.append("Evidence exists")
        else:
            issues.append("No supporting evidence found")

        evidence_ids = [
            item.get("evidence_id") for item in evidence
            if item.get("evidence_id")
        ]

        invalid_ids = [
            evidence_id for evidence_id in used_evidence_ids
            if evidence_id not in evidence_ids
        ]

        if used_evidence_ids and not invalid_ids:
            checks.append("Valid evidence IDs are used")
        else:
            issues.append("Valid evidence IDs are missing or incorrect")

        if result.get("recommendation") or result.get("actions"):
            checks.append("Recommendation is included")
        else:
            issues.append("Recommendation is missing")

        if result.get("risks") is not None:
            checks.append("Risk section is present")
        else:
            issues.append("Risk section is missing")

        if result.get("priority") in ["High", "Medium", "Low"]:
            checks.append("Priority is mentioned")
        else:
            issues.append("Priority is missing or invalid")

        if result.get("confidence") in ["High", "Medium", "Low"]:
            checks.append("Confidence is mentioned")
        else:
            issues.append("Confidence is missing or invalid")

        if issues:
            status = "failed"
            approved = False
            decision = "Recommendation needs review before approval."
        else:
            status = "passed"
            approved = True
            decision = "Recommendation approved."

        return {
            "status": status,
            "approved": approved,
            "checks": checks,
            "issues": issues,
            "decision": decision
        }