import streamlit as st
import pandas as pd


@st.cache_resource
def load_ai_ceo_agent():
    from agents.ceo_agent import AICEOAgent

    agent = AICEOAgent(
        top_k=8,
        use_llm=True
    )
    return agent


@st.cache_data
def load_sentiment_results():
    from intelligence_engine.sentiment_analyzer import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    return analyzer.get_sentiment_summary()


def get_unique_evidence_items(result, limit=None):
    unique_items = []
    seen_keys = set()

    for item in result.get("evidence", []):
        url = str(item.get("url", "")).strip().lower()
        title = str(item.get("title", "")).strip().lower()
        source = str(item.get("source", "")).strip().lower()

        if url:
            key = url
        else:
            key = f"{title}|{source}"

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_items.append(item)

        if limit is not None and len(unique_items) >= limit:
            break

    return unique_items


def get_evidence_text(result, limit=3):
    evidence_titles = []

    for item in get_unique_evidence_items(result, limit=limit):
        title = item.get("title", "Unknown title")
        source = item.get("source", "Unknown source")
        evidence_titles.append(f"{title} ({source})")

    return " | ".join(evidence_titles)


def get_max_risk_level(result):
    risks = result.get("risks", [])

    for risk in risks:
        if risk.get("severity") == "High":
            return "High"

    for risk in risks:
        if risk.get("severity") == "Medium":
            return "Medium"

    return "Low"


def build_opportunity_monitor_table(result):
    rows = []
    evidence_text = get_evidence_text(result)
    confidence = result.get("confidence", "Medium")

    for opportunity in result.get("opportunities", []):
        rows.append({
            "Opportunity Title": opportunity.get("title", "Unknown opportunity"),
            "Impact Level": opportunity.get("impact", "Medium"),
            "Evidence": evidence_text,
            "Confidence Score": confidence
        })

    return pd.DataFrame(rows)


def build_risk_monitor_table(result):
    rows = []
    evidence_text = get_evidence_text(result)
    confidence = result.get("confidence", "Medium")

    for risk in result.get("risks", []):
        rows.append({
            "Risk Title": risk.get("title", "Unknown risk"),
            "Risk Category": risk.get("category", "Strategic Risk"),
            "Severity Level": risk.get("severity", "Medium"),
            "Evidence": evidence_text,
            "Confidence Score": confidence
        })

    return pd.DataFrame(rows)


def estimate_expected_impact(action):
    action_lower = action.lower()

    if "neue klasse" in action_lower or "ix3" in action_lower or "i3" in action_lower:
        return "Market differentiation, stronger EV product positioning, and customer acquisition"

    if "range" in action_lower or "charging" in action_lower or "800v" in action_lower or "battery" in action_lower:
        return "Competitive advantage, improved customer perception, and premium EV differentiation"

    if "performance" in action_lower or "electric m" in action_lower:
        return "Brand strengthening, premium positioning, and performance-based differentiation"

    if "china" in action_lower or "profit" in action_lower:
        return "Margin protection, market stability, and reduced exposure to regional weakness"

    if "competitor" in action_lower or "pricing" in action_lower or "tesla" in action_lower or "byd" in action_lower:
        return "Improved competitive response, pricing discipline, and market share protection"

    return "Strategic focus, improved decision-making, and better market positioning"


def estimate_risk_level(action, result):
    action_lower = action.lower()

    if "china" in action_lower or "profit" in action_lower:
        return "High"

    if "competitor" in action_lower or "pricing" in action_lower:
        return "High"

    if "tesla" in action_lower or "byd" in action_lower:
        return "High"

    if "combustion" in action_lower or "ice" in action_lower:
        return "Medium"

    return get_max_risk_level(result)


