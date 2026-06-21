import streamlit as st

from dashboard.common import (
    load_ai_ceo_agent,
    build_opportunity_monitor_table,
    safe_dataframe,
    display_evidence,
    get_unique_evidence_items
)


def render_opportunity_tab():
    st.subheader("Opportunity Monitor")

    st.write(
        "This section identifies BMW's strategic opportunities using retrieved evidence from the knowledge base."
    )

    opportunity_questions = [
        "What are BMW's strongest EV strategy opportunities across all collected articles?",
        "What opportunities does BMW have from Neue Klasse?",
        "How can BMW use battery and charging improvements as a strategic opportunity?",
        "What opportunity does BMW have in premium performance EVs?",
        "How can BMW respond to Tesla and BYD through strategic opportunities?",
        "What opportunities are visible from BMW i3, iX3, and electric M models?"
    ]

    selected_opportunity_question = st.selectbox(
        "Choose a sample opportunity query",
        opportunity_questions,
        key="opportunity_question_select"
    )

    custom_opportunity_question = st.text_input(
        "Or type your own opportunity question",
        placeholder="Example: What EV opportunity should BMW prioritize next?",
        key="opportunity_custom_question"
    )

    if custom_opportunity_question.strip():
        final_opportunity_question = custom_opportunity_question.strip()
    else:
        final_opportunity_question = selected_opportunity_question

    generate_opportunity_button = st.button(
        "Generate Opportunity Monitor",
        key="generate_opportunity_monitor"
    )

    if generate_opportunity_button:
        with st.spinner("Detecting BMW strategic opportunities from retrieved evidence..."):
            agent = load_ai_ceo_agent()
            result = agent.ask(final_opportunity_question)
            st.session_state["opportunity_monitor_result"] = result

    if "opportunity_monitor_result" in st.session_state:
        result = st.session_state["opportunity_monitor_result"]

        st.subheader("Opportunity Query")
        st.info(result["question"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Priority", result.get("priority", "Medium"))

        with col2:
            st.metric("Confidence", result.get("confidence", "Medium"))

        with col3:
            st.metric("Evidence Sources", len(get_unique_evidence_items(result)))

        opportunity_df = build_opportunity_monitor_table(result)

        st.subheader("Opportunity Table")

        if not opportunity_df.empty:
            safe_dataframe(opportunity_df)
        else:
            st.warning("No opportunities were detected for this query.")

        st.subheader("Opportunity Impact Distribution")

        if not opportunity_df.empty and "Impact Level" in opportunity_df.columns:
            opportunity_impact_chart = (
                opportunity_df["Impact Level"]
                .value_counts()
                .reset_index()
            )

            opportunity_impact_chart.columns = ["Impact Level", "Count"]

            st.bar_chart(
                opportunity_impact_chart,
                x="Impact Level",
                y="Count",
                width="stretch",
                height=320
            )
        else:
            st.info("Impact Level column not available for opportunity chart.")

        st.subheader("Supporting Evidence")
        display_evidence(result)

    else:
        st.info("Choose a sample opportunity query or type your own question, then click Generate Opportunity Monitor.")