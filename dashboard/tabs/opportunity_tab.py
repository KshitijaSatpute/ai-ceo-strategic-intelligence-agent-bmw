import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ai_ceo.db"


OPPORTUNITY_THEMES = [
    {
        "title": "Accelerate Neue Klasse product momentum",
        "impact": "High",
        "keywords": [
            "neue klasse", "ix3", "i3", "new class", "platform",
            "next-generation", "electric sedan", "electric suv"
        ]
    },
    {
        "title": "Use battery range and fast charging as EV differentiators",
        "impact": "High",
        "keywords": [
            "battery", "range", "fast charging", "charging", "800v",
            "kwh", "energy density", "charging speed"
        ]
    },
    {
        "title": "Strengthen premium electric SUV positioning",
        "impact": "High",
        "keywords": [
            "suv", "ix5", "x5", "luxury suv", "premium", "electric suv",
            "crossover", "high-end"
        ]
    },
    {
        "title": "Improve competitive positioning against Tesla and BYD",
        "impact": "Medium",
        "keywords": [
            "tesla", "byd", "model y", "competition", "competitor",
            "rival", "market share", "price", "ev sales"
        ]
    },
    {
        "title": "Expand EV strategy in Europe and growth markets",
        "impact": "Medium",
        "keywords": [
            "europe", "european", "market growth", "ev sales",
            "growth", "adoption", "latin america", "global market"
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
        del row["raw_support_score"]

    return rows


@st.cache_data(show_spinner=False)
def generate_overall_opportunity_monitor():
    repository_df = load_text_repository()

    if repository_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    opportunity_rows = []
    evidence_rows = []

    for theme in OPPORTUNITY_THEMES:
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
                "Opportunity Theme": theme["title"],
                "Source": item["source"],
                "Category": item["category"],
                "Title": item["title"],
                "Matched Keywords": matched_words,
                "Evidence Snippet": snippet,
                "URL": item["url"]
            })

        opportunity_rows.append({
            "Opportunity Title": theme["title"],
            "Impact Level": theme["impact"],
            "Evidence Sources": source_count,
            "Matched Evidence Chunks": matched_chunk_count,
            "Keyword Coverage": f"{len(all_matched_keywords)}/{len(theme['keywords'])}",
            "Confidence Score": 0.0,
            "Evidence Summary": " | ".join(evidence_text),
            "raw_support_score": raw_support_score
        })

    opportunity_rows = normalize_confidence_scores(opportunity_rows)

    opportunity_df = pd.DataFrame(opportunity_rows)
    evidence_df = pd.DataFrame(evidence_rows)

    if not opportunity_df.empty:
        opportunity_df = opportunity_df.sort_values(
            by="Confidence Score",
            ascending=False
        )

    return opportunity_df, evidence_df


def render_opportunity_tab():
    st.subheader("Opportunity Monitor")

    st.write(
        "This section scans all stored BMW EV article chunks and converts opportunity-related "
        "evidence into opportunity themes, impact levels, evidence snippets, and confidence scores. "
        "It does not require a user question."
    )

    with st.spinner("Scanning collected articles for strategic opportunity signals..."):
        opportunity_df, evidence_df = generate_overall_opportunity_monitor()

    if opportunity_df.empty:
        st.warning("No opportunity signals were found in the current knowledge base.")
        return

    high_count = int((opportunity_df["Impact Level"] == "High").sum())
    medium_count = int((opportunity_df["Impact Level"] == "Medium").sum())
    low_count = int((opportunity_df["Impact Level"] == "Low").sum())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Detected Opportunities", len(opportunity_df))

    with col2:
        st.metric("High Impact", high_count)

    with col3:
        st.metric("Medium Impact", medium_count)

    with col4:
        st.metric("Low Impact", low_count)

    st.subheader("Opportunity Table")
    st.dataframe(opportunity_df, use_container_width=True)

    st.subheader("Evidence Behind Opportunities")

    if evidence_df.empty:
        st.info("No evidence snippets available.")
    else:
        st.dataframe(evidence_df, use_container_width=True)

    st.caption(
        "Confidence score represents relative evidence strength across all detected opportunity themes. "
        "It is based on matched chunks, supporting sources, keyword coverage, and total evidence matches."
    )