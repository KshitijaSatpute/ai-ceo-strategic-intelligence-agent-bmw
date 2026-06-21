# AI CEO: Strategic Intelligence Agent for BMW EV Strategy

## 1. Project Overview

This project is an AI-powered Strategic Intelligence Agent designed to support CEO-level decision-making for BMW's electric vehicle strategy.

The system collects public articles related to BMW, electric vehicles, competitors, battery technology, charging, market risks, and strategic opportunities. It stores the collected information in a structured database, builds a vector search index, retrieves relevant evidence, and generates evidence-based CEO recommendations.

The central business question is:

**If I were BMW's CEO today, what should I do next in EV strategy and why?**

---

## 2. Company and Scope

**Company:** BMW
**Industry:** Automotive / Electric Vehicles
**Focus Area:** EV strategy and competitive intelligence

The project focuses on:

* BMW EV strategy
* Neue Klasse platform
* iX3 and i3 electric vehicles
* Battery range and fast charging
* Premium EV competition
* China sales and profit pressure
* Competitors such as Tesla, Mercedes, Audi, BYD, Rivian, Lucid, and Toyota
* CEO-level strategic recommendations

---

## 3. Project Requirements Mapping

| Requirement                               | Implementation Status                             |
| ----------------------------------------- | ------------------------------------------------- |
| Collect at least 100 public documents     | Completed: 121 documents collected                |
| Use at least 3 independent public sources | Completed: BMWBlog, Electrek, CleanTechnica       |
| Store collected information               | Completed using SQLite                            |
| Clean and process text                    | Completed using custom preprocessing scripts      |
| Generate embeddings                       | Completed using all-MiniLM-L6-v2                  |
| Build searchable knowledge repository     | Completed using ChromaDB                          |
| Retrieve evidence using semantic search   | Completed using ChromaDB retriever                |
| Generate strategic recommendations        | Completed using safe AI CEO recommendation engine |
| Use free/open-source model                | Completed using Ollama + Qwen2.5:3B               |
| Build executive dashboard                 | Completed using Streamlit                         |
| Provide explainable evidence              | Completed using supporting evidence display       |

---

## 4. System Architecture

The system follows a modular AI pipeline:

```text
Public Sources
     ↓
Data Collection
     ↓
SQLite Knowledge Database
     ↓
Text Cleaning and Deduplication
     ↓
Document Chunking
     ↓
Embedding Generation
     ↓
ChromaDB Vector Store
     ↓
Semantic Retriever
     ↓
Safe Recommendation Engine
     ↓
Local LLM Rewriting
     ↓
Streamlit Executive Dashboard
```

---

## 5. Data Collection

The project collects articles from three public sources:

1. BMWBlog
2. Electrek
3. CleanTechnica

The final dataset contains:

* **121 collected documents**
* **3 unique publishers**
* **Full article content**
* **Average article length around 700 words**
* **Source type:** full_article_source

The data is collected automatically and stored in the SQLite database.

---

## 6. Database Design

The project uses SQLite as the structured storage layer.

Main database file:

```text
data/ai_ceo.db
```

Main tables:

* `documents`
* `chunks`
* `recommendations`

The `documents` table stores article-level information such as title, source, category, URL, content, and word count.

The `chunks` table stores smaller text chunks used for retrieval.

The `recommendations` table can be used to store generated CEO recommendations.

---

## 7. Text Processing Pipeline

The processing pipeline includes:

1. Text cleaning
2. Duplicate removal
3. Chunking
4. Embedding generation
5. Vector indexing

Chunking configuration:

```text
Chunk size: 500
Chunk overlap: 80
Total chunks created: 244
```

This allows the system to retrieve focused evidence instead of sending full articles directly to the language model.

---

## 8. Embeddings and Vector Store

The project uses:

```text
Embedding model: sentence-transformers/all-MiniLM-L6-v2
Vector database: ChromaDB
Collection name: bmw_ai_ceo_chunks
```

The vector store contains 244 embedded chunks.
When a user asks a question, the system converts the question into an embedding and retrieves the most semantically similar chunks.

---

## 9. Retrieval-Augmented Generation

The system uses Retrieval-Augmented Generation.

The process is:

```text
User question
     ↓
Question embedding
     ↓
ChromaDB similarity search
     ↓
Top evidence chunks
     ↓
Risk, opportunity, trend, and action extraction
     ↓
Grounded CEO briefing
```

The language model does not search the internet directly.
It only rewrites information supported by retrieved evidence.

---

## 10. Safe Recommendation Engine

A major challenge in LLM-based systems is hallucination.
To reduce hallucination, the project uses a safe recommendation design.

