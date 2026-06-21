import streamlit as st

from dashboard.common import (
    load_ai_ceo_agent,
    get_unique_evidence_items,
    build_ceo_briefing_summary
)


def render_ceo_briefing_tab():
    st.subheader("CEO Briefing")

    st.write(
        "This section gives a concise CEO-level executive summary. "
        "Detailed recommendation tables are available in the Strategic Recommendations tab."
    )

    default_questions = [
        "What should BMW do next in EV strategy?",
        "What are BMW's biggest risks in the electric vehicle market?",
        "What opportunities does BMW have from Neue Klasse?",
        "How should BMW respond to Tesla and BYD competition?",
        "What battery and charging trends should BMW focus on?"
    ]

    selected_question = st.selectbox(
        "Choose a sample CEO question",
        default_questions,
        key="ceo_question_select"
    )

    custom_question = st.text_input(
        "Or type your own question",
        placeholder="Example: What should BMW prioritize in EV strategy?",
        key="ceo_custom_question"
    )

    if custom_question.strip():
        final_question = custom_question.strip()
    else:
        final_question = selected_question

    generate_button = st.button(
        "Generate CEO Briefing",
        key="generate_ceo_recommendation"
    )

    if generate_button:
        with st.spinner("Generating CEO briefing using RAG + safe AI CEO agent..."):
            agent = load_ai_ceo_agent()
            result = agent.ask(final_question)
            st.session_state["ceo_result"] = result

    if "ceo_result" in st.session_state:
        result = st.session_state["ceo_result"]

        st.subheader("CEO Question")
        st.info(result["question"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Priority", result["priority"])

        with col2:
            st.metric("Confidence", result["confidence"])

        with col3:
            st.metric("Unique Evidence Sources", len(get_unique_evidence_items(result)))

        st.caption(f"Generation mode: {result['generation_mode']}")

        st.subheader("Executive Summary")
        st.markdown(build_ceo_briefing_summary(result))

        st.info(
            "Detailed risks, opportunities, recommendation tables, and full evidence "
            "are shown in the Strategic Recommendations tab to avoid repetition."
        )