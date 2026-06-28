import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ai_ceo.db"


RISK_THEMES = [
    {
        "title": "Premium EV competitive pressure",
        "category": "Competitive Risk",
        "keywords": [
            "tesla", "byd", "rivian", "mercedes", "audi", "volkswagen",
            "hyundai", "kia", "lucid", "competition", "competitor",
            "rival", "model y", "electric suv"
        ]
    },
    {
        "title": "China sales and market pressure",
        "category": "Market Risk",
        "keywords": [
            "china", "chinese market", "sales drop", "slump", "weak demand",
            "profit guidance", "market pressure", "price war", "slowdown"
        ]
    },
    {
        "title": "Profit margin and pricing pressure",
        "category": "Financial Risk",
        "keywords": [
            "profit", "margin", "cost", "pricing", "price cut", "expensive",
            "loss", "layoffs", "earnings", "financial pressure"
        ]
    },
    {
        "title": "ICE transition and regulatory pressure",
        "category": "Regulatory / Transition Risk",
        "keywords": [
            "combustion", "ice", "internal-combustion", "emissions",
            "regulation", "regulatory", "ban", "transition", "hybrid"
        ]
    },
    {
        "title": "Battery, range and charging execution risk",
        "category": "Technology Risk",
        "keywords": [
            "battery", "range", "charging", "fast charging", "800v",
            "kwh", "supply chain", "battery cost", "charging network"
        ]
    }
]


def choose_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def clean_text(text):
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_table_columns(conn, table_name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))

    if cursor.fetchone() is None:
        return []

    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()

    return [row[1] for row in rows]


