import sqlite3
from pathlib import Path

import streamlit as st

from storage.sqlite_store import (
    create_tables,
    get_document_stats,
    get_source_type_count
)

from utils.config import COMPANY, INDUSTRY

from dashboard.tabs.overview_tab import render_overview_tab
from dashboard.tabs.market_tab import render_market_tab
from dashboard.tabs.opportunity_tab import render_opportunity_tab
from dashboard.tabs.risk_tab import render_risk_tab
from dashboard.tabs.sentiment_tab import render_sentiment_tab
from dashboard.tabs.recommendations_tab import render_recommendations_tab
from dashboard.tabs.ceo_briefing_tab import render_ceo_briefing_tab


def get_total_chunks():
    db_path = Path(__file__).resolve().parent / "data" / "ai_ceo.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
        table_exists = cursor.fetchone()

        if not table_exists:
            conn.close()
            return 0

        cursor.execute("SELECT COUNT(*) FROM chunks")
        total_chunks = cursor.fetchone()[0]

        conn.close()
        return total_chunks

    except Exception:
        return 0


st.set_page_config(
    page_title="AI CEO Strategic Intelligence Agent",
    layout="wide"
)

st.markdown(
    """
    <style>
    button[data-baseweb="tab"] {
        padding: 14px 22px;
        margin-right: 8px;
    }

    button[data-baseweb="tab"] p {
        font-size: 18px;
        font-weight: 700;
    }

    div[data-baseweb="tab-list"] {
        gap: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

create_tables()

stats = get_document_stats()
source_type_count = get_source_type_count()
total_chunks = get_total_chunks()

st.title("AI CEO: Strategic Intelligence Agent")
st.caption("BMW EV Strategy and Competitive Intelligence")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Company", COMPANY)

with col2:
    st.metric("Collected Documents", stats["total_documents"])

with col3:
    st.metric("Data Sources", stats["unique_publishers"])

with col4:
    st.metric("Text Chunks", total_chunks)

with col5:
    st.metric("Industry", INDUSTRY)

st.write(f"Last Update: {stats['last_update']}")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview",
    "🌍 Market Intelligence",
    "🚀 Opportunities",
    "⚠️ Risk Monitor",
    "💬 Sentiment",
    "🎯 Recommendations",
    "👁 CEO Briefing"
])

with tab1:
    render_overview_tab(stats, source_type_count)

with tab2:
    render_market_tab()

with tab3:
    render_opportunity_tab()

with tab4:
    render_risk_tab()

with tab5:
    render_sentiment_tab()

with tab6:
    render_recommendations_tab()

with tab7:
    render_ceo_briefing_tab()