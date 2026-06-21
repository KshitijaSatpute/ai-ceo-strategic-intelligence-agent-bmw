import streamlit as st

from dashboard.common import (
    load_ai_ceo_agent,
    get_unique_evidence_items,
    build_recommendation_table,
    build_risk_monitor_table,
    build_opportunity_monitor_table,
    display_evidence,
    safe_dataframe
)


def render_recommendations_tab():
    st.subheader("Strategic Recommendations")

    st.write(
        "For each recommendation, this section displays recommendation, priority, "
        "supporting evidence, expected impact, risk level, and detailed risk assessment."
    )

    recommendation_questions = [
        "What should BMW do next in EV strategy?",
        "What are BMW's biggest risks in the electric vehicle market?",
        "What opportunities does BMW have from Neue Klasse?",
        "How should BMW respond to Tesla and BYD competition?",
        "What battery and charging trends should BMW focus on?"
    ]

    selected_recommendation_question = st.selectbox(
        "Select a strategic recommendation question",
        recommendation_questions,
        key="recommendation_question_select"
    )

    custom_recommendation_question = st.text_input(
        "Or enter your own strategic question",
        placeholder="Example: What should BMW prioritize in EV strategy?",
        key="recommendation_custom_question"
    )

    if custom_recommendation_question.strip():
        final_recommendation_question = custom_recommendation_question.strip()
    else:
        final_recommendation_question = selected_recommendation_question

    generate_recommendation_button = st.button(
        "Generate Strategic Recommendation",
        key="generate_recommendation_button"
    )

    if generate_recommendation_button:
        with st.spinner("Generating strategic recommendation using RAG and AI CEO agent..."):
            agent = load_ai_ceo_agent()
            result = agent.ask(final_recommendation_question)
            st.session_state["strategic_recommendation_result"] = result

    if "strategic_recommendation_result" in st.session_state:
        result = st.session_state["strategic_recommendation_result"]

        st.subheader("Strategic Question")
        st.info(result["question"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Priority", result["priority"])

        with col2:
            st.metric("Confidence", result["confidence"])

        with col3:
            st.metric("Evidence Items", len(get_unique_evidence_items(result)))

        st.caption(f"Generation mode: {result['generation_mode']}")

        st.subheader("Evidence-Based Recommendation Table")

        recommendation_df = build_recommendation_table(result)
        safe_dataframe(recommendation_df)

        st.subheader("Risk Assessment")
        risk_df = build_risk_monitor_table(result)
        safe_dataframe(risk_df)

        st.subheader("Expected Impact / Opportunities")
        opportunity_df = build_opportunity_monitor_table(result)
        safe_dataframe(opportunity_df)

        st.subheader("Strategic Trends")
        for trend in result.get("trends", []):
            st.write(f"- {trend}")

        st.subheader("Supporting Evidence")
        display_evidence(result)

    else:
        st.info("Generate a recommendation to display priority, evidence, impact, and risk level.")