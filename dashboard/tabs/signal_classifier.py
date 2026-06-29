import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ai_ceo.db"


RISK_KEYWORDS = {
    "Competition / Market Pressure": [
        "competition", "competitor", "competitive", "rival", "tesla", "byd",
        "mercedes", "audi", "volkswagen", "market share", "price war",
        "pricing pressure", "market pressure"
    ],
    "Regulation / Policy Risk": [
        "regulation", "regulatory", "emissions", "ban", "policy",
        "compliance", "tariff", "law", "government", "approval",
        "subsidy cut", "incentive cut"
    ],
    "Supply Chain / Production Risk": [
        "supply chain", "shortage", "production delay", "supplier",
        "raw material", "battery supply", "semiconductor", "factory",
        "manufacturing", "delivery delay"
    ],
    "Demand / Adoption Risk": [
        "weak demand", "slow demand", "adoption barrier", "slowdown",
        "sales decline", "sales drop", "slump", "customer hesitation",
        "affordability", "soft demand"
    ],
    "Technology / Execution Risk": [
        "battery issue", "charging issue", "range anxiety", "software issue",
        "recall", "delay", "technology risk", "execution risk",
        "reliability", "technical problem", "charging network"
    ],
    "Financial / Cost Pressure": [
        "cost pressure", "margin pressure", "profit warning", "earnings pressure",
        "expensive", "price cut", "loss", "financial pressure",
        "investment burden", "revenue decline"
    ]
}


OPPORTUNITY_KEYWORDS = {
    "Product / Innovation Opportunity": [
        "new product", "launch", "platform", "innovation", "technology",
        "software", "battery", "charging", "range", "next-generation",
        "neue klasse", "new model", "product launch", "electric platform"
    ],
    "Market Growth Opportunity": [
        "growth", "market expansion", "sales growth", "demand growth",
        "customer demand", "global market", "new market", "increase",
        "strong demand", "market opportunity"
    ],
    "Partnership / Ecosystem Opportunity": [
        "partnership", "partner", "collaboration", "joint venture",
        "alliance", "ecosystem", "supplier partnership", "charging partner"
    ],
    "Competitive Positioning Opportunity": [
        "advantage", "differentiation", "premium", "leadership",
        "market position", "competitive edge", "brand strength",
        "luxury", "performance", "premium segment"
    ],
    "Regulation / Policy Opportunity": [
        "subsidy", "incentive", "policy support", "tax credit",
        "government support", "emissions target", "regulatory support"
    ],
    "Customer / Adoption Opportunity": [
        "customer", "consumer adoption", "affordability", "user experience",
        "charging convenience", "range improvement", "customer interest",
        "adoption growth"
    ]
}


def clean_text(text):
    text = "" if text is None else str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def choose_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def get_table_columns(conn, table_name):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,)
    )

    if cursor.fetchone() is None:
        return []

    cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()

    return [row[1] for row in rows]


