import json
import re
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from agent.validator import AgentValidator
from intelligence.strategic_analyzer import CEORecommendationEngine


class StrategicTools:
    def __init__(self, top_k=5, use_llm=False, ollama_model="qwen2.5:3b"):
        self.top_k = top_k
        self.use_llm = use_llm
        self.ollama_model = ollama_model
        self.engine = CEORecommendationEngine(top_k=top_k, use_llm=use_llm)
        self.validator = AgentValidator()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.db_path = Path(__file__).resolve().parents[1] / "data" / "ai_ceo.db"

    def retrieve_evidence_tool(self, user_goal):
        retrieved_items = self.engine.retriever.retrieve(
            user_goal,
            top_k=self.top_k
        )

        evidence_items = []

        for index, item in enumerate(retrieved_items, start=1):
            evidence_items.append({
                "evidence_id": f"E{index}",
                "rank": index,
                "title": item.get("title", "Untitled"),
                "source": item.get("source", "Unknown"),
                "category": item.get("category", "Unknown"),
                "url": item.get("url", ""),
                "text": item.get("text", item.get("chunk_text", "")),
                "similarity": item.get("similarity", item.get("score", ""))
            })

        return evidence_items

    def analyze_risks_tool(self, evidence_items):
        return self._analyze_by_focus(evidence_items, focus="risk")

    def analyze_opportunities_tool(self, evidence_items):
        return self._analyze_by_focus(evidence_items, focus="opportunity")

    def analyze_trends_tool(self, evidence_items):
        return self._analyze_by_focus(evidence_items, focus="trend")

    def analyze_competitors_tool(self, evidence_items):
        return self._analyze_by_focus(evidence_items, focus="competitor")

    def sentiment_tool(self, evidence_items):
        combined_text = " ".join(
            item.get("text", "") for item in evidence_items
        )

        if not combined_text.strip():
            return {
                "label": "Neutral",
                "compound": 0.0,
                "reason": "No evidence text was available for sentiment analysis."
            }

        score = self.sentiment_analyzer.polarity_scores(combined_text)
        compound = score["compound"]

        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"

        return {
            "label": label,
            "compound": round(compound, 4),
            "positive": round(score["pos"], 4),
            "neutral": round(score["neu"], 4),
            "negative": round(score["neg"], 4),
            "reason": "Sentiment is calculated from retrieved evidence using VADER."
        }

    def generate_recommendation_tool(self, user_goal, goal_type, evidence_items, analysis_results, sentiment):
        risks = analysis_results.get("risks", [])
        opportunities = analysis_results.get("opportunities", [])
        trends = analysis_results.get("trends", [])
        competitors = analysis_results.get("competitors", [])

        actions = []

        if goal_type == "risk_analysis":
            actions.append("Prioritize mitigation actions for the strongest evidence-supported risks.")
        elif goal_type == "opportunity_analysis":
            actions.append("Prioritize investment in the strongest evidence-supported opportunities.")
        elif goal_type == "trend_analysis":
            actions.append("Monitor the strongest evidence-supported industry and technology trends.")
        elif goal_type == "competitor_analysis":
            actions.append("Respond to competitor movements using evidence-supported market signals.")
        else:
            actions.append("Balance EV growth opportunities with strategic risk mitigation.")

        if opportunities:
            actions.append("Use opportunity signals to guide product, market, or technology priorities.")

        if risks:
            actions.append("Create management actions for the most important risk signals.")

        if trends:
            actions.append("Track trend signals continuously and update strategy as new evidence appears.")

        priority = self._decide_priority(goal_type, risks, opportunities, trends, competitors)
        confidence = self._decide_confidence(evidence_items, analysis_results)

        final_briefing = self._build_ceo_briefing(
            user_goal=user_goal,
            goal_type=goal_type,
            risks=risks,
            opportunities=opportunities,
            trends=trends,
            competitors=competitors,
            actions=actions,
            sentiment=sentiment,
            priority=priority,
            confidence=confidence
        )

        used_evidence_ids = [
            item["evidence_id"] for item in evidence_items[:3]
            if "evidence_id" in item
        ]

        return {
            "user_goal": user_goal,
            "question": user_goal,
            "goal_type": goal_type,
            "answer": final_briefing,
            "final_briefing": final_briefing,
            "recommendation": actions[0] if actions else "Review retrieved evidence before making a decision.",
            "actions": actions,
            "priority": priority,
            "confidence": confidence,
            "risks": risks,
            "opportunities": opportunities,
            "trends": trends,
            "competitors": competitors,
            "sentiment": sentiment,
            "evidence": evidence_items,
            "used_evidence_ids": used_evidence_ids,
            "generation_mode": "controlled_dynamic_agentic_rag"
        }

    def validate_recommendation_tool(self, result):
        return self.validator.validate(result)

    def overall_risk_monitor_tool(self, max_articles=60):
        articles = self._load_full_articles(max_articles=max_articles)

        if not articles:
            return {
                "items": [],
                "evidence": [],
                "articles_analyzed": 0,
                "error": "No full articles found in the documents table."
            }

        items = self._extract_overall_signals_with_llm(
            signal_type="risk",
            articles=articles
        )

        normalized_items = self._normalize_overall_items(items, signal_type="risk")
        evidence_rows = self._build_overall_evidence_rows(normalized_items, signal_type="Risk")

        return {
            "items": normalized_items,
            "evidence": evidence_rows,
            "articles_analyzed": len(articles),
            "error": "" if normalized_items else "No risk signals were generated. Check if Ollama is running."
        }

    def overall_opportunity_monitor_tool(self, max_articles=60):
        articles = self._load_full_articles(max_articles=max_articles)

        if not articles:
            return {
                "items": [],
                "evidence": [],
                "articles_analyzed": 0,
                "error": "No full articles found in the documents table."
            }

        items = self._extract_overall_signals_with_llm(
            signal_type="opportunity",
            articles=articles
        )

        normalized_items = self._normalize_overall_items(items, signal_type="opportunity")
        evidence_rows = self._build_overall_evidence_rows(normalized_items, signal_type="Opportunity")

        return {
            "items": normalized_items,
            "evidence": evidence_rows,
            "articles_analyzed": len(articles),
            "error": "" if normalized_items else "No opportunity signals were generated. Check if Ollama is running."
        }

    def _extract_overall_signals_with_llm(self, signal_type, articles):
        batch_size = 5
        batch_items = []

        for start in range(0, len(articles), batch_size):
            batch = articles[start:start + batch_size]

            prompt = self._build_batch_extraction_prompt(
                signal_type=signal_type,
                articles=batch,
                start_index=start
            )

            parsed = self._call_ollama_json(prompt)
            items = parsed.get("items", [])

            if isinstance(items, list):
                batch_items.extend(items)

        if not batch_items:
            return []

        merge_prompt = self._build_merge_prompt(
            signal_type=signal_type,
            items=batch_items
        )

        merged = self._call_ollama_json(merge_prompt)
        merged_items = merged.get("items", [])

        if isinstance(merged_items, list) and merged_items:
            return merged_items

        return batch_items

    def _build_batch_extraction_prompt(self, signal_type, articles, start_index=0):
        article_blocks = []

        for local_index, article in enumerate(articles, start=1):
            global_index = start_index + local_index
            text = self._shorten_text(article.get("text", ""), max_chars=1800)

            article_blocks.append(
                f"""
Article {global_index}
Title: {article.get("title", "Untitled")}
Source: {article.get("source", "Unknown")}
Category: {article.get("category", "Unknown")}
URL: {article.get("url", "")}
Article Text:
{text}
"""
            )

        article_text = "\n".join(article_blocks)

        if signal_type == "risk":
            task = "Identify strategic risks for BMW's EV strategy from these articles."
            schema = """
{
  "items": [
    {
      "title": "short risk title",
      "category": "risk category",
      "evidence_reason": "short reason based only on article evidence",
      "supporting_source": "source name",
      "supporting_title": "article title",
      "evidence_snippet": "short evidence snippet from the article"
    }
  ]
}
"""
        else:
            task = "Identify strategic opportunities for BMW's EV strategy from these articles."
            schema = """
{
  "items": [
    {
      "title": "short opportunity title",
      "evidence_reason": "short reason based only on article evidence",
      "supporting_source": "source name",
      "supporting_title": "article title",
      "evidence_snippet": "short evidence snippet from the article"
    }
  ]
}
"""

        prompt = f"""
You are a strategic intelligence extraction tool.

Task:
{task}

Rules:
- Use the provided articles as the only evidence source.
- Do not use predefined risk themes.
- Do not use predefined opportunity themes.
- Do not use keyword lists.
- Decide the signals from article meaning and context.
- Do not invent facts.
- Return only valid JSON.
- Extract 1 to 3 strongest items from this batch.
- Do not assign confidence score.
- Do not assign severity or impact level.

JSON schema:
{schema}

Articles:
{article_text}
"""
        return prompt

    def _build_merge_prompt(self, signal_type, items):
        if signal_type == "risk":
            task = "Merge the extracted batch-level risks into 4 to 6 final BMW EV strategic risks."
            schema = """
{
  "items": [
    {
      "title": "final risk title",
      "category": "risk category",
      "evidence_reason": "combined evidence-based reason",
      "supporting_source": "source name",
      "supporting_title": "article title",
      "evidence_snippet": "short evidence snippet"
    }
  ]
}
"""
        else:
            task = "Merge the extracted batch-level opportunities into 4 to 6 final BMW EV strategic opportunities."
            schema = """
{
  "items": [
    {
      "title": "final opportunity title",
      "evidence_reason": "combined evidence-based reason",
      "supporting_source": "source name",
      "supporting_title": "article title",
      "evidence_snippet": "short evidence snippet"
    }
  ]
}
"""

        prompt = f"""
You are a strategic intelligence consolidation tool.

Task:
{task}

Rules:
- Merge duplicates.
- Keep only the strongest evidence-supported signals.
- Do not invent new facts.
- Use only the extracted items below.
- Return only valid JSON.
- Do not assign confidence score.
- Do not assign severity or impact level.

JSON schema:
{schema}

Extracted items:
{json.dumps(items, indent=2)}
"""
        return prompt

    def _call_ollama_json(self, prompt):
        response_text = self._call_ollama(prompt)

        if not response_text:
            return {}

        cleaned = response_text.strip()
        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if match:
            cleaned = match.group(0)

        try:
            return json.loads(cleaned)
        except Exception:
            return {}

    def _call_ollama(self, prompt):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.0
                    }
                },
                timeout=180
            )

            if response.status_code != 200:
                return ""

            data = response.json()
            return data.get("response", "").strip()

        except Exception:
            return ""

    def _normalize_overall_items(self, items, signal_type):
        rows = []

        if not isinstance(items, list):
            return rows

        for item in items:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title", "")).strip()

            if not title:
                continue

            evidence_reason = str(item.get("evidence_reason", "")).strip()
            supporting_source = str(item.get("supporting_source", "")).strip()
            supporting_title = str(item.get("supporting_title", "")).strip()
            evidence_snippet = str(item.get("evidence_snippet", "")).strip()

            support_strength = self._get_support_strength(
                evidence_reason=evidence_reason,
                supporting_source=supporting_source,
                supporting_title=supporting_title,
                evidence_snippet=evidence_snippet
            )

            if signal_type == "risk":
                rows.append({
                    "Risk Title": title,
                    "Risk Category": str(item.get("category", "Strategic Risk")).strip(),
                    "Severity Level": "",
                    "Confidence Score": 0.0,
                    "Evidence Reason": evidence_reason,
                    "Supporting Source": supporting_source,
                    "Supporting Article": supporting_title,
                    "Evidence Snippet": evidence_snippet,
                    "_Support Strength": support_strength
                })

            else:
                rows.append({
                    "Opportunity Title": title,
                    "Impact Level": "",
                    "Confidence Score": 0.0,
                    "Evidence Reason": evidence_reason,
                    "Supporting Source": supporting_source,
                    "Supporting Article": supporting_title,
                    "Evidence Snippet": evidence_snippet,
                    "_Support Strength": support_strength
                })

        rows = self._remove_duplicate_overall_items(rows, signal_type)
        rows = self._assign_relative_scores(rows, signal_type)

        return rows[:6]

    def _get_support_strength(
        self,
        evidence_reason,
        supporting_source,
        supporting_title,
        evidence_snippet
    ):
        score = 0

        if supporting_source:
            score += 1

        if supporting_title:
            score += 1

        if len(evidence_reason) >= 80:
            score += 1

        if len(evidence_reason) >= 160:
            score += 1

        if len(evidence_snippet) >= 80:
            score += 1

        if len(evidence_snippet) >= 160:
            score += 1

        return score

    def _remove_duplicate_overall_items(self, rows, signal_type):
        title_key = "Risk Title" if signal_type == "risk" else "Opportunity Title"
        unique_rows = []

        for row in rows:
            title = row.get(title_key, "")
            duplicate_found = False

            for existing in unique_rows:
                existing_title = existing.get(title_key, "")

                similarity = SequenceMatcher(
                    None,
                    title.lower(),
                    existing_title.lower()
                ).ratio()

                if similarity > 0.82:
                    duplicate_found = True

                    current_strength = row.get("_Support Strength", 0)
                    existing_strength = existing.get("_Support Strength", 0)

                    if current_strength > existing_strength:
                        existing.update(row)

                    break

            if not duplicate_found:
                unique_rows.append(row)

        unique_rows = sorted(
            unique_rows,
            key=lambda item: item.get("_Support Strength", 0),
            reverse=True
        )

        return unique_rows

    def _assign_relative_scores(self, rows, signal_type):
        if not rows:
            return rows

        cleaned_rows = []

        for index, row in enumerate(rows):
            support_strength = row.get("_Support Strength", 0)

            base_score = 0.88 - (index * 0.06)
            support_bonus = min(support_strength * 0.005, 0.02)

            confidence = base_score + support_bonus
            confidence = max(0.58, min(confidence, 0.90))
            confidence = round(confidence, 2)

            row["Confidence Score"] = confidence

            if signal_type == "risk":
                if confidence >= 0.84:
                    row["Severity Level"] = "High"
                elif confidence >= 0.70:
                    row["Severity Level"] = "Medium"
                else:
                    row["Severity Level"] = "Low"
            else:
                if confidence >= 0.84:
                    row["Impact Level"] = "High"
                elif confidence >= 0.70:
                    row["Impact Level"] = "Medium"
                else:
                    row["Impact Level"] = "Low"

            if "_Support Strength" in row:
                del row["_Support Strength"]

            cleaned_rows.append(row)

        return cleaned_rows

    def _build_overall_evidence_rows(self, items, signal_type):
        rows = []

        if signal_type == "Risk":
            title_key = "Risk Title"
        else:
            title_key = "Opportunity Title"

        for item in items:
            rows.append({
                f"{signal_type} Signal": item.get(title_key, ""),
                "Evidence Reason": item.get("Evidence Reason", ""),
                "Supporting Source": item.get("Supporting Source", ""),
                "Supporting Article": item.get("Supporting Article", ""),
                "Evidence Snippet": item.get("Evidence Snippet", ""),
                "Confidence Score": item.get("Confidence Score", "")
            })

        return rows

    def _load_full_articles(self, max_articles=60):
        if not self.db_path.exists():
            return []

        conn = sqlite3.connect(self.db_path)

        try:
            columns = self._get_columns(conn, "documents")

            if not columns:
                conn.close()
                return []

            text_column = self._choose_column(
                columns,
                ["clean_text", "content", "text", "article_text", "raw_text", "summary"]
            )
            title_column = self._choose_column(columns, ["title", "headline", "name"])
            source_column = self._choose_column(columns, ["source", "publisher", "source_name"])
            category_column = self._choose_column(columns, ["category", "source_type", "topic"])
            url_column = self._choose_column(columns, ["url", "link"])

            if text_column is None:
                conn.close()
                return []

            selected_columns = [text_column]

            for column in [title_column, source_column, category_column, url_column]:
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
            df["text_length"] = df["text"].str.len()
            df = df.sort_values(by="text_length", ascending=False)

            if len(df) > max_articles:
                df = df.head(max_articles)

            articles = []

            for _, row in df.iterrows():
                articles.append({
                    "title": row["title"],
                    "source": row["source"],
                    "category": row["category"],
                    "url": row["url"],
                    "text": row["text"]
                })

            return articles

        except Exception:
            conn.close()
            return []

    def _get_columns(self, conn, table_name):
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

    def _choose_column(self, columns, possible_names):
        for name in possible_names:
            if name in columns:
                return name

        return None

    def _analyze_by_focus(self, evidence_items, focus):
        findings = []

        for item in evidence_items:
            text = item.get("text", "")
            title = item.get("title", "Untitled")
            source = item.get("source", "Unknown")
            evidence_id = item.get("evidence_id", "")

            if not text.strip():
                continue

            finding = {
                "title": f"{focus.title()} signal from retrieved evidence",
                "reason": f"This signal is derived from retrieved evidence: {title}",
                "source": source,
                "evidence_id": evidence_id
            }

            if focus == "risk":
                finding["category"] = "Strategic Risk"
                finding["severity"] = "Medium"

            elif focus == "opportunity":
                finding["impact"] = "Medium"

            elif focus == "trend":
                finding["type"] = "Market / Technology Trend"

            elif focus == "competitor":
                finding["category"] = "Competitive Signal"

            findings.append(finding)

        return findings[:3]

    def _decide_priority(self, goal_type, risks, opportunities, trends, competitors):
        if goal_type in ["risk_analysis", "competitor_analysis"] and risks:
            return "High"

        if goal_type == "opportunity_analysis" and opportunities:
            return "High"

        if goal_type == "strategic_decision" and (risks or opportunities):
            return "High"

        if goal_type == "trend_analysis" and trends:
            return "Medium"

        return "Medium"

    def _decide_confidence(self, evidence_items, analysis_results):
        evidence_count = len(evidence_items)
        signal_count = (
            len(analysis_results.get("risks", []))
            + len(analysis_results.get("opportunities", []))
            + len(analysis_results.get("trends", []))
            + len(analysis_results.get("competitors", []))
        )

        if evidence_count >= 5 and signal_count >= 3:
            return "High"

        if evidence_count >= 3:
            return "Medium"

        return "Low"

    def _build_ceo_briefing(
        self,
        user_goal,
        goal_type,
        risks,
        opportunities,
        trends,
        competitors,
        actions,
        sentiment,
        priority,
        confidence
    ):
        lines = []

        lines.append(f"CEO Goal: {user_goal}")
        lines.append("")
        lines.append(f"Detected Goal Type: {goal_type}")
        lines.append("")
        lines.append("Executive Recommendation:")
        lines.append(actions[0] if actions else "Review retrieved evidence before making a decision.")
        lines.append("")
        lines.append("Why this matters:")
        lines.append(
            "The recommendation is based on retrieved evidence from the knowledge repository, "
            "not only on the language model's internal knowledge."
        )
        lines.append("")

        lines.append("Risk Signals:")
        if risks:
            for risk in risks:
                lines.append(f"- {risk.get('title', 'Risk')}: {risk.get('reason', '')}")
        else:
            lines.append("- No major risk signal was selected for this goal type.")

        lines.append("")
        lines.append("Opportunity Signals:")
        if opportunities:
            for opportunity in opportunities:
                lines.append(f"- {opportunity.get('title', 'Opportunity')}: {opportunity.get('reason', '')}")
        else:
            lines.append("- No major opportunity signal was selected for this goal type.")

        lines.append("")
        lines.append("Trend Signals:")
        if trends:
            for trend in trends:
                lines.append(f"- {trend.get('title', 'Trend')}: {trend.get('reason', '')}")
        else:
            lines.append("- No major trend signal was extracted from the retrieved evidence.")

        if competitors:
            lines.append("")
            lines.append("Competitive Signals:")
            for competitor in competitors:
                lines.append(f"- {competitor.get('title', 'Competitive signal')}: {competitor.get('reason', '')}")

        lines.append("")
        lines.append("Recommended Actions:")
        for action in actions:
            lines.append(f"- {action}")

        lines.append("")
        lines.append(f"Priority: {priority}")
        lines.append(f"Confidence: {confidence}")
        lines.append(f"Evidence Sentiment: {sentiment.get('label', 'Unknown')}")

        return "\n".join(lines)

    def _shorten_text(self, text, max_chars=1800):
        text = str(text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + "..."


if __name__ == "__main__":
    tools = StrategicTools(top_k=3, use_llm=False)

    print("Testing overall risk monitor...")
    risk_result = tools.overall_risk_monitor_tool(max_articles=10)
    print("Risks:", len(risk_result.get("items", [])))

    print("Testing overall opportunity monitor...")
    opportunity_result = tools.overall_opportunity_monitor_tool(max_articles=10)
    print("Opportunities:", len(opportunity_result.get("items", [])))