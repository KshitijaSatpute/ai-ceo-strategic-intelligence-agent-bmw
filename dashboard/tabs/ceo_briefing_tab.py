import pandas as pd
import streamlit as st

from agent.ai_ceo_agent import StrategicAgent


def build_evidence_table(result):
    rows = []

    for item in result.get("evidence", []):
        rows.append({
            "Evidence ID": item.get("evidence_id", ""),
            "Rank": item.get("rank", ""),
            "Source": item.get("source", "Unknown"),
            "Category": item.get("category", "Unknown"),
            "Title": item.get("title", "Untitled"),
            "URL": item.get("url", "")
        })

    return pd.DataFrame(rows)


def render_ceo_briefing_tab():
    st.subheader("CEO Briefing")

    st.write(
        "This section generates a CEO-level executive briefing from a dynamic user goal. "
        "The AI CEO Agent plans, selects tools, retrieves evidence, analyzes it, recommends actions, "
        "validates the result, saves memory, and returns a trace."
    )

    user_goal = st.text_area(
        "Enter a CEO-level strategic goal",
        placeholder="Example: What should BMW do next in EV strategy?",
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

        with st.spinner("AI CEO Agent is generating an evidence-based briefing..."):
            agent = StrategicAgent(top_k=5, use_llm=False)
            result = agent.run(user_goal.strip())
            st.session_state["ceo_briefing_result"] = result
            st.session_state["latest_agent_result"] = result
            st.session_state["latest_agent_result_source"] = "CEO Briefing"

    if "ceo_briefing_result" not in st.session_state:
        st.info("Enter a CEO-level goal to generate the briefing.")
        return

    result = st.session_state["ceo_briefing_result"]
    trace = result.get("agent_trace", {})
    validation = result.get("validation", {})

    st.divider()

    st.subheader("CEO Goal")
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

    st.subheader("Executive Briefing")

    answer = result.get("answer") or result.get("final_briefing", "")
    if answer:
        st.write(answer)
    else:
        st.warning("No CEO briefing generated.")

    st.subheader("Agent Plan")

    plan_steps = trace.get("plan_steps", [])
    if plan_steps:
        for step in plan_steps:
            st.write(f"- {step}")
    else:
        st.info("No plan available.")

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

    memory = result.get("memory", {})
    if memory.get("memory_saved"):
        st.success(memory.get("message", "Agent run saved in memory."))