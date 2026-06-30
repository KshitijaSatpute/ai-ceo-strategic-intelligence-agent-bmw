import pandas as pd
import streamlit as st

from agent.ai_ceo_agent import StrategicAgent


DEFAULT_CEO_QUERY = (
    "What should BMW do next in its EV strategy considering competition, "
    "market demand, innovation, and strategic risks?"
)


def build_evidence_table(result):
    rows = []

    for item in result.get("evidence", []):
        text = item.get("text", "")
        preview = text[:250] + "..." if len(text) > 250 else text

        rows.append({
            "Evidence ID": item.get("evidence_id", ""),
            "Rank": item.get("rank", ""),
            "Similarity": item.get("similarity", ""),
            "Source": item.get("source", "Unknown"),
            "Category": item.get("category", "Unknown"),
            "Title": item.get("title", "Untitled"),
            "Text Preview": preview,
            "URL": item.get("url", "")
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
            "Matched Keywords": risk.get("matched_keywords", ""),
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
            "Matched Keywords": opportunity.get("matched_keywords", ""),
            "Reason": opportunity.get("reason", "")
        })

    return pd.DataFrame(rows)


def show_dataframe_or_message(df, message):
    if df.empty:
        st.info(message)
    else:
        st.dataframe(df, use_container_width=True)


def render_ceo_briefing_tab():
    st.subheader("CEO Briefing")

    st.write(
        "This section generates a CEO-level executive briefing from a dynamic user goal. "
        "The AI CEO Agent plans, selects tools, retrieves evidence, analyzes it, sends the evidence "
        "to the local LLM for final briefing generation, validates the result, saves memory, "
        "and returns a trace."
    )

    if "ceo_briefing_user_goal" not in st.session_state:
        st.session_state["ceo_briefing_user_goal"] = DEFAULT_CEO_QUERY

    user_goal = st.text_area(
        "Enter a CEO-level strategic goal",
        key="ceo_briefing_user_goal",
        height=100
    )

    run_button = st.button(
        "Generate CEO Briefing",
        key="generate_ceo_briefing_button"
    )

    if run_button:
        if not user_goal.strip():
            st.warning("Please enter a CEO-level strategic goal first.")
            return

        with st.spinner("AI CEO Agent is retrieving evidence and generating a CEO briefing..."):
            agent = StrategicAgent(top_k=5, use_llm=True)
            result = agent.run(user_goal.strip())

            st.session_state["ceo_briefing_result"] = result
            st.session_state["latest_agent_result"] = result
            st.session_state["latest_agent_result_source"] = "CEO Briefing"

    if "ceo_briefing_result" not in st.session_state:
        st.info("A default CEO-level goal is already provided. You can run it or edit it first.")
        return

    result = st.session_state["ceo_briefing_result"]
    trace = result.get("agent_trace", {})
    validation = result.get("validation", {})
    memory = result.get("memory", {})

    st.divider()

    st.subheader("CEO Goal")
    st.info(result.get("user_goal", ""))

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Detected Goal Type", result.get("goal_type", "Unknown"))

    with col2:
        st.metric("Priority", result.get("priority", "Unknown"))

    with col3:
        st.metric("Confidence", result.get("confidence", "Unknown"))

    with col4:
        st.metric("Evidence Chunks", len(result.get("evidence", [])))

    with col5:
        st.metric("Generation Mode", result.get("generation_mode", "Unknown"))

    st.subheader("Executive Briefing")

    answer = result.get("answer") or result.get("final_briefing", "")

    if answer:
        st.markdown(answer)
    else:
        st.warning("No CEO briefing generated.")

    st.subheader("Risk Signals Used")
    show_dataframe_or_message(
        build_risk_table(result),
        "No risk signals selected for this CEO goal."
    )

    st.subheader("Opportunity Signals Used")
    show_dataframe_or_message(
        build_opportunity_table(result),
        "No opportunity signals selected for this CEO goal."
    )

    st.subheader("Agent Plan")

    plan_steps = trace.get("plan_steps", [])

    if plan_steps:
        for step in plan_steps:
            st.write(f"- {step}")
    else:
        st.info("No plan available.")

    st.subheader("Selected Tools")

    selected_tools = trace.get("selected_tools", result.get("tools_used", []))

    if selected_tools:
        st.dataframe(
            pd.DataFrame({"Selected Tools": selected_tools}),
            use_container_width=True
        )
    else:
        st.info("No selected tools available.")

    st.subheader("Validation Result")

    if validation.get("status") == "passed":
        st.success("Validation passed. Briefing approved.")
    else:
        st.error("Validation failed or needs review.")

    if validation.get("issues"):
        for issue in validation["issues"]:
            st.write(f"- {issue}")

    st.subheader("Supporting Evidence")

    evidence_df = build_evidence_table(result)

    if evidence_df.empty:
        st.info("No evidence available.")
    else:
        st.dataframe(evidence_df, use_container_width=True)

    if memory.get("memory_saved"):
        st.success(memory.get("message", "Agent run saved in memory."))
    else:
        st.info("Memory status not available.")