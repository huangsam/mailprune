"""
Content patterns command with NLP processing for Mailprune.
Analyzes email content snippets for comprehensive pattern recognition.
"""

from mailprune.utils.analysis import analyze_title_patterns_core


def analyze_patterns(cache_path: str, audit_data: list[dict], top_n: int = 5, by: str = "volume", use_nlp: bool = True) -> str:
    """Analyze content patterns for top senders using email snippets.

    This function performs comprehensive content analysis on email data to identify
    patterns and characteristics of top senders. It leverages NLP processing to extract
    meaningful keywords and named entities from email content snippets.

    The analysis process includes:

    1. Load cached email data from the specified cache path.
    2. Group emails by sender and sort by the specified metric (volume or ignorance score).
    3. For each top sender, analyze combined email snippets for keywords and entities.
    4. Display formatted results showing sender details, content patterns, and insights.

    Note: Requires existing email cache and audit data. NLP processing provides richer
    insights but requires spaCy model to be available.
    """
    results = analyze_title_patterns_core(cache_path, audit_data, top_n, by, use_nlp)

    output = []
    # Display results
    output.append(f"\nContent Pattern Analysis (Top {top_n} Senders by {by})")
    output.append("=" * 60)

    for sender, data in results.items():
        output.append(f"\nSender: {sender}")
        output.append(f"Sample Subject: {data['sample_subject']}")
        output.append(f"Emails Analyzed: {data['email_count']}")
        output.append(f"NLP Processing: {'Enabled' if data['nlp_used'] else 'Disabled'}")
        # Display top intents
        top_intents = data.get("top_intents", [("unknown", 0)])
        if top_intents and len(top_intents) > 0:
            intent_strs = [f"{intent} ({score})" for intent, score in top_intents if score > 0]
            if intent_strs:
                output.append(f"Top Intents: {', '.join(intent_strs)}")
            else:
                output.append("Top Intents: unknown")

        output.append("Top Keywords from Email Content:")
        keyword_strs = [f"{keyword} ({count})" for keyword, count in data["top_keywords"]]
        output.append(f"  {', '.join(keyword_strs)}")

        # Display entities if available
        if "top_entities" in data and data["top_entities"]:
            output.append("Extracted Entities:")
            for label, entities in data["top_entities"].items():
                if entities:
                    entity_strs = [f"{entity} ({count})" for entity, count in entities]
                    output.append(f"  {label}: {', '.join(entity_strs)}")

    return "\n".join(output)
