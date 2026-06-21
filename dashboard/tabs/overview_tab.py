import streamlit as st
import pandas as pd

from storage.sqlite_store import (
    get_source_type_summary,
    get_category_summary
)

from utils.config import COMPANY, INDUSTRY
from dashboard.common import safe_dataframe


def render_overview_tab(stats, source_type_count):
    st.subheader("Company Overview")

    st.write("This section displays the company-level overview required for the executive dashboard.")

    overview_data = {
        "Field": [
            "Company Name",
            "Industry",
            "Number of Collected Documents",
            "Number of Data Sources"
        ],
        "Value": [
            COMPANY,
            INDUSTRY,
            stats["total_documents"],
            stats["unique_publishers"]
        ]
    }

    safe_dataframe(pd.DataFrame(overview_data))

    st.subheader("Source Type Summary")

    source_type_summary = get_source_type_summary()

    if source_type_summary:
        safe_dataframe(pd.DataFrame(source_type_summary))
    else:
        st.warning("No source type data available yet.")

    st.subheader("Category Summary")

    category_summary = get_category_summary()

    if category_summary:
        safe_dataframe(pd.DataFrame(category_summary))
    else:
        st.warning("No category data available yet.")