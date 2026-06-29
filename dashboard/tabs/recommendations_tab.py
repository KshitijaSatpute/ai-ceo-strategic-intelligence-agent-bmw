import pandas as pd
import streamlit as st

from agent.ai_ceo_agent import StrategicAgent


def build_actions_table(result):
    rows = []

    for index, action in enumerate(result.get("actions", []), start=1):
        rows.append({
            "Action Number": index,
            "Recommended Action": action,
            "Priority": result.get("priority", "Unknown"),
            "Confidence": result.get("confidence", "Unknown")
        })

    return pd.DataFrame(rows)


def build_risk_table(result):
    rows = []

    for risk in result.get("risks", []):
        rows.append({
            "Risk Title": risk.get("title", "Risk signal"),
            "Category": risk.get("category", "Strategic Risk"),
            "Severity": risk.get("severity", "Medium"),
            "Evidence ID": risk.get("evidence_id", ""),
            "Reason": risk.get("reason", "")
        })

    return pd.DataFrame(rows)


def build_opportunity_table(result):
    rows = []

    for opportunity in result.get("opportunities", []):
        rows.append({
            "Opportunity Title": opportunity.get("title", "Opportunity signal"),
            "Impact": opportunity.get("impact", "Medium"),
            "Evidence ID": opportunity.get("evidence_id", ""),
            "Reason": opportunity.get("reason", "")
        })

    return pd.DataFrame(rows)


def build_trend_table(result):
    rows = []

    for trend in result.get("trends", []):
        rows.append({
            "Trend Title": trend.get("title", "Trend signal"),
            "Type": trend.get("type", "Trend"),
            "Evidence ID": trend.get("evidence_id", ""),
            "Reason": trend.get("reason", "")
        })

    return pd.DataFrame(rows)


def build_competitor_table(result):
    rows = []

    for competitor in result.get("competitors", []):
        rows.append({
            "Competitive Signal": competitor.get("title", "Competitive signal"),
            "Category": competitor.get("category", "Competitive Signal"),
            "Evidence ID": competitor.get("evidence_id", ""),
            "Reason": competitor.get("reason", "")
        })

    return pd.DataFrame(rows)


def build_evidence_table(result):
    rows = []

    for item in result.get("evidence", []):
        text = item.get("text", "")
        preview = text[:250] + "..." if len(text) > 250 else text

        rows.append({
            "Evidence ID": item.get("evidence_id", ""),
            "Rank": item.get("rank", ""),
            "Source": item.get("source", "Unknown"),
            "Category": item.get("category", "Unknown"),
            "Title": item.get("title", "Untitled"),
            "Text Preview": preview,
            "URL": item.get("url", "")
        })

    return pd.DataFrame(rows)


def show_dataframe_or_message(df, message):
    if df.empty:
        st.info(message)
    else:
        st.dataframe(df, use_container_width=True)


def render_recommendations_tab():
    st.subheader("Strategic Recommendations")

    st.write(
        "This section generates evidence-based strategic recommendations from a dynamic CEO goal. "
        "The agent detects the goal type, selects tools, retrieves evidence, analyzes the evidence, "
        "generates recommendations, validates them, and stores the run in memory."
    )

    user_goal = st.text_area(
        "Enter a strategic CEO goal",
        placeholder="Example: What should BMW prioritize to strengthen its EV strategy?",
        key="recommendation_user_goal",
        height=100
    )

    run_button = st.button(
        "Generate Strategic Recommendation",
        key="generate_strategic_recommendation_button"
    )

    if run_button:
        if not user_goal.strip():
            st.warning("Please enter a strategic CEO goal first.")
            return

        with st.spinner("AI CEO Agent is generating an evidence-based strategic recommendation..."):
            agent = StrategicAgent(top_k=5, use_llm=False)
            result = agent.run(user_goal.strip())
            st.session_state["strategic_recommendation_result"] = result
            st.session_state["latest_agent_result"] = result
            st.session_state["latest_agent_result_source"] = "Strategic Recommendations"

    if "strategic_recommendation_result" not in st.session_state:
        st.info("Enter a dynamic strategic goal to generate recommendations.")
        return

    result = st.session_state["strategic_recommendation_result"]
    trace = result.get("agent_trace", {})
    validation = result.get("validation", {})

    st.divider()

    st.subheader("Strategic Goal")
    st.info(result.get("user_goal", ""))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Detected Goal Type", result.get("goal_type", "Unknown"))

    with col2:
        st.metric("Priority", result.get("priority", "Unknown"))

    with col3:
        st.metric("Confidence", result.get("confidence", "Unknown"))

    with col4:
        st.metric("Evidence Chunks", len(result.get("evidence", [])))

    st.subheader("Selected Tools")

    selected_tools = trace.get("selected_tools", result.get("tools_used", []))
    if selected_tools:
        st.dataframe(pd.DataFrame({"Selected Tools": selected_tools}), use_container_width=True)
    else:
        st.info("No selected tools available.")

    st.subheader("Final Recommendation")

    answer = result.get("answer") or result.get("final_briefing", "")
    if answer:
        st.write(answer)
    else:
        st.warning("No recommendation generated.")

    st.subheader("Recommended Actions")
    show_dataframe_or_message(
        build_actions_table(result),
        "No recommended actions available."
    )

    st.subheader("Risk Assessment")
    show_dataframe_or_message(
        build_risk_table(result),
        "No risk signals selected for this goal type."
    )

    st.subheader("Opportunity Assessment")
    show_dataframe_or_message(
        build_opportunity_table(result),
        "No opportunity signals selected for this goal type."
    )

    st.subheader("Trend Assessment")
    show_dataframe_or_message(
        build_trend_table(result),
        "No trend signals selected for this goal type."
    )

    st.subheader("Competitive Signals")
    show_dataframe_or_message(
        build_competitor_table(result),
        "No competitor signals selected for this goal type."
    )

    st.subheader("Validation Result")

    if validation.get("status") == "passed":
        st.success("Validation passed. Recommendation approved.")
    else:
        st.error("Validation failed or needs review.")

    if validation.get("issues"):
        for issue in validation["issues"]:
            st.write(f"- {issue}")

    st.subheader("Supporting Evidence")
    show_dataframe_or_message(
        build_evidence_table(result),
        "No supporting evidence available."
    )

    memory = result.get("memory", {})
    if memory.get("memory_saved"):
        st.success(memory.get("message", "Agent run saved in memory."))