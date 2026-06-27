import time
import re
import sqlite3
from urllib.parse import quote_plus

import feedparser
import trafilatura

from storage.sqlite_store import create_tables, insert_document
from utils.config import DB_PATH


SOURCES = [
    {
        "source_name": "BMWBlog",
        "base_url": "https://www.bmwblog.com",
        "feed_urls": [
            "https://feeds.feedburner.com/BmwBlog"
        ],
        "queries": [
            "BMW electric vehicle",
            "BMW i3",
            "BMW iX3",
            "BMW Neue Klasse",
            "BMW electric M3",
            "BMW battery",
            "BMW charging",
            "BMW China sales",
            "BMW profit guidance",
            "BMW EV demand",
            "BMW hydrogen",
            "BMW hybrid electric"
        ],
        "target_max": 20
    },
    {
        "source_name": "Electrek",
        "base_url": "https://electrek.co",
        "feed_urls": [
            "https://electrek.co/feed/"
        ],
        "queries": [
            "BMW EV",
            "BMW iX3",
            "BMW i3",
            "BMW Neue Klasse",
            "Tesla Europe",
            "BYD Europe",
            "Mercedes EV",
            "Audi EV",
            "Volkswagen EV",
            "Europe EV sales",
            "EV price war",
            "EV charging",
            "EV battery",
            "solid state battery",
            "China EV market"
        ],
        "target_max": 90
    },
    {
        "source_name": "CleanTechnica",
        "base_url": "https://cleantechnica.com",
        "feed_urls": [
            "https://cleantechnica.com/feed/"
        ],
        "queries": [],
        "target_max": 20
    }
]


UNWANTED_TITLE_TERMS = [
    "e-bike",
    "ebike",
    "electric bicycle",
    "bicycle",
    "bike sale",
    "power station",
    "solar panel",
    "solar generation",
    "natural gas",
    "headphones",
    "fridge",
    "coupon",
    "discount",
    "deal",
    "art basel",
    "museum",
    "race car",
    "m drive tour",
    "old alpina",
    "offshore wind",
    "maritime",
    "agrivoltaics",
    "rv",
    "motorcycle"
]


RELEVANT_TERMS = [
    "bmw",
    "neue klasse",
    "ix3",
    "i3",
    "ix5",
    "electric",
    "electric vehicle",
    "electric car",
    "ev",
    "battery",
    "charging",
    "charger",
    "solid-state",
    "solid state",
    "lfp",
    "tesla",
    "byd",
    "mercedes",
    "audi",
    "volkswagen",
    "ford",
    "rivian",
    "lucid",
    "hyundai",
    "kia",
    "toyota",
    "porsche",
    "xiaomi",
    "xpeng",
    "china",
    "europe",
    "sales",
    "demand",
    "price",
    "profit",
    "guidance",
    "mandate",
    "regulation",
    "tariff",
    "range",
    "preorder",
    "orders",
    "lease",
    "market"
]


def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_search_feed_url(base_url, query):
    encoded_query = quote_plus(query)
    return f"{base_url}/?s={encoded_query}&feed=rss2"


def has_unwanted_title(title):
    title_lower = title.lower()

    for term in UNWANTED_TITLE_TERMS:
        if term in title_lower:
            return True

    return False


def is_relevant(title, summary):
    combined = f"{title} {summary}".lower()

    if has_unwanted_title(title):
        return False

    for term in RELEVANT_TERMS:
        if term in combined:
            return True

    return False


