import streamlit as st

from dashboard.common import (
    load_ai_ceo_agent,
    build_risk_monitor_table,
    safe_dataframe,
    display_evidence,
    get_unique_evidence_items
)


def render_risk_tab():
    st.subheader("Risk Monitor")

    st.write(
        "This section identifies BMW's strategic risks using retrieved evidence from the knowledge base."
    )

    risk_questions = [
        "What are BMW's biggest risks in the electric vehicle market?",
        "What risks does BMW face from Tesla and BYD competition?",
        "What financial risks does BMW face in its EV strategy?",
        "What risks does BMW face from China sales and profit pressure?",
        "What operational risks are linked to battery, charging, and EV rollout?",
        "What strategic risks does BMW face during the transition from combustion cars to EVs?"
    ]

    selected_risk_question = st.selectbox(
        "Choose a sample risk query",
        risk_questions,
        key="risk_question_select"
    )

    custom_risk_question = st.text_input(
        "Or type your own risk question",
        placeholder="Example: What is the biggest strategic risk for BMW in EVs?",
        key="risk_custom_question"
    )

    if custom_risk_question.strip():
        final_risk_question = custom_risk_question.strip()
    else:
        final_risk_question = selected_risk_question

    generate_risk_button = st.button(
        "Generate Risk Monitor",
        key="generate_risk_monitor"
    )

    if generate_risk_button:
        with st.spinner("Detecting BMW strategic risks from retrieved evidence..."):
            agent = load_ai_ceo_agent()
            result = agent.ask(final_risk_question)
            st.session_state["risk_monitor_result"] = result

    if "risk_monitor_result" in st.session_state:
        result = st.session_state["risk_monitor_result"]

        st.subheader("Risk Query")
        st.info(result["question"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Priority", result.get("priority", "Medium"))

        with col2:
            st.metric("Confidence", result.get("confidence", "Medium"))

        with col3:
            st.metric("Evidence Sources", len(get_unique_evidence_items(result)))

        risk_df = build_risk_monitor_table(result)

        st.subheader("Risk Table")

        if not risk_df.empty:
            safe_dataframe(risk_df)
        else:
            st.warning("No risks were detected for this query.")

        st.subheader("Risk Severity Distribution")

        if not risk_df.empty and "Severity Level" in risk_df.columns:
            risk_severity_chart = (
                risk_df["Severity Level"]
                .value_counts()
                .reset_index()
            )

            risk_severity_chart.columns = ["Severity Level", "Count"]

            st.bar_chart(
                risk_severity_chart,
                x="Severity Level",
                y="Count",
                width="stretch",
                height=320
            )
        else:
            st.info("Severity Level column not available for risk chart.")

        st.subheader("Supporting Evidence")
        display_evidence(result)

    else:
        st.info("Choose a sample risk query or type your own question, then click Generate Risk Monitor.")