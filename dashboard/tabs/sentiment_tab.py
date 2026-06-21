import streamlit as st

from dashboard.common import (
    load_sentiment_results,
    safe_dataframe
)


def render_sentiment_tab():
    st.subheader("Sentiment Analysis")

    st.write(
        "This section displays news sentiment, public article sentiment, sentiment trends, and visualizations."
    )

    if st.button("Run Sentiment Analysis", key="run_sentiment_analysis"):
        with st.spinner("Analyzing document sentiment..."):
            sentiment_summary = load_sentiment_results()
            st.session_state["sentiment_summary"] = sentiment_summary

    if "sentiment_summary" in st.session_state:
        sentiment_summary = st.session_state["sentiment_summary"]

        documents_df = sentiment_summary["documents"]
        overall_summary = sentiment_summary["overall_summary"]
        source_summary = sentiment_summary["source_summary"]
        category_summary = sentiment_summary["category_summary"]

        st.subheader("News / Public Sentiment Summary")
        safe_dataframe(overall_summary)

        st.subheader("Sentiment by Source")
        safe_dataframe(source_summary)

        st.subheader("Sentiment by Category")
        safe_dataframe(category_summary)

        st.subheader("Document-Level Sentiment")

        selected_sentiment = st.selectbox(
            "Filter documents by sentiment",
            ["All", "Positive", "Neutral", "Negative"],
            key="sentiment_filter"
        )

        if selected_sentiment != "All":
            filtered_df = documents_df[
                documents_df["sentiment"] == selected_sentiment
            ]
        else:
            filtered_df = documents_df

        sentiment_columns = [
            "title",
            "source",
            "category",
            "compound",
            "positive",
            "neutral",
            "negative",
            "sentiment"
        ]

        safe_dataframe(filtered_df[sentiment_columns])

        st.subheader("Sentiment Trends / Visualizations")

        if not overall_summary.empty:
            st.write("Overall Sentiment Distribution")
            overall_chart_df = overall_summary.set_index("sentiment")
            st.bar_chart(overall_chart_df["count"])

        if not source_summary.empty:
            st.write("Sentiment by Source")
            source_pivot = source_summary.pivot_table(
                index="source",
                columns="sentiment",
                values="count",
                fill_value=0
            )
            st.bar_chart(source_pivot)

        if not category_summary.empty:
            st.write("Sentiment by Category")
            category_pivot = category_summary.pivot_table(
                index="category",
                columns="sentiment",
                values="count",
                fill_value=0
            )
            st.bar_chart(category_pivot)

        st.info(
            "Interpretation note: VADER sentiment is used as a lightweight lexical baseline. "
            "The sentiment score represents article tone, not final strategic risk."
        )

    else:
        st.info("Click 'Run Sentiment Analysis' to display sentiment tables and charts.")