import pandas as pd
import streamlit as st

from dashboard.tabs.signal_classifier import (
    assign_relative_levels,
    generate_signal_classification
)


def render_risk_tab():
    st.subheader("Risk Monitor")

    st.write(
        "This is a supporting analytics view built from the full document repository. "
        "Each document is classified only once as Risk, Opportunity, or Neutral. "
        "This tab shows only documents whose stronger signal is Risk."
    )

    with st.spinner("Classifying full repository into exclusive strategic signals..."):
        classified_df, total_documents = generate_signal_classification()

    if total_documents == 0:
        st.warning("No documents were found in the current repository.")
        return

    risk_df = classified_df[classified_df["Signal Type"] == "Risk"].copy()
    opportunity_count = int((classified_df["Signal Type"] == "Opportunity").sum())
    neutral_count = int((classified_df["Signal Type"] == "Neutral").sum())

    if risk_df.empty:
        st.warning("No risk-dominant documents were found in the current repository.")
        return

    risk_df = assign_relative_levels(risk_df, label_column="Severity")

    risk_documents = len(risk_df)

    high_count = int((risk_df["Severity"] == "High").sum())
    medium_count = int((risk_df["Severity"] == "Medium").sum())
    low_count = int((risk_df["Severity"] == "Low").sum())

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Documents", total_documents)

    with col2:
        st.metric("Risk Documents", risk_documents)

    with col3:
        st.metric("Opportunity Docs", opportunity_count)

    with col4:
        st.metric("Neutral Docs", neutral_count)

    with col5:
        st.metric("Check Total", risk_documents + opportunity_count + neutral_count)

    st.caption(
        f"Risk severity check: High + Medium + Low = {high_count + medium_count + low_count}. "
        f"Risk + Opportunity + Neutral = {risk_documents + opportunity_count + neutral_count}. "
        f"Total Documents = {total_documents}."
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("High Severity", high_count)

    with col_b:
        st.metric("Medium Severity", medium_count)

    with col_c:
        st.metric("Low Severity", low_count)

    theme_summary = (
        risk_df
        .groupby("Final Theme")
        .agg(
            Documents=("Final Theme", "count"),
            Sources=("Source", "nunique"),
            Average_Evidence_Strength=("Evidence Strength Score", "mean")
        )
        .reset_index()
    )

    theme_summary["Average_Evidence_Strength"] = theme_summary["Average_Evidence_Strength"].round(2)
    theme_summary = theme_summary.sort_values(by="Documents", ascending=False)

    source_summary = (
        risk_df
        .groupby("Source")
        .size()
        .reset_index(name="Risk Documents")
        .sort_values(by="Risk Documents", ascending=False)
    )

    st.subheader("Top Risk Themes")
    st.dataframe(theme_summary, use_container_width=True)

    st.subheader("Source Distribution")
    st.dataframe(source_summary, use_container_width=True)

    st.subheader("Risk-Dominant Documents")

    risk_df = risk_df.rename(columns={"Final Theme": "Risk Theme"})

    display_columns = [
        "Document ID",
        "Risk Theme",
        "Severity",
        "Evidence Strength Score",
        "Risk Score",
        "Opportunity Score",
        "Title",
        "Source",
        "Source Type",
        "Category",
        "Date",
        "Matched Keywords",
        "Why Classified",
        "Evidence Preview",
        "URL"
    ]

    st.dataframe(
        risk_df[display_columns],
        use_container_width=True
    )

    st.caption(
        "Explanation: This tab uses exclusive keyword-based classification. "
        "A document appears here only if its risk score is stronger than its opportunity score. "
        "The main agentic reasoning still happens in the CEO Agent workflow."
    )