import pandas as pd
import streamlit as st

from dashboard.tabs.signal_classifier import (
    assign_relative_levels,
    generate_signal_classification
)


def render_opportunity_tab():
    st.subheader("Opportunity Monitor")

    st.write(
        "This is a supporting analytics view built from the full document repository. "
        "Each document is classified only once as Risk, Opportunity, or Neutral. "
        "This tab shows only documents whose stronger signal is Opportunity."
    )

    with st.spinner("Classifying full repository into exclusive strategic signals..."):
        classified_df, total_documents = generate_signal_classification()

    if total_documents == 0:
        st.warning("No documents were found in the current repository.")
        return

    opportunity_df = classified_df[classified_df["Signal Type"] == "Opportunity"].copy()
    risk_count = int((classified_df["Signal Type"] == "Risk").sum())
    neutral_count = int((classified_df["Signal Type"] == "Neutral").sum())

    if opportunity_df.empty:
        st.warning("No opportunity-dominant documents were found in the current repository.")
        return

    opportunity_df = assign_relative_levels(opportunity_df, label_column="Impact")

    opportunity_documents = len(opportunity_df)

    high_count = int((opportunity_df["Impact"] == "High").sum())
    medium_count = int((opportunity_df["Impact"] == "Medium").sum())
    low_count = int((opportunity_df["Impact"] == "Low").sum())

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Documents", total_documents)

    with col2:
        st.metric("Opportunity Docs", opportunity_documents)

    with col3:
        st.metric("Risk Docs", risk_count)

    with col4:
        st.metric("Neutral Docs", neutral_count)

    with col5:
        st.metric("Check Total", opportunity_documents + risk_count + neutral_count)

    st.caption(
        f"Opportunity impact check: High + Medium + Low = {high_count + medium_count + low_count}. "
        f"Risk + Opportunity + Neutral = {risk_count + opportunity_documents + neutral_count}. "
        f"Total Documents = {total_documents}."
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("High Impact", high_count)

    with col_b:
        st.metric("Medium Impact", medium_count)

    with col_c:
        st.metric("Low Impact", low_count)

    theme_summary = (
        opportunity_df
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
        opportunity_df
        .groupby("Source")
        .size()
        .reset_index(name="Opportunity Documents")
        .sort_values(by="Opportunity Documents", ascending=False)
    )

    st.subheader("Top Opportunity Themes")
    st.dataframe(theme_summary, use_container_width=True)

    st.subheader("Source Distribution")
    st.dataframe(source_summary, use_container_width=True)

    st.subheader("Opportunity-Dominant Documents")

    opportunity_df = opportunity_df.rename(columns={"Final Theme": "Opportunity Theme"})

    display_columns = [
        "Document ID",
        "Opportunity Theme",
        "Impact",
        "Evidence Strength Score",
        "Opportunity Score",
        "Risk Score",
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
        opportunity_df[display_columns],
        use_container_width=True
    )

    st.caption(
        "Explanation: This tab uses exclusive keyword-based classification. "
        "A document appears here only if its opportunity score is stronger than its risk score. "
        "The main agentic reasoning still happens in the CEO Agent workflow."
    )