def estimate_risk_assessment(action, result):
    action_lower = action.lower()

    if "china" in action_lower or "profit" in action_lower:
        return "Financial risk: High | Strategic risk: Medium | Operational risk: Low"

    if "competitor" in action_lower or "pricing" in action_lower or "tesla" in action_lower or "byd" in action_lower:
        return "Strategic risk: High | Financial risk: Medium | Operational risk: Low"

    if "range" in action_lower or "charging" in action_lower or "800v" in action_lower or "battery" in action_lower:
        return "Operational risk: Medium | Financial risk: Medium | Strategic risk: Low"

    if "neue klasse" in action_lower or "ix3" in action_lower or "i3" in action_lower:
        return "Strategic risk: Medium | Financial risk: Medium | Operational risk: Medium"

    if "performance" in action_lower or "electric m" in action_lower:
        return "Strategic risk: Medium | Financial risk: Low | Operational risk: Low"

    return "Strategic risk: Medium | Financial risk: Medium | Operational risk: Low"


def build_recommendation_table(result):
    rows = []
    evidence_text = get_evidence_text(result)

    for action in result.get("actions", []):
        rows.append({
            "Recommendation": action,
            "Priority": result.get("priority", "Medium"),
            "Supporting Evidence": evidence_text,
            "Expected Impact": estimate_expected_impact(action),
            "Risk Level": estimate_risk_level(action, result),
            "Risk Assessment": estimate_risk_assessment(action, result)
        })

    return pd.DataFrame(rows)


def display_evidence(result):
    unique_evidence = get_unique_evidence_items(result)

    for display_rank, item in enumerate(unique_evidence, start=1):
        title = item.get("title", "Unknown title")
        source = item.get("source", "Unknown source")

        with st.expander(
            f"Evidence {display_rank}: {title} | {source}"
        ):
            st.write(f"Similarity score: {item.get('similarity', 'N/A')}")
            st.write(f"Category: {item.get('category', 'N/A')}")
            st.write(f"Source: {source}")

            if item.get("url"):
                st.markdown(f"[Open source article]({item['url']})")

            st.write(item.get("preview", "No preview available."))


def safe_dataframe(df):
    st.dataframe(
        df,
        width="stretch"
    )


def build_ceo_briefing_summary(result):
    risks = result.get("risks", [])
    opportunities = result.get("opportunities", [])
    trends = result.get("trends", [])
    actions = result.get("actions", [])
    evidence_items = get_unique_evidence_items(result, limit=3)

    briefing_lines = []

    briefing_lines.append("### 1. What happened?")

    if trends:
        for trend in trends[:3]:
            briefing_lines.append(f"- {trend}")

    if risks:
        for risk in risks[:2]:
            briefing_lines.append(
                f"- The system identified **{risk.get('title', 'a strategic risk')}** as a key risk area."
            )

    if opportunities:
        for opportunity in opportunities[:2]:
            briefing_lines.append(
                f"- The system identified **{opportunity.get('title', 'a strategic opportunity')}** as a key opportunity."
            )

    briefing_lines.append("")
    briefing_lines.append("### 2. Why does it matter?")

    if risks:
        for risk in risks[:3]:
            briefing_lines.append(
                f"- **{risk.get('title', 'Risk')}** matters because {risk.get('reason', 'it may affect BMW’s EV strategy and market position')}"
            )

    if opportunities:
        for opportunity in opportunities[:3]:
            briefing_lines.append(
                f"- **{opportunity.get('title', 'Opportunity')}** matters because {opportunity.get('reason', 'it can support BMW’s EV growth and differentiation')}"
            )

    briefing_lines.append("")
    briefing_lines.append("### 3. What should BMW management do next?")

    if actions:
        for index, action in enumerate(actions[:5], start=1):
            briefing_lines.append(f"{index}. {action}")
    else:
        briefing_lines.append(
            "- Management should review the retrieved evidence and prioritize the highest-impact strategic actions."
        )

    briefing_lines.append("")
    briefing_lines.append("### 4. Supporting evidence")

    if evidence_items:
        for index, item in enumerate(evidence_items, start=1):
            title = item.get("title", "Unknown title")
            source = item.get("source", "Unknown source")
            briefing_lines.append(f"- Evidence {index}: {title} ({source})")
    else:
        briefing_lines.append("- No supporting evidence available.")

    briefing_lines.append("")
    briefing_lines.append("### 5. Confidence")
    briefing_lines.append(f"- {result.get('confidence', 'Medium')}")

    return "\n".join(briefing_lines)