def get_existing_source_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT source, COUNT(*)
    FROM documents
    WHERE source_type = 'full_article_source'
    GROUP BY source
    """)

    rows = cursor.fetchall()
    conn.close()

    counts = {
        "BMWBlog": 0,
        "Electrek": 0,
        "CleanTechnica": 0
    }

    for source, count in rows:
        if source in counts:
            counts[source] = count

    return counts


def calculate_quality_score(title, content, source):
    title_text = title.lower()
    content_text = content[:3000].lower()
    text = title_text + " " + content_text

    # Hard rejection only from title.
    # Full article content can contain related links, ads, footer text, or recommendations.
    # So we do not reject based on unwanted words inside full content.
    for term in UNWANTED_TITLE_TERMS:
        if term in title_text:
            return -10

    score = 0

    # BMW-specific signals
    if "bmw" in text:
        score += 5

    if "neue klasse" in text:
        score += 5

    if "ix3" in text or "i3" in text or "ix5" in text:
        score += 4

    # EV strategy and technology signals
    if "electric vehicle" in text:
        score += 3

    if "electric car" in text:
        score += 3

    if " electric " in text:
        score += 2

    if " ev " in text:
        score += 2

    if "battery" in text:
        score += 3

    if "charging" in text or "charger" in text:
        score += 3

    if "solid-state" in text or "solid state" in text:
        score += 2

    if "lfp" in text:
        score += 2

    if "range" in text:
        score += 2

    # Competitor intelligence signals
    competitors = [
        "tesla",
        "byd",
        "mercedes",
        "audi",
        "volkswagen",
        "ford",
        "rivian",
        "lucid",
        "hyundai",
        "kia",
        "toyota",
        "porsche",
        "xiaomi",
        "xpeng",
        "stellantis"
    ]

    for competitor in competitors:
        if competitor in text:
            score += 2

    # Business / market / policy signals
    strategy_terms = [
        "china",
        "europe",
        "sales",
        "demand",
        "price",
        "profit",
        "guidance",
        "mandate",
        "regulation",
        "tariff",
        "market",
        "competition",
        "preorder",
        "orders",
        "lease",
        "cost",
        "affordable",
        "premium"
    ]

    for term in strategy_terms:
        if term in text:
            score += 1

    # BMWBlog articles should still be strategically useful.
    # But do not over-filter BMWBlog because it gives BMW-specific context.
    if source == "BMWBlog":
        if "bmw" in text:
            score += 2

    return score


def assign_category(title, content):
    text = f"{title} {content[:3000]}".lower()

    if "bmw" in text or "neue klasse" in text or "ix3" in text or "i3" in text or "ix5" in text:
        return "BMW EV Strategy"

    competitor_terms = [
        "tesla",
        "byd",
        "mercedes",
        "audi",
        "volkswagen",
        "ford",
        "rivian",
        "lucid",
        "hyundai",
        "kia",
        "toyota",
        "porsche",
        "xiaomi",
        "xpeng",
        "stellantis"
    ]

    if any(term in text for term in competitor_terms):
        return "Competitor Intelligence"

    if any(term in text for term in ["battery", "solid-state", "solid state", "lfp", "charging", "charger"]):
        return "Battery and Charging"

    if any(term in text for term in ["china", "europe", "regulation", "mandate", "tariff", "sales", "demand", "price"]):
        return "Market Risk and Policy"

    return "EV Market Intelligence"


def extract_full_article(url):
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return ""

        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=False
        )

        return clean_text(text)

    except Exception as e:
        print(f"Extraction failed: {url} | {e}")
        return ""


def collect_from_feed_url(
    source_name,
    feed_url,
    target_max,
    inserted_by_source,
    seen_urls,
    sleep_seconds
):
    feed = feedparser.parse(feed_url)
    entries = feed.entries

    print(f"Feed URL: {feed_url}")
    print(f"Entries found: {len(entries)}")

    inserted_count = 0

    for entry in entries:
        if inserted_by_source[source_name] >= target_max:
            break

        title = entry.get("title", "No title")
        url = entry.get("link", "")
        published_date = entry.get("published", "")
        summary = entry.get("summary", "")

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        if not is_relevant(title, summary):
            continue

        print("\nTrying article:")
        print(title[:120])
        print(url)

        content = extract_full_article(url)

        if not content:
            print("Skipped: full article text could not be extracted.")
            continue

        quality_score = calculate_quality_score(title, content, source_name)

        if quality_score < 3:
            print(f"Skipped: low quality score = {quality_score}")
            continue

        category = assign_category(title, content)

        inserted = insert_document(
            title=title,
            source=source_name,
            source_type="full_article_source",
            url=url,
            published_date=published_date,
            company="BMW/Rivals",
            category=category,
            content=content
        )

        if inserted:
            inserted_by_source[source_name] += 1
            inserted_count += 1
            print(f"Inserted full article. Quality score: {quality_score}")
        else:
            print("Duplicate skipped.")

        time.sleep(sleep_seconds)

    return inserted_count


def collect_final_dataset(sleep_seconds=1.0):
    create_tables()

    seen_urls = set()

    inserted_by_source = get_existing_source_counts()

    print("\nExisting full article counts:")
    for source_name, count in inserted_by_source.items():
        print(f"{source_name}: {count}")

    for source in SOURCES:
        source_name = source["source_name"]
        base_url = source["base_url"]
        target_max = source["target_max"]

        print("\n" + "=" * 100)
        print(f"Collecting source: {source_name}")
        print(f"Target max: {target_max}")
        print(f"Current count: {inserted_by_source[source_name]}")

        if inserted_by_source[source_name] >= target_max:
            print(f"{source_name} already reached target. Skipping.")
            continue

        # 1. Direct RSS feed
        for feed_url in source["feed_urls"]:
            if inserted_by_source[source_name] >= target_max:
                break

            collect_from_feed_url(
                source_name=source_name,
                feed_url=feed_url,
                target_max=target_max,
                inserted_by_source=inserted_by_source,
                seen_urls=seen_urls,
                sleep_seconds=sleep_seconds
            )

        # 2. Search RSS feeds
        for query in source["queries"]:
            if inserted_by_source[source_name] >= target_max:
                break

            search_feed_url = build_search_feed_url(base_url, query)

            print("\n" + "-" * 100)
            print(f"Search query: {query}")

            collect_from_feed_url(
                source_name=source_name,
                feed_url=search_feed_url,
                target_max=target_max,
                inserted_by_source=inserted_by_source,
                seen_urls=seen_urls,
                sleep_seconds=sleep_seconds
            )

    print("\n" + "=" * 100)
    print("Final Three-Source Collection Summary")
    print("-------------------------------------")

    total_inserted = 0

    for source_name, count in inserted_by_source.items():
        print(f"{source_name}: {count}")
        total_inserted += count

    print(f"Total full articles in database from selected sources: {total_inserted}")

    if total_inserted >= 100:
        print("Status: SUCCESS - dataset has 100+ full articles.")
    else:
        print("Status: WARNING - dataset has fewer than 100 full articles.")


if __name__ == "__main__":
    collect_final_dataset(sleep_seconds=1.0)