import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def get_database_path():
    return Path(__file__).resolve().parents[2] / "data" / "ai_ceo.db"


def choose_column(columns, possible_names):
    for name in possible_names:
        if name in columns:
            return name
    return None


def load_documents_for_sentiment():
    db_path = get_database_path()

    if not db_path.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)

    try:
        columns_df = pd.read_sql_query("PRAGMA table_info(documents)", conn)
        columns = columns_df["name"].tolist()

        text_column = choose_column(
            columns,
            ["clean_text", "content", "text", "article_text", "raw_text", "summary"]
        )

        title_column = choose_column(
            columns,
            ["title", "headline", "name"]
        )

        source_column = choose_column(
            columns,
            ["source", "publisher", "source_name"]
        )

        category_column = choose_column(
            columns,
            ["category", "source_type", "topic"]
        )

        date_column = choose_column(
            columns,
            ["published_date", "published_at", "collected_at", "created_at", "date"]
        )

        if text_column is None:
            conn.close()
            return pd.DataFrame()

        selected_columns = [text_column]

        if title_column:
            selected_columns.append(title_column)

        if source_column:
            selected_columns.append(source_column)

        if category_column:
            selected_columns.append(category_column)

        if date_column:
            selected_columns.append(date_column)

        selected_columns = list(dict.fromkeys(selected_columns))

        query = f"""
            SELECT {", ".join(selected_columns)}
            FROM documents
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

        if date_column:
            rename_map[date_column] = "date"

        df = df.rename(columns=rename_map)

        if "title" not in df.columns:
            df["title"] = "Untitled"

        if "source" not in df.columns:
            df["source"] = "Unknown"

        if "category" not in df.columns:
            df["category"] = "Unknown"

        if "date" not in df.columns:
            df["date"] = ""

        df["text"] = df["text"].fillna("").astype(str)
        df = df[df["text"].str.strip() != ""]

        return df

    except Exception as error:
        conn.close()
        st.error(f"Could not load documents for sentiment analysis: {error}")
        return pd.DataFrame()


def calculate_sentiment(df):
    analyzer = SentimentIntensityAnalyzer()
    rows = []

    for _, row in df.iterrows():
        text = row["text"]
        score = analyzer.polarity_scores(text)
        compound = score["compound"]

        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        rows.append({
            "Title": row["title"],
            "Source": row["source"],
            "Category": row["category"],
            "Date": row["date"],
            "Sentiment": label,
            "Compound Score": round(compound, 4),
            "Positive": round(score["pos"], 4),
            "Neutral": round(score["neu"], 4),
            "Negative": round(score["neg"], 4)
        })

    return pd.DataFrame(rows)


def render_sentiment_tab():
    st.subheader("Sentiment Analysis")

    st.write(
        "This section analyzes the tone of collected BMW EV-related public articles "
        "using VADER sentiment analysis."
    )

    if st.button("Run Sentiment Analysis"):
        documents_df = load_documents_for_sentiment()

        if documents_df.empty:
            st.warning("No documents available for sentiment analysis.")
            return

        sentiment_df = calculate_sentiment(documents_df)

        total_documents = len(sentiment_df)
        positive_count = int((sentiment_df["Sentiment"] == "Positive").sum())
        neutral_count = int((sentiment_df["Sentiment"] == "Neutral").sum())
        negative_count = int((sentiment_df["Sentiment"] == "Negative").sum())
        average_score = round(sentiment_df["Compound Score"].mean(), 4)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Documents Analyzed", total_documents)

        with col2:
            st.metric("Positive", positive_count)

        with col3:
            st.metric("Neutral", neutral_count)

        with col4:
            st.metric("Negative", negative_count)

        with col5:
            st.metric("Average Score", average_score)

        st.subheader("Sentiment Distribution")
        distribution_df = sentiment_df["Sentiment"].value_counts().reset_index()
        distribution_df.columns = ["Sentiment", "Count"]
        st.bar_chart(distribution_df.set_index("Sentiment"))

        st.subheader("Sentiment by Source")
        source_df = (
            sentiment_df
            .groupby(["Source", "Sentiment"])
            .size()
            .reset_index(name="Count")
        )
        st.dataframe(source_df, use_container_width=True)

        st.subheader("Sentiment by Category")
        category_df = (
            sentiment_df
            .groupby(["Category", "Sentiment"])
            .size()
            .reset_index(name="Count")
        )
        st.dataframe(category_df, use_container_width=True)

        st.subheader("Document-level Sentiment")
        st.dataframe(
            sentiment_df[
                [
                    "Title",
                    "Source",
                    "Category",
                    "Sentiment",
                    "Compound Score"
                ]
            ],
            use_container_width=True
        )