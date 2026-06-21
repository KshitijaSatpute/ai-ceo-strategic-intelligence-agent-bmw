import sqlite3
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils.config import DB_PATH


class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def get_documents(self):
        conn = sqlite3.connect(DB_PATH)

        query = """
        SELECT 
            id,
            title,
            source,
            category,
            content
        FROM documents
        WHERE content IS NOT NULL
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def classify_sentiment(self, compound_score):
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        else:
            return "Neutral"

    def analyze_text(self, text):
        if not text:
            return {
                "compound": 0.0,
                "positive": 0.0,
                "neutral": 0.0,
                "negative": 0.0,
                "sentiment": "Neutral"
            }

        scores = self.analyzer.polarity_scores(text)
        sentiment = self.classify_sentiment(scores["compound"])

        return {
            "compound": scores["compound"],
            "positive": scores["pos"],
            "neutral": scores["neu"],
            "negative": scores["neg"],
            "sentiment": sentiment
        }

    def analyze_documents(self):
        df = self.get_documents()

        results = []

        for _, row in df.iterrows():
            text = str(row["title"]) + " " + str(row["content"])
            scores = self.analyze_text(text)

            results.append({
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "category": row["category"],
                "compound": scores["compound"],
                "positive": scores["positive"],
                "neutral": scores["neutral"],
                "negative": scores["negative"],
                "sentiment": scores["sentiment"]
            })

        result_df = pd.DataFrame(results)
        return result_df

    def get_sentiment_summary(self):
        df = self.analyze_documents()

        if df.empty:
            return {
                "documents": df,
                "overall_summary": pd.DataFrame(),
                "source_summary": pd.DataFrame(),
                "category_summary": pd.DataFrame()
            }

        overall_summary = (
            df["sentiment"]
            .value_counts()
            .reset_index()
        )
        overall_summary.columns = ["sentiment", "count"]

        source_summary = (
            df.groupby(["source", "sentiment"])
            .size()
            .reset_index(name="count")
            .sort_values(["source", "count"], ascending=[True, False])
        )

        category_summary = (
            df.groupby(["category", "sentiment"])
            .size()
            .reset_index(name="count")
            .sort_values(["category", "count"], ascending=[True, False])
        )

        return {
            "documents": df,
            "overall_summary": overall_summary,
            "source_summary": source_summary,
            "category_summary": category_summary
        }


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    summary = analyzer.get_sentiment_summary()

    print("\nOverall Sentiment Summary")
    print(summary["overall_summary"])

    print("\nSource Sentiment Summary")
    print(summary["source_summary"])

    print("\nCategory Sentiment Summary")
    print(summary["category_summary"])

    print("\nSample Document Sentiments")
    print(summary["documents"][["title", "source", "category", "compound", "sentiment"]].head(10))