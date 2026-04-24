"""
Optimized JSON Data Store for Breaking News Finder
Handles saving/loading of news data and analysis results with
append-mode support and file rotation.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

from config import DATA_DIR, JSON_STORE_FILE, ANALYSIS_STORE_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_articles(articles: List[Dict], filepath: str = JSON_STORE_FILE) -> str:
    """
    Save articles to JSON file with metadata.
    Overwrites previous data (each run is a fresh snapshot).
    Deduplicates by URL before saving as a final safety net.
    """
    ensure_data_dir()

    # Final safety-net deduplication by URL
    seen: set = set()
    unique_articles: List[Dict] = []
    for article in articles:
        url = article.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique_articles.append(article)
    if len(unique_articles) < len(articles):
        logger.info(
            f"save_articles: removed {len(articles) - len(unique_articles)} duplicate URLs "
            f"before saving ({len(unique_articles)} unique)."
        )

    data = {
        "metadata": {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "total_articles": len(unique_articles),
            "sources": list(set(a.get("source", "Unknown") for a in unique_articles)),
        },
        "articles": unique_articles,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(filepath)
    logger.info(f"Saved {len(unique_articles)} articles to {filepath} ({file_size / 1024:.1f} KB)")
    return filepath


def load_articles(filepath: str = JSON_STORE_FILE) -> List[Dict]:
    """Load articles from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Data file not found: {filepath}")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles = data.get("articles", [])
        logger.info(f"Loaded {len(articles)} articles from {filepath}")
        return articles
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error loading data: {e}")
        return []


def save_analysis(results: Dict, filepath: str = ANALYSIS_STORE_FILE) -> str:
    """Save analysis results to JSON."""
    ensure_data_dir()

    data = {
        "metadata": {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        },
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Analysis saved to {filepath}")
    return filepath


def load_analysis(filepath: str = ANALYSIS_STORE_FILE) -> Optional[Dict]:
    """Load analysis results from JSON."""
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("results", {})
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error loading analysis: {e}")
        return None


def get_data_freshness() -> Optional[str]:
    """Check when data was last fetched."""
    if not os.path.exists(JSON_STORE_FILE):
        return None

    try:
        with open(JSON_STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("metadata", {}).get("fetched_at")
    except Exception:
        return None