def load_repository_documents():
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)

    try:
        columns = get_table_columns(conn, "documents")

        if not columns:
            conn.close()
            return pd.DataFrame()

        text_column = choose_column(
            columns,
            ["clean_text", "content", "text", "article_text", "raw_text", "summary"]
        )
        title_column = choose_column(columns, ["title", "headline", "name"])
        source_column = choose_column(columns, ["source", "publisher", "source_name"])
        source_type_column = choose_column(columns, ["source_type", "type"])
        category_column = choose_column(columns, ["category", "topic"])
        date_column = choose_column(
            columns,
            ["published_date", "published_at", "collected_at", "created_at", "date"]
        )
        url_column = choose_column(columns, ["url", "link"])

        if text_column is None:
            conn.close()
            return pd.DataFrame()

        selected_columns = [text_column]

        for column in [
            title_column,
            source_column,
            source_type_column,
            category_column,
            date_column,
            url_column
        ]:
            if column and column not in selected_columns:
                selected_columns.append(column)

        query = f"""
            SELECT {", ".join(selected_columns)}
            FROM documents
            WHERE {text_column} IS NOT NULL
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        rename_map = {text_column: "text"}

        if title_column:
            rename_map[title_column] = "title"
        if source_column:
            rename_map[source_column] = "source"
        if source_type_column:
            rename_map[source_type_column] = "source_type"
        if category_column:
            rename_map[category_column] = "category"
        if date_column:
            rename_map[date_column] = "date"
        if url_column:
            rename_map[url_column] = "url"

        df = df.rename(columns=rename_map)

        default_columns = {
            "title": "Untitled",
            "source": "Unknown",
            "source_type": "Unknown",
            "category": "Unknown",
            "date": "",
            "url": ""
        }

        for column, default_value in default_columns.items():
            if column not in df.columns:
                df[column] = default_value

            df[column] = df[column].fillna(default_value).astype(str)

        df["text"] = df["text"].fillna("").astype(str)
        df = df[df["text"].str.strip() != ""].reset_index(drop=True)
        df["Document ID"] = df.index + 1

        return df

    except Exception as error:
        conn.close()
        st.error(f"Could not load repository documents: {error}")
        return pd.DataFrame()


def keyword_in_text(keyword, text):
    keyword = keyword.lower().strip()
    text = text.lower()

    if " " in keyword:
        return keyword in text

    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text) is not None


def calculate_keyword_score(text, title, keyword_groups):
    combined_text = f"{title} {text}".lower()
    title_lower = title.lower()

    best_theme = ""
    best_keywords = []
    best_score = 0.0

    for theme, keywords in keyword_groups.items():
        matched_keywords = []

        for keyword in keywords:
            if keyword_in_text(keyword, combined_text):
                matched_keywords.append(keyword)

        if not matched_keywords:
            continue

        phrase_hits = sum(1 for keyword in matched_keywords if " " in keyword)
        title_hits = sum(
            1 for keyword in matched_keywords
            if keyword_in_text(keyword, title_lower)
        )

        score = (
            len(matched_keywords) * 1.0
            + phrase_hits * 0.8
            + title_hits * 0.5
        )

        if score > best_score:
            best_score = score
            best_theme = theme
            best_keywords = matched_keywords

    return best_score, best_theme, best_keywords


def build_evidence_preview(text, matched_keywords, max_length=300):
    text = clean_text(text)

    if not text:
        return ""

    if not matched_keywords:
        return text[:max_length]

    text_lower = text.lower()
    first_position = -1

    for keyword in matched_keywords:
        position = text_lower.find(keyword.lower())

        if position != -1:
            first_position = position
            break

    if first_position == -1:
        return text[:max_length]

    start = max(0, first_position - 100)
    end = min(len(text), first_position + max_length)

    preview = text[start:end].strip()

    if start > 0:
        preview = "..." + preview

    if end < len(text):
        preview = preview + "..."

    return preview


def classify_document(row):
    text = clean_text(row["text"])
    title = clean_text(row["title"])

    risk_score, risk_theme, risk_keywords = calculate_keyword_score(
        text=text,
        title=title,
        keyword_groups=RISK_KEYWORDS
    )

    opportunity_score, opportunity_theme, opportunity_keywords = calculate_keyword_score(
        text=text,
        title=title,
        keyword_groups=OPPORTUNITY_KEYWORDS
    )

    if risk_score == 0 and opportunity_score == 0:
        signal_type = "Neutral"
        final_theme = "No strong signal"
        final_keywords = []
        final_score = 0.0

    elif risk_score > opportunity_score:
        signal_type = "Risk"
        final_theme = risk_theme
        final_keywords = risk_keywords
        final_score = risk_score

    elif opportunity_score > risk_score:
        signal_type = "Opportunity"
        final_theme = opportunity_theme
        final_keywords = opportunity_keywords
        final_score = opportunity_score

    else:
        signal_type = "Neutral"
        final_theme = "Balanced risk and opportunity signal"
        final_keywords = risk_keywords + opportunity_keywords
        final_score = risk_score

    return {
        "Document ID": row["Document ID"],
        "Signal Type": signal_type,
        "Final Theme": final_theme,
        "Raw Evidence Score": final_score,
        "Risk Score": risk_score,
        "Opportunity Score": opportunity_score,
        "Title": row["title"],
        "Source": row["source"],
        "Source Type": row["source_type"],
        "Category": row["category"],
        "Date": row["date"],
        "Matched Keywords": ", ".join(final_keywords),
        "Why Classified": (
            f"Final label: {signal_type}. "
            f"Risk score = {risk_score:.2f}, Opportunity score = {opportunity_score:.2f}. "
            f"Matched keywords: {', '.join(final_keywords) if final_keywords else 'None'}"
        ),
        "Evidence Preview": build_evidence_preview(text, final_keywords),
        "URL": row["url"]
    }


def assign_relative_levels(df, label_column):
    if df.empty:
        return df

    df = df.sort_values(
        by=["Raw Evidence Score"],
        ascending=False
    ).reset_index(drop=True)

    total = len(df)
    scores = []
    levels = []

    for index in range(total):
        if total == 1:
            relative_position = 0
        else:
            relative_position = index / (total - 1)

        evidence_score = 0.90 - (relative_position * 0.35)
        evidence_score = round(max(0.55, min(evidence_score, 0.90)), 2)

        if relative_position <= 0.30:
            level = "High"
        elif relative_position <= 0.75:
            level = "Medium"
        else:
            level = "Low"

        scores.append(evidence_score)
        levels.append(level)

    df["Evidence Strength Score"] = scores
    df[label_column] = levels

    return df


@st.cache_data(show_spinner=False)
def generate_signal_classification():
    docs_df = load_repository_documents()

    if docs_df.empty:
        return pd.DataFrame(), 0

    rows = []

    for _, row in docs_df.iterrows():
        rows.append(classify_document(row))

    classified_df = pd.DataFrame(rows)
    total_documents = len(docs_df)

    return classified_df, total_documents