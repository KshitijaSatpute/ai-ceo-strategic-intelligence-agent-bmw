import streamlit as st
import pandas as pd

from agent.ai_ceo_agent import StrategicAgent


def render_agent_trace_tab():
    st.subheader("AI CEO Agent Trace")

    st.write(
        "This tab shows why the system is agentic: the AI CEO Agent creates a plan, "
        "selects tools, executes tools, makes decisions, validates the answer, "
        "saves the run in memory, and returns a CEO-level briefing."
    )

    sample_questions = [
        "What are BMW's biggest risks in the EV market?",
        "What opportunities does BMW have from Neue Klasse?",
        "How should BMW respond to Tesla and BYD competition?",
        "What battery and charging trends should BMW focus on?",
        "What should BMW do next in EV strategy?"
    ]

    selected_question = st.selectbox(
        "Select an agent question",
        sample_questions,
        key="agent_trace_question_select"
    )

    custom_question = st.text_input(
        "Or enter your own CEO question",
        placeholder="Example: What should BMW prioritize in EV strategy?",
        key="agent_trace_custom_question"
    )

    if custom_question.strip():
        final_question = custom_question.strip()
    else:
        final_question = selected_question

    use_llm = st.checkbox(
        "Use local Ollama LLM for final rewriting",
        value=False,
        key="agent_trace_use_llm"
    )

    if st.button("Run AI CEO Agent", key="run_agent_trace_button"):
        with st.spinner("Agent is planning, selecting tools, retrieving evidence, analyzing, validating, and saving memory..."):
            agent = StrategicAgent(top_k=5, use_llm=use_llm)
            result = agent.run(final_question)
            st.session_state["agent_trace_result"] = result

    if "agent_trace_result" not in st.session_state:
        st.info("Run the AI CEO Agent to see the full trace.")
        return

    result = st.session_state["agent_trace_result"]
    trace = result["agent_trace"]

    st.divider()

    st.subheader("1. Goal")
    st.info(trace["goal"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Query Type", trace["query_type"])

    with col2:
        st.metric("Priority", result["priority"])

    with col3:
        st.metric("Confidence", result["confidence"])

    with col4:
        sentiment = result.get("sentiment", {})
        st.metric("Sentiment", sentiment.get("label", "Unknown"))

    st.subheader("2. Agent Plan")
    for step in trace["plan_steps"]:
        st.write(f"- {step}")

    st.subheader("3. Selected Tools")
    st.dataframe(
        pd.DataFrame({"Selected Tools": trace["selected_tools"]}),
        use_container_width=True
    )

    st.subheader("4. Executed Tools")
    st.dataframe(
        pd.DataFrame({"Executed Tools": trace["executed_tools"]}),
        use_container_width=True
    )

    st.subheader("5. Agent Decisions")
    for decision in trace["decisions"]:
        st.write(f"- {decision}")

    st.subheader("6. Validation Result")
    validation = trace["validation"]

    if validation.get("status") == "passed":
        st.success("Validation status: passed")
    else:
        st.error("Validation status: failed or needs review")

    if validation.get("checks"):
        st.write("**Passed checks:**")
        for check in validation["checks"]:
            st.write(f"- {check}")

    if validation.get("warnings"):
        st.warning("Warnings:")
        for warning in validation["warnings"]:
            st.write(f"- {warning}")

    st.subheader("7. Final CEO Briefing")
    st.write(result["final_briefing"])
    st.caption(f"Generation mode: {result['generation_mode']}")

    st.subheader("8. Supporting Evidence")

    evidence_rows = []
    for item in result.get("evidence", []):
        evidence_rows.append({
            "Rank": item.get("rank"),
            "Source": item.get("source"),
            "Category": item.get("category"),
            "Title": item.get("title"),
            "Similarity": item.get("similarity"),
            "URL": item.get("url")
        })

    if evidence_rows:
        st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True)
    else:
        st.info("No evidence available.")