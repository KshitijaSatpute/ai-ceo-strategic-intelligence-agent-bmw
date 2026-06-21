import streamlit as st
import pandas as pd

from storage.sqlite_store import get_recent_documents
from dashboard.common import safe_dataframe


def render_market_tab():
    st.subheader("Market Intelligence")

    st.write(
        "This section displays recent news, competitor activities, emerging technologies, "
        "and important BMW announcements."
    )

    recent_docs = get_recent_documents(limit=40)

    if recent_docs:
        df = pd.DataFrame(recent_docs)

        display_columns = [
            "title",
            "source",
            "source_type",
            "company",
            "category",
            "word_count",
            "url"
        ]

        available_columns = [
            column for column in display_columns
            if column in df.columns
        ]

        st.subheader("Recent News")
        safe_dataframe(df[available_columns].head(15))

        st.subheader("Competitor Activities")

        if "category" in df.columns:
            competitor_df = df[df["category"] == "Competitor Intelligence"]

            if not competitor_df.empty:
                safe_dataframe(competitor_df[available_columns])
            else:
                st.info("No recent competitor activity documents found in the latest sample.")
        else:
            st.warning("Category column not available.")

        st.subheader("Emerging Technologies")

        if "category" in df.columns:
            technology_df = df[
                df["category"].isin([
                    "Battery and Charging",
                    "EV Market Intelligence"
                ])
            ]

            if not technology_df.empty:
                safe_dataframe(technology_df[available_columns])
            else:
                st.info("No recent emerging technology documents found in the latest sample.")
        else:
            st.warning("Category column not available.")

        st.subheader("Important Company Announcements")

        if "category" in df.columns:
            company_df = df[df["category"] == "BMW EV Strategy"]

            if not company_df.empty:
                safe_dataframe(company_df[available_columns])
            else:
                st.info("No recent BMW announcement documents found in the latest sample.")
        else:
            st.warning("Category column not available.")

    else:
        st.warning("No market intelligence documents available yet.")