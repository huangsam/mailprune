"""
Email analysis utilities for mailprune.
Provides functions to analyze email audit data and generate insights.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ..constants import DEFAULT_CSV_PATH, ENGAGEMENT_HIGH_THRESHOLD, ENGAGEMENT_LOW_THRESHOLD, ENGAGEMENT_MEDIUM_THRESHOLD
from ..utils.audit import get_sender_snippets_from_cache, get_sender_subjects_from_cache
from ..utils.helpers import load_email_cache

logger = logging.getLogger(__name__)

_SPACY_MODEL = None


def get_spacy_model():
    """Load and cache the spaCy model."""
    global _SPACY_MODEL
    if _SPACY_MODEL is not None:
        return _SPACY_MODEL

    import spacy

    try:
        _SPACY_MODEL = spacy.load("en_core_web_sm")
    except OSError:
        logger.info("spaCy model 'en_core_web_sm' not found. Attempting to download...")
        try:
            spacy.cli.download("en_core_web_sm")
            _SPACY_MODEL = spacy.load("en_core_web_sm")
            logger.info("Successfully downloaded and loaded spaCy model.")
        except Exception as e:
            logger.warning(f"Failed to download spaCy model: {e}")
            return None
    return _SPACY_MODEL


def load_audit_data(csv_path: str = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """Load the email audit data from CSV."""
    try:
        return pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: {csv_path} not found. Run audit first.")
        return pd.DataFrame()


def get_top_noise_makers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Get the top N noise makers by ignorance score."""
    return df.nlargest(n, "ignorance_score")


