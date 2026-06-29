import pandas as pd
import streamlit as st


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
            "Similarity": item.get("similarity", ""),
            "Text Preview": preview,
            "URL": item.get("url", "")
        })

    return pd.DataFrame(rows)


def render_validation(validation):
    status = validation.get("status", "unknown")

    if status == "passed":
        st.success("Validation passed. Recommendation approved.")
    else:
        st.error("Validation failed or needs review.")

    if validation.get("checks"):
        st.write("**Passed checks:**")
        for check in validation["checks"]:
            st.write(f"- {check}")

    if validation.get("issues"):
        st.write("**Validation issues:**")
        for issue in validation["issues"]:
            st.write(f"- {issue}")

    if validation.get("decision"):
        st.info(validation["decision"])


def render_agent_trace_tab():
    st.subheader("AI CEO Agent Trace")

    st.write(
        "This tab does not ask for a separate query. It displays the latest agent run from "
        "CEO Briefing or Strategic Recommendations. This keeps user questions only in those two tabs "
        "and uses this tab as a transparent trace viewer."
    )

    result = st.session_state.get("latest_agent_result")

    if not result:
        st.info(
            "No agent run available yet. Generate a CEO Briefing or Strategic Recommendation first, "
            "then return here to view the full agent trace."
        )
        return

    trace = result.get("agent_trace", {})

    st.divider()

    st.subheader("1. User Goal")
    st.info(trace.get("goal", result.get("user_goal", "")))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Detected Goal Type", trace.get("goal_type", result.get("goal_type", "Unknown")))

    with col2:
        st.metric("Priority", result.get("priority", "Unknown"))

    with col3:
        st.metric("Confidence", result.get("confidence", "Unknown"))

    with col4:
        sentiment = result.get("sentiment", {})
        st.metric("Evidence Sentiment", sentiment.get("label", "Unknown"))

    st.subheader("2. Agent Plan")

    plan_steps = trace.get("plan_steps", [])
    if plan_steps:
        for step in plan_steps:
            st.write(f"- {step}")
    else:
        st.info("No plan steps available.")

    st.subheader("3. Selected Tools")

    selected_tools = trace.get("selected_tools", result.get("tools_used", []))
    if selected_tools:
        st.dataframe(
            pd.DataFrame({"Selected Tools": selected_tools}),
            use_container_width=True
        )
    else:
        st.info("No selected tools available.")

    st.subheader("4. Execution Trace")

    execution_trace = trace.get("execution_trace", [])
    if execution_trace:
        for step in execution_trace:
            st.write(f"- {step}")
    else:
        st.info("No execution trace available.")

    st.subheader("5. Agent Decisions")

    decisions = trace.get("agent_decisions", [])
    if decisions:
        for decision in decisions:
            st.write(f"- {decision}")
    else:
        st.info("No agent decisions available.")

    st.subheader("6. Validation Result")

    validation = trace.get("validation_result", result.get("validation", {}))
    render_validation(validation)

    st.subheader("7. Memory Status")

    memory = trace.get("memory_updated", result.get("memory", {}))
    if memory.get("memory_saved"):
        st.success(memory.get("message", "Agent run saved in memory."))
        st.caption(f"Timestamp: {memory.get('timestamp', '')}")
    else:
        st.warning("Memory update status not available.")

    st.subheader("8. Final CEO Recommendation")

    answer = result.get("answer") or result.get("final_briefing", "")
    if answer:
        st.write(answer)
    else:
        st.warning("No final recommendation available.")

    st.subheader("9. Supporting Evidence")

    evidence_df = build_evidence_table(result)

    if evidence_df.empty:
        st.info("No supporting evidence available.")
    else:
        st.dataframe(evidence_df, use_container_width=True)