The system does not allow the LLM to freely invent strategy. Instead:

```text
Retriever finds evidence
     ↓
Python rule engine extracts supported risks, opportunities, trends, and actions
     ↓
LLM rewrites only supported points
     ↓
Unsafe output is checked
     ↓
Fallback rule-based briefing is used if needed
```

The system includes safeguards against unsupported claims such as:

* Fake partnerships
* Treating competitor vehicles as BMW models
* Unsupported future claims
* Weak podcast/comment evidence
* Unsupported strategic actions

This improves the reliability of the CEO recommendation.

---

## 11. Local LLM

The project uses:

```text
Runtime: Ollama
Model: Qwen2.5:3B
```

This satisfies the requirement of using a free/open-source model instead of paid commercial APIs.

The LLM is used as a writing assistant, not as the main decision maker.

---

## 12. Strategic Intelligence Engine

The strategic intelligence engine identifies:

### Risks

* China sales and profit pressure
* Premium EV competitive pressure
* ICE transition and regulatory pressure
* Pricing pressure in the EV segment

### Opportunities

* Neue Klasse product momentum
* iX3 and i3 positioning
* Battery range and fast charging differentiation
* Electric M performance positioning
* Premium electric SUV opportunity

### Trends

* EV adoption and electrification
* Range and fast charging as important EV factors
* Premium EV competition
* China and Europe as important strategic markets

---

## 13. Executive Dashboard

The dashboard is built using Streamlit.

Dashboard sections include:

1. Company Overview
2. Market Intelligence
3. Opportunity Monitor
4. Risk Monitor
5. Sentiment Analysis
6. Strategic Recommendations
7. CEO Briefing
8. Supporting Evidence

The dashboard shows:

* Collected document count
* Source summaries
* Category summaries
* Recent documents
* AI CEO query input
* Generated CEO recommendation
* Risks
* Opportunities
* Trends
* Recommended actions
* Supporting evidence
* Sentiment analysis tables and charts

---

## 14. Sentiment Analysis

The project uses VADER sentiment analysis as a lightweight sentiment baseline.

The sentiment module analyzes article tone and provides:

* Overall sentiment summary
* Sentiment by source
* Sentiment by category
* Document-level sentiment

Important limitation:

VADER is a lexical sentiment model. Business and EV articles often contain words such as "growth", "strong", "advanced", "range", and "fast charging", which may produce positive scores. Therefore, sentiment is interpreted as article tone, not final strategic risk.

---

## 15. Example CEO Question

Example question:

```text
What should BMW do next in EV strategy?
```

The system returns:

* Executive recommendation
* Why it matters
* Key risks
* Key opportunities
* Evidence-based action plan
* Confidence level
* Supporting evidence

---

## 16. How to Run the Project

### Step 1: Open project folder

```powershell
cd C:\Users\admin\OneDrive\Desktop\ai_ceo_agent
```

### Step 2: Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Check retriever

```powershell
python -m vector_store.retriever
```

### Step 4: Test recommendation engine

```powershell
python -m intelligence_engine.recommendation_engine
```

### Step 5: Test CEO agent

```powershell
python -m agents.ceo_agent
```

### Step 6: Run dashboard

```powershell
streamlit run app.py
```

---

## 17. Important Files

```text
data_collection/collect_final_three_sources.py
data_processing/clean_text.py
data_processing/deduplicate.py
data_processing/chunk_documents.py
storage/sqlite_store.py
vector_store/build_chroma.py
vector_store/retriever.py
intelligence_engine/recommendation_engine.py
intelligence_engine/sentiment_analyzer.py
agents/ceo_agent.py
llm/ollama_client.py
app.py
```

---

## 18. Limitations

The project has some limitations:

1. The collected data depends on public web article availability.
2. Some article extraction may include extra webpage text.
3. VADER sentiment is only a simple lexical baseline.
4. The local LLM may still over-write some points, so rule-based guardrails are used.
5. The system provides strategic decision support, not a final business decision.
6. The system is designed for academic demonstration and should not be treated as real financial advice.

---

## 19. Conclusion

This project demonstrates an end-to-end NLP and RAG-based Strategic Intelligence Agent for BMW's EV strategy.

It combines:

* Public data collection
* Text preprocessing
* SQLite storage
* Document chunking
* Embeddings
* ChromaDB semantic retrieval
* Local open-source LLM generation
* Hallucination-safe recommendation logic
* Sentiment analysis
* Streamlit executive dashboard

The final system supports CEO-level strategic decision-making by generating recommendations with retrieved supporting evidence.