def get_engagement_tiers(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Get engagement tier dataframes."""
    return {
        "high": df[df["open_rate"] >= ENGAGEMENT_HIGH_THRESHOLD],
        "medium": df[(df["open_rate"] >= ENGAGEMENT_MEDIUM_THRESHOLD) & (df["open_rate"] < ENGAGEMENT_HIGH_THRESHOLD)],
        "low": df[(df["open_rate"] >= ENGAGEMENT_LOW_THRESHOLD) & (df["open_rate"] < ENGAGEMENT_MEDIUM_THRESHOLD)],
        "zero": df[df["open_rate"] == 0],
    }


def get_top_senders_by_volume(sender_subjects: Dict[str, List[str]], top_n: int) -> List[Tuple[str, int]]:
    """Get top senders ranked by email volume.

    Args:
        sender_subjects: Dictionary mapping sender emails to lists of their subjects
        top_n: Number of top senders to return

    Returns:
        List of (sender, email_count) tuples, sorted by volume descending
    """
    return [(sender, len(subjects)) for sender, subjects in sorted(sender_subjects.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]]


def calculate_overall_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate overall email metrics from audit data.

    Computes key statistics including total emails, unread percentage,
    average open rate, and ignorance score metrics.

    Args:
        df: DataFrame containing audit data with columns:
            - total_volume: Total emails per sender
            - unread_count: Unread emails per sender
            - open_rate: Open rate percentage per sender
            - ignorance_score: Calculated ignorance score per sender

    Returns:
        Dictionary containing:
            - total_emails: Sum of all email volumes
            - unread_percentage: Percentage of unread emails
            - average_open_rate: Mean open rate across all senders
            - senders_never_opened: Count of senders with 0% open rate
            - top_ignorance_score: Highest ignorance score
    """
    total_emails = df.total_volume.sum()
    unread_pct = df.unread_count.sum() / total_emails * 100
    avg_open_rate = df.open_rate.mean()
    never_opened = len(df[df.open_rate == 0])
    top_score = df.ignorance_score.max()

    return {
        "total_emails": total_emails,
        "unread_percentage": unread_pct,
        "average_open_rate": avg_open_rate,
        "senders_never_opened": never_opened,
        "top_ignorance_score": top_score,
    }


def analyze_sender_patterns(df: pd.DataFrame, sender_name: str) -> Optional[Dict]:
    """Analyze a specific sender's email patterns."""
    sender_data = df[df["from"].str.contains(sender_name, case=False, na=False)]
    if sender_data.empty:
        return None

    row = sender_data.iloc[0]
    return {
        "sender": row["from"],
        "total_emails": int(row["total_volume"]),
        "open_rate": row["open_rate"],
        "ignorance_score": row["ignorance_score"],
        "unread_count": int(row["unread_count"]),
    }


def compare_metrics(before_metrics: Dict, after_metrics: Dict) -> Dict:
    """Compare email metrics before and after cleanup actions.

    Calculates improvements in key metrics to quantify the effectiveness
    of email management actions.

    Args:
        before_metrics: Metrics dictionary from before cleanup
        after_metrics: Metrics dictionary from after cleanup

    Returns:
        Dictionary with improvement metrics:
            - unread_improvement: Reduction in unread percentage
            - top_score_reduction: Absolute reduction in top ignorance score
            - top_score_reduction_pct: Percentage reduction in top score
            - open_rate_improvement: Increase in average open rate
    """
    return {
        "unread_improvement": before_metrics["unread_percentage"] - after_metrics["unread_percentage"],
        "top_score_reduction": before_metrics["top_ignorance_score"] - after_metrics["top_ignorance_score"],
        "top_score_reduction_pct": (before_metrics["top_ignorance_score"] - after_metrics["top_ignorance_score"]) / before_metrics["top_ignorance_score"] * 100,
        "open_rate_improvement": after_metrics["average_open_rate"] - before_metrics["average_open_rate"],
    }


def generate_cleanup_report(df: pd.DataFrame, baseline_metrics: Optional[Dict] = None) -> str:
    """Generate a comprehensive cleanup report."""
    current_metrics = calculate_overall_metrics(df)

    report = []
    report.append("=== 📧 EMAIL AUDIT REPORT ===")
    report.append("")
    report.append(f"📊 Current Status: {len(df)} senders, {int(current_metrics['total_emails'])} emails")
    report.append(f"📈 Unread Rate: {current_metrics['unread_percentage']:.1f}%")
    report.append(f"🎯 Average Open Rate: {current_metrics['average_open_rate']:.1f}%")
    report.append(f"🚫 Senders Never Opened: {int(current_metrics['senders_never_opened'])}")
    report.append(f"🥇 Top Ignorance Score: {current_metrics['top_ignorance_score']:.0f}")
    report.append("")

    if baseline_metrics:
        comparison = compare_metrics(baseline_metrics, current_metrics)
        report.append("=== 📈 IMPROVEMENT METRICS ===")
        report.append(f"📉 Unread Rate Improvement: {comparison['unread_improvement']:.1f}%")
        report.append(f"🎯 Top Score Reduction: {comparison['top_score_reduction']:.0f} ({comparison['top_score_reduction_pct']:.0f}%)")
        report.append(f"📈 Open Rate Improvement: {comparison['open_rate_improvement']:.1f}%")
        report.append("")

    report.append("=== 🏆 TOP 10 NOISE MAKERS ===")
    top10 = get_top_noise_makers(df, 10)
    for i, (_, row) in enumerate(top10.iterrows(), 1):
        report.append(f"{i:2d}. {row['from']:<50} | Vol: {int(row['total_volume']):3d} | Open: {row['open_rate']:5.1f}% | Score: {row['ignorance_score']:6.0f}")
    report.append("")

    report.append("=== 🎯 CLEANUP RECOMMENDATIONS ===")
    never_opened = df[df.open_rate == 0].nlargest(5, "total_volume")
    if not never_opened.empty:
        report.append("🗑️  Consider unsubscribing from these (0% open rate):")
        for _, row in never_opened.iterrows():
            report.append(f"   • {row['from']} ({int(row['total_volume'])} emails)")
        report.append("")

    high_volume = df[df.total_volume >= 20].nlargest(5, "ignorance_score")
    if not high_volume.empty:
        report.append("🎛️  Review these high-volume senders:")
        for _, row in high_volume.iterrows():
            report.append(f"   • {row['from']} ({int(row['total_volume'])} emails, {row['open_rate']:.1f}% open)")
        report.append("")

    return "\n".join(report)


def analyze_sender_email_patterns(sender_emails: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Analyze email subject patterns for a sender (valuable vs promotional)."""
    valuable_keywords = [
        "credit score",
        "score changed",
        "score update",
        "fico",
        "spending category",
        "top spending",
        "transaction",
        "deposit",
        "pending transaction",
        "balance",
        "account",
        "cash back",
        "rewards",
        "savings account",
        "alert",
        "security",
        "login",
        "password",
        "bill",
        "payment",
    ]

    promotional_keywords = [
        "loan",
        "mortgage",
        "insurance",
        "car insurance",
        "advisor",
        "financial advisor",
        "credit card",
        "intro apr",
        "interest rate",
        "approved fast",
        "heloc",
        "refinance",
        "high-yield",
        "comparison",
        "rate",
        "offer",
        "deal",
        "apply",
        "application",
        "survey",
        "feedback",
        "review",
        "newsletter",
        "tips",
        "guide",
    ]

    valuable_emails = []
    promotional_emails = []
    uncategorized = []

    for subject in sender_emails:
        subject_lower = subject.lower()

        if any(keyword in subject_lower for keyword in valuable_keywords):
            valuable_emails.append(subject)
        elif any(keyword in subject_lower for keyword in promotional_keywords):
            promotional_emails.append(subject)
        else:
            uncategorized.append(subject)

    return valuable_emails, promotional_emails, uncategorized


def filter_common_words(words: List[str]) -> List[str]:
    """Filter out common English words and short words from subject analysis.

    Removes common prepositions, articles, and conjunctions that don't provide
    meaningful insight into email patterns. Also filters out words shorter
    than 4 characters to focus on more significant terms.

    Args:
        words: List of words extracted from email subjects

    Returns:
        Filtered list of words suitable for pattern analysis
    """
    common_words = {
        "with",
        "from",
        "your",
        "this",
        "that",
        "have",
        "been",
        "will",
        "they",
        "their",
        "there",
        "here",
        "when",
        "where",
        "what",
        "which",
        "then",
        "than",
        "into",
        "onto",
        "over",
        "under",
        "after",
        "before",
        "while",
        "since",
        "until",
        "through",
        "during",
        "between",
        "among",
        "within",
    }
    return [word.lower() for word in words if len(word) > 3 and word.lower() not in common_words]


def cluster_senders_unsupervised(df: pd.DataFrame, n_clusters: int = 5) -> Dict[str, int]:
    """
    Perform unsupervised clustering on senders using K-Means.
    Features: total_volume, unread_count, open_rate, ignorance_score.
    Returns a dictionary mapping sender to cluster ID.
    """
    if df.empty or len(df) < n_clusters:
        return {}

    # Select features for clustering
    features = df[["total_volume", "unread_count", "open_rate", "ignorance_score"]].copy()

    # Handle any NaN values
    features = features.fillna(0)

    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)

    # Map senders to clusters
    result = {}
    for i, row in df.iterrows():
        result[row["from"]] = int(clusters[i])

    return result


def preprocess_text(text: str) -> str:
    """Clean and normalize text for analysis."""
    import re

    # Convert to lowercase
    text = text.lower()
    # Remove special characters and extra whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords_nlp(text: str, use_nlp: bool = True) -> List[str]:
    """Extract meaningful keywords using simple text processing."""
    if not text:
        return []

    # Simple regex-based keyword extraction
    logger.debug("Using simple regex keyword extraction.")
    words = preprocess_text(text).split()
    # Filter out common words and short words
    common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "an", "a"}
    return [word for word in words if len(word) > 2 and word not in common_words]


def extract_entities_nlp(text: str, use_nlp: bool = True) -> Dict[str, List[str]]:
    """
    Extract named entities (ORG, PERSON, GPE, MONEY, DATE, etc.) from text using spaCy.
    Returns a dictionary of entity types and their values.
    """
    if not text or not use_nlp:
        return {}

    entities: Dict[str, List[str]] = {}

    try:
        nlp = get_spacy_model()
        if nlp:
            doc = nlp(text)
            # Filter for interesting entity types
            target_labels = ["ORG", "PERSON", "GPE", "MONEY", "DATE", "PRODUCT", "EVENT"]

            for ent in doc.ents:
                if ent.label_ in target_labels:
                    if ent.label_ not in entities:
                        entities[ent.label_] = []
                    # Avoid duplicates
                    if ent.text not in entities[ent.label_]:
                        entities[ent.label_].append(ent.text)
    except Exception as e:
        logger.debug(f"Entity extraction failed: {e}")

    return entities


def infer_intent_nlp(text: str, use_nlp: bool = True, top_n: int = 1) -> Union[str, List[Tuple[str, int]]]:
    """
    Infer email intent using NLP analysis of content.
    Classifies emails into categories: promotional, transactional, informational, social, or unknown.

    Args:
        text: The text content to analyze
        use_nlp: Whether to use NLP processing
        top_n: Number of top intents to return (1 returns just the top intent as string, >1 returns list of tuples)

    Returns:
        If top_n == 1: Single intent string
        If top_n > 1: List of (intent, score) tuples sorted by score descending
    """
    if not text or not use_nlp:
        return "unknown" if top_n == 1 else [("unknown", 0)]

    try:
        nlp = get_spacy_model()
        if not nlp:
            return "unknown" if top_n == 1 else [("unknown", 0)]

        doc = nlp(text.lower())

        # Define intent keywords and patterns
        intent_patterns = {
            "promotional": [
                "buy",
                "sale",
                "discount",
                "offer",
                "deal",
                "save",
                "free",
                "limited",
                "exclusive",
                "subscribe",
                "newsletter",
                "marketing",
                "advertisement",
                "promotion",
                "coupon",
            ],
            "transactional": [
                "receipt",
                "invoice",
                "payment",
                "order",
                "confirmation",
                "shipping",
                "delivered",
                "purchase",
                "billing",
                "account",
                "transaction",
                "charged",
                "refund",
            ],
            "informational": [
                "update",
                "news",
                "alert",
                "notification",
                "report",
                "summary",
                "status",
                "announcement",
                "reminder",
                "schedule",
                "meeting",
                "event",
            ],
            "social": ["friend", "connect", "follow", "like", "share", "comment", "post", "message", "invite", "group", "community", "network"],
        }

        # Count matches for each intent
        intent_scores = dict.fromkeys(intent_patterns, 0)

        for token in doc:
            lemma = token.lemma_
            for intent, keywords in intent_patterns.items():
                if lemma in keywords:
                    intent_scores[intent] += 1

        # Also check for entity-based clues
        entities = extract_entities_nlp(text, use_nlp)
        if "MONEY" in entities:
            intent_scores["transactional"] += 2
        if "ORG" in entities and any("newsletter" in ent.lower() for ent in entities["ORG"]):
            intent_scores["promotional"] += 2

        # Return the intent(s) with the highest score(s), or "unknown" if no clear intent
        max_score = max(intent_scores.values())
        if max_score > 0:
            # Sort intents by score descending
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
            top_intents = sorted_intents[:top_n]
            if top_n == 1:
                return top_intents[0][0]  # Backward compatibility: return single string
            return top_intents  # Return list of (intent, score) tuples
        else:
            return "unknown" if top_n == 1 else [("unknown", 0)]

    except Exception as e:
        logger.debug(f"Intent inference failed: {e}")
        return "unknown" if top_n == 1 else [("unknown", 0)]


def analyze_title_patterns_core(
    cache_path: str,
    audit_data: List[Dict],
    top_n: int = 5,
    by: str = "volume",
    use_nlp: bool = True,
) -> Dict:
    """Core content pattern analysis using email snippets for richer NLP analysis."""
    from collections import Counter

    results = {}

    # Load email cache and get sender snippets
    try:
        cache = load_email_cache(cache_path)
        sender_snippets = get_sender_snippets_from_cache(cache)
        sender_subjects = get_sender_subjects_from_cache(cache)
    except Exception:
        sender_snippets = {}
        sender_subjects = {}

    # Sort by specified metric and get top senders
    if by == "ignorance":
        sorted_senders = sorted(audit_data, key=lambda x: x.get("ignorance_score", 0), reverse=True)
    else:  # volume
        sorted_senders = sorted(audit_data, key=lambda x: x.get("volume", 0), reverse=True)
    top_senders = sorted_senders[:top_n]

    for sender_data in top_senders:
        sender = sender_data.get("from", "Unknown")  # CSV uses 'from' column
        snippets = sender_snippets.get(sender, [])

        if not snippets:
            continue

        # Extract keywords and entities from all email snippets
        all_keywords = []
        all_entities: Dict[str, List[str]] = {}

        for snippet in snippets:
            # Keywords
            keywords = extract_keywords_nlp(snippet, use_nlp)
            all_keywords.extend(keywords)

            # Entities
            if use_nlp:
                ents = extract_entities_nlp(snippet, use_nlp)
                for label, values in ents.items():
                    if label not in all_entities:
                        all_entities[label] = []
                    all_entities[label].extend(values)

        # Count keyword frequencies across all content
        keyword_counts = Counter(all_keywords)

        # Get top keywords from content analysis
        top_keywords = keyword_counts.most_common(10)

        # Process entities (count frequencies per type)
        top_entities = {}
        for label, values in all_entities.items():
            entity_counts = Counter(values)
            top_entities[label] = entity_counts.most_common(5)

        # Infer intent if requested
        top_intents = [("unknown", 0)]
        combined_content = " ".join(snippets)
        intent_result = infer_intent_nlp(combined_content, use_nlp, top_n=3)
        if isinstance(intent_result, list):
            top_intents = intent_result
        else:
            # Backward compatibility: single string result
            top_intents = [(intent_result, 1)]

        # Get a sample subject for display (from audit data or cache)
        sample_subject = sender_data.get("sample_subject", "")
        if not sample_subject:
            subjects = sender_subjects.get(sender, [])
            if subjects:
                sample_subject = subjects[0]

        results[sender] = {
            "sample_subject": sample_subject,
            "email_count": len(snippets),
            "top_keywords": top_keywords,
            "top_entities": top_entities,
            "nlp_used": use_nlp,
            "top_intents": top_intents,
        }

    return results