def load_text_repository():
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    chunk_columns = get_table_columns(conn, "chunks")

    if chunk_columns:
        table_name = "chunks"
        columns = chunk_columns
    else:
        table_name = "documents"
        columns = get_table_columns(conn, "documents")

    if not columns:
        conn.close()
        return pd.DataFrame()

    text_column = choose_column(
        columns,
        ["chunk_text", "text", "content", "clean_text", "article_text", "raw_text", "summary"]
    )
    title_column = choose_column(columns, ["title", "headline", "name"])
    source_column = choose_column(columns, ["source", "publisher", "source_name"])
    category_column = choose_column(columns, ["category", "source_type", "topic"])
    url_column = choose_column(columns, ["url", "link"])

    if text_column is None:
        conn.close()
        return pd.DataFrame()

    selected_columns = [text_column]

    for column in [title_column, source_column, category_column, url_column]:
        if column and column not in selected_columns:
            selected_columns.append(column)

    query = f"""
        SELECT {", ".join(selected_columns)}
        FROM {table_name}
        WHERE {text_column} IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    rename_map = {
        text_column: "text"
    }

    if title_column:
        rename_map[title_column] = "title"

    if source_column:
        rename_map[source_column] = "source"

    if category_column:
        rename_map[category_column] = "category"

    if url_column:
        rename_map[url_column] = "url"

    df = df.rename(columns=rename_map)

    if "title" not in df.columns:
        df["title"] = "Untitled"

    if "source" not in df.columns:
        df["source"] = "Unknown"

    if "category" not in df.columns:
        df["category"] = "Unknown"

    if "url" not in df.columns:
        df["url"] = ""

    df["text"] = df["text"].fillna("").astype(str)
    df = df[df["text"].str.strip() != ""]

    return df


def get_matched_keywords(text, keywords):
    text_lower = text.lower()
    matched_keywords = []

    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched_keywords.append(keyword)

    return matched_keywords


def build_snippet(text, keywords, max_length=260):
    text = clean_text(text)
    text_lower = text.lower()

    match_position = -1

    for keyword in keywords:
        position = text_lower.find(keyword.lower())
        if position != -1:
            match_position = position
            break

    if match_position == -1:
        return text[:max_length]

    start = max(0, match_position - 90)
    end = min(len(text), match_position + max_length)

    snippet = text[start:end].strip()

    if start > 0:
        snippet = "..." + snippet

    if end < len(text):
        snippet = snippet + "..."

    return snippet


def normalize_confidence_scores(rows):
    if not rows:
        return rows

    raw_scores = [row["raw_support_score"] for row in rows]
    min_score = min(raw_scores)
    max_score = max(raw_scores)

    for row in rows:
        if max_score == min_score:
            confidence = 0.75
        else:
            normalized = (row["raw_support_score"] - min_score) / (max_score - min_score)
            confidence = 0.62 + (normalized * 0.28)

        row["Confidence Score"] = round(confidence, 2)

        if confidence >= 0.82:
            row["Severity Level"] = "High"
        elif confidence >= 0.70:
            row["Severity Level"] = "Medium"
        else:
            row["Severity Level"] = "Low"

        del row["raw_support_score"]

    return rows


@st.cache_data(show_spinner=False)
def generate_overall_risk_monitor():
    repository_df = load_text_repository()

    if repository_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    risk_rows = []
    evidence_rows = []

    for theme in RISK_THEMES:
        matched_rows = []
        all_matched_keywords = set()

        for _, row in repository_df.iterrows():
            text = clean_text(row["text"])
            matched_keywords = get_matched_keywords(text, theme["keywords"])

            if matched_keywords:
                all_matched_keywords.update(matched_keywords)

                matched_rows.append({
                    "title": row["title"],
                    "source": row["source"],
                    "category": row["category"],
                    "url": row["url"],
                    "text": text,
                    "matched_keywords": matched_keywords,
                    "match_count": len(matched_keywords)
                })

        if not matched_rows:
            continue

        matched_rows = sorted(
            matched_rows,
            key=lambda item: item["match_count"],
            reverse=True
        )

        matched_chunk_count = len(matched_rows)
        source_count = len(set(item["source"] for item in matched_rows))
        keyword_coverage = len(all_matched_keywords) / len(theme["keywords"])
        total_matches = sum(item["match_count"] for item in matched_rows)

        raw_support_score = (
            matched_chunk_count * 1.0
            + source_count * 8.0
            + len(all_matched_keywords) * 5.0
            + total_matches * 0.5
            + keyword_coverage * 20.0
        )

        top_evidence = matched_rows[:3]

        evidence_text = []
        for item in top_evidence:
            snippet = build_snippet(item["text"], item["matched_keywords"])
            matched_words = ", ".join(item["matched_keywords"])

            evidence_text.append(
                f"{item['source']} - {item['title']}: {snippet}"
            )

            evidence_rows.append({
                "Risk Theme": theme["title"],
                "Source": item["source"],
                "Category": item["category"],
                "Title": item["title"],
                "Matched Keywords": matched_words,
                "Evidence Snippet": snippet,
                "URL": item["url"]
            })

        risk_rows.append({
            "Risk Title": theme["title"],
            "Risk Category": theme["category"],
            "Severity Level": "",
            "Evidence Sources": source_count,
            "Matched Evidence Chunks": matched_chunk_count,
            "Keyword Coverage": f"{len(all_matched_keywords)}/{len(theme['keywords'])}",
            "Confidence Score": 0.0,
            "Evidence Summary": " | ".join(evidence_text),
            "raw_support_score": raw_support_score
        })

    risk_rows = normalize_confidence_scores(risk_rows)

    risk_df = pd.DataFrame(risk_rows)
    evidence_df = pd.DataFrame(evidence_rows)

    if not risk_df.empty:
        risk_df = risk_df.sort_values(
            by="Confidence Score",
            ascending=False
        )

    return risk_df, evidence_df


def render_risk_tab():
    st.subheader("Risk Monitor")

    st.write(
        "This section scans all stored BMW EV article chunks and converts risk-related "
        "evidence into risk themes, categories, severity levels, evidence snippets, "
        "and confidence scores. It does not require a user question."
    )

    with st.spinner("Scanning collected articles for strategic risk signals..."):
        risk_df, evidence_df = generate_overall_risk_monitor()

    if risk_df.empty:
        st.warning("No risk signals were found in the current knowledge base.")
        return

    high_count = int((risk_df["Severity Level"] == "High").sum())
    medium_count = int((risk_df["Severity Level"] == "Medium").sum())
    low_count = int((risk_df["Severity Level"] == "Low").sum())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Detected Risk Themes", len(risk_df))

    with col2:
        st.metric("High Severity", high_count)

    with col3:
        st.metric("Medium Severity", medium_count)

    with col4:
        st.metric("Low Severity", low_count)

    st.subheader("Risk Table")
    st.dataframe(risk_df, use_container_width=True)

    st.subheader("Evidence Behind Risks")

    if evidence_df.empty:
        st.info("No evidence snippets available.")
    else:
        st.dataframe(evidence_df, use_container_width=True)

    st.caption(
        "Confidence score represents relative evidence strength across all detected risk themes. "
        "It is based on matched chunks, supporting sources, keyword coverage, and total evidence matches."
    )