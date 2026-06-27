import streamlit as st
import pandas as pd


@st.cache_resource
def load_ai_ceo_agent():
    from agent.ai_ceo_agent import StrategicAgent as AICEOAgent

    agent = AICEOAgent(
        top_k=8,
        use_llm=True
    )
    return agent


@st.cache_data
def load_sentiment_results():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as SentimentAnalyzer

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
    df = df.copy()

    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].astype(str)

    st.dataframe(
        df,
        width="stretch"
    )
    
def build_ceo_briefing_summary(result):
    question = result.get("question", "CEO strategy question")
    risks = result.get("risks", [])
    opportunities = result.get("opportunities", [])
    trends = result.get("trends", [])
    actions = result.get("actions", [])
    confidence = result.get("confidence", "Medium")

    evidence_items = get_unique_evidence_items(result, limit=3)

    question_lower = question.lower()

    def get_evidence_url(item):
        return (
            item.get("url")
            or item.get("source_url")
            or item.get("article_url")
            or item.get("link")
        )

    def get_evidence_chunk(item):
        chunk_text = (
            item.get("chunk_text")
            or item.get("text")
            or item.get("content")
            or item.get("preview")
            or item.get("snippet")
            or ""
        )

        chunk_text = str(chunk_text).strip()

        if len(chunk_text) > 650:
            chunk_text = chunk_text[:650].rsplit(" ", 1)[0] + "..."

        return chunk_text

    briefing_lines = []

    # Do not add "Executive Summary" here because the tab already displays that heading.
    briefing_lines.append(f"**CEO Question:** {question}")
    briefing_lines.append("")

    briefing_lines.append("### 1. What happened?")

    if "risk" in question_lower:
        briefing_lines.append(
            "- The retrieved evidence mainly highlights strategic risks in BMW's EV transition."
        )
    elif "opportunit" in question_lower or "neue klasse" in question_lower:
        briefing_lines.append(
            "- The retrieved evidence mainly highlights opportunities around BMW's EV platform, products, and technology positioning."
        )
    elif "battery" in question_lower or "charging" in question_lower:
        briefing_lines.append(
            "- The retrieved evidence mainly highlights battery range, charging speed, and EV technology trends."
        )
    elif "tesla" in question_lower or "byd" in question_lower or "competition" in question_lower:
        briefing_lines.append(
            "- The retrieved evidence mainly highlights competitive pressure in the EV market."
        )
    else:
        briefing_lines.append(
            "- The retrieved evidence highlights key strategic signals around BMW's EV strategy."
        )

    if trends:
        for trend in trends[:2]:
            briefing_lines.append(f"- Trend signal: {trend}")

    if risks:
        for risk in risks[:2]:
            briefing_lines.append(
                f"- Risk signal: {risk.get('title', 'Strategic risk')}."
            )

    if opportunities:
        for opportunity in opportunities[:2]:
            briefing_lines.append(
                f"- Opportunity signal: {opportunity.get('title', 'Strategic opportunity')}."
            )

    briefing_lines.append("")

    briefing_lines.append("### 2. Why does it matter?")

    if "risk" in question_lower:
        briefing_lines.append(
            "- These risks matter because they can affect BMW's EV market share, pricing power, profitability, and transition speed."
        )
    elif "opportunit" in question_lower or "neue klasse" in question_lower:
        briefing_lines.append(
            "- These opportunities matter because BMW can use Neue Klasse, range, charging, and premium positioning to strengthen its EV competitiveness."
        )
    elif "battery" in question_lower or "charging" in question_lower:
        briefing_lines.append(
            "- Battery and charging matter because they directly influence customer confidence, EV usability, and competitive differentiation."
        )
    elif "tesla" in question_lower or "byd" in question_lower or "competition" in question_lower:
        briefing_lines.append(
            "- Competitor pressure matters because Tesla, BYD, and other EV players can challenge BMW on price, technology, speed, and market perception."
        )
    else:
        briefing_lines.append(
            "- These signals matter because BMW must balance EV growth, premium brand positioning, competitive pressure, and financial discipline."
        )

    briefing_lines.append("")

    briefing_lines.append("### 3. What should BMW management do next?")

    if actions:
        for index, action in enumerate(actions[:4], start=1):
            briefing_lines.append(f"{index}. {action}")
    else:
        briefing_lines.append(
            "1. Prioritize the strongest EV opportunity while monitoring the highest strategic risk."
        )

    briefing_lines.append("")

    briefing_lines.append("### 4. Supporting evidence")

    if evidence_items:
        for index, item in enumerate(evidence_items[:3], start=1):
            title = item.get("title", "Unknown title")
            source = item.get("source", "Unknown source")
            url = get_evidence_url(item)
            chunk_text = get_evidence_chunk(item)

            if url:
                briefing_lines.append(
                    f"**Evidence {index}: [{title}]({url})**  "
                )
            else:
                briefing_lines.append(
                    f"**Evidence {index}: {title}**"
                )

            briefing_lines.append(f"- Source: {source}")

            if chunk_text:
                briefing_lines.append(f"- Relevant retrieved chunk: {chunk_text}")
            else:
                briefing_lines.append("- Relevant retrieved chunk: Not available in this evidence item.")

            briefing_lines.append("")
    else:
        briefing_lines.append("- No supporting evidence available.")

    briefing_lines.append("### 5. Confidence")
    briefing_lines.append(f"- {confidence}")

    return "\n".join(briefing_lines)    

