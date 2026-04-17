"""
MCP Server for Mailprune

Exposes Mailprune's email analysis tools via the Model Context Protocol.
"""

import logging
import os

import anyio
from mcp.server.fastmcp import FastMCP

from mailprune.commands import (
    analyze_clusters,
    analyze_engagement,
    analyze_patterns,
    generate_report,
    perform_audit,
)
from mailprune.constants import (
    DEFAULT_CACHE_PATH,
    DEFAULT_CSV_PATH,
    DEFAULT_MAX_EMAILS,
)
from mailprune.utils import load_audit_data

# Set up logging for MCP
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Mailprune")


@mcp.resource("mailprune://guidance/cleanup-strategy")
def get_cleanup_strategy() -> str:
    """Provides the logic for how to handle different sender clusters."""
    return """# Mailprune Cleanup Strategy Guidance

Use this guidance to interpret the results from the `cluster` and `patterns` tools.

## Cluster Interpretation
- **Cluster 4 (Silent Noise)**: Senders with low volume but near-zero open rates. 
  - **Action**: High-confidence "Unsubscribe" candidates.
- **Cluster 2 (Mega Noise)**: High-volume newsletters. 
  - **Action**: Compare `patterns` intent. If "promotional", suggest Unsubscribe. If "informational", suggest a weekly digest.
- **Cluster 3/1 (Mid-Tier)**: Transactional or Utility alerts.
  - **Action**: Suggest "Gmail Filters" to skip the inbox rather than unsubscribing.

## Intent Guidance
- **Promotional**: Sales, offers, marketing. Suggest Unsubscribe if engagement < 50%.
- **Transactional**: Receipts, orders, security. Suggest Filtering/Labeling.
- **Social/Informational**: Newsletters, updates. Suggest review based on volume.
"""


@mcp.resource("mailprune://guidance/noise-metrics")
def get_noise_metrics() -> str:
    """Explains how the 'Ignorance Score' is calculated."""
    return """# Mailprune Noise Metrics (Ignorance Score)

The 'Ignorance Score' is the primary metric used to rank senders in Mailprune.

## Formula
`Ignorance Score = total_volume * (100 - open_rate)`

## Why this metric?
- **High Volume, High Open Rate**: Low score (e.g. 100 emails, 100% open = 0 score). These are emails you value.
- **High Volume, Zero Open Rate**: Maximum score (e.g. 100 emails, 0% open = 10,000 score). These are your worst noise makers.
- **Low Volume, Zero Open Rate**: Low score (e.g. 1 email, 0% open = 100 score). These are minor annoyances.
"""


@mcp.tool()
async def audit(max_emails: int = DEFAULT_MAX_EMAILS, query: str = "-label:trash", refresh: bool = False) -> str:
    """Run an email audit to identify noise makers in your Gmail inbox.

    This is the STARTING POINT for any analysis. It performs network I/O to fetch
    metadata from Gmail and calculates the initial 'Ignorance Scores' for all senders.

    Args:
        max_emails: Maximum number of emails to audit (default is 2000).
        query: Gmail search query to filter emails (default is '-label:trash').
        refresh: Force refresh of email cache by re-fetching all emails from Gmail.
    """
    logger.info(f"MCP Tool: audit(max_emails={max_emails}, query='{query}', refresh={refresh})")

    # Offload the blocking Gmail API and processing work to a thread
    result = await anyio.to_thread.run_sync(perform_audit, max_emails, query, str(DEFAULT_CACHE_PATH), refresh)

    if result is None:
        return "❌ Failed to perform audit. Please ensure your Gmail credentials are configured correctly and you have run 'mailprune auth' manually."

    # Format a concise summary for the LLM
    top_10 = result.head(10)[["from", "total_volume", "open_rate", "avg_recency_days", "ignorance_score"]]
    summary = top_10.to_string(index=False)

    logger.info(f"Audit completed successfully for {len(result)} senders.")
    return (
        f"✅ Audit complete! Analyzed {len(result)} senders.\n\n"
        f"Top 10 Noise Makers (ranked by Ignorance Score):\n"
        f"-----------------------------------------------\n"
        f"{summary}\n\n"
        f"Tip: Reference 'mailprune://guidance/noise-metrics' for more info on the scores."
    )


@mcp.tool()
async def report(brief: bool = False) -> str:
    """Generate a comprehensive email audit and cleanup report based on the last audit.

    Provides actionable insights, engagement tiers, and specific cleanup recommendations
    (Unsubscribe vs Filter) based on the data from the last 'audit' call.

    Args:
        brief: If True, returns a shorter summary report.
    """
    logger.info(f"MCP Tool: report(brief={brief})")
    return await anyio.to_thread.run_sync(generate_report, str(DEFAULT_CSV_PATH), brief)


@mcp.tool()
async def patterns(top_n: int = 5, by: str = "volume", use_nlp: bool = True) -> str:
    """Analyze content patterns and inferred intent for top senders using email snippets.

    HEAVY TOOL: Performs NLP processing (entity extraction, intent inference) on
    email snippets. Use this to find the 'Why' behind high noise scores.

    Args:
        top_n: Number of top senders to analyze (default is 5).
        by: Metric to rank senders by ('volume' or 'ignorance').
        use_nlp: Whether to use NLP for enhanced keyword and entity extraction.
    """
    logger.info(f"MCP Tool: patterns(top_n={top_n}, by='{by}', use_nlp={use_nlp})")

    df = await anyio.to_thread.run_sync(load_audit_data, str(DEFAULT_CSV_PATH))
    if df.empty:
        return "⚠️ No audit data found. Please run the 'audit' tool first."

    audit_data = df.to_dict("records")
    return await anyio.to_thread.run_sync(analyze_patterns, str(DEFAULT_CACHE_PATH), audit_data, top_n, by, use_nlp)


@mcp.tool()
async def engagement(tier: str = "all") -> str:
    """Analyze sender engagement patterns and categorize them into tiers.

    Breaks down your inbox into High, Medium, Low, and Zero engagement groups.
    Useful for seeing the 'Long Tail' of senders you might have missed.

    Args:
        tier: Engagement tier to analyze ('high', 'medium', 'low', 'zero', or 'all').
    """
    logger.info(f"MCP Tool: engagement(tier='{tier}')")
    return await anyio.to_thread.run_sync(analyze_engagement, str(DEFAULT_CSV_PATH), tier)


@mcp.tool()
async def cluster(n_clusters: int = 5) -> str:
    """Group senders into behavioral clusters using unsupervised learning (K-Means).

    Identifies 'Peer Groups' of senders (e.g. Cluster 4: Silent Newsletters).
    Reference 'mailprune://guidance/cleanup-strategy' to interpret these clusters.

    Args:
        n_clusters: Number of clusters to create (default is 5).
    """
    logger.info(f"MCP Tool: cluster(n_clusters={n_clusters})")
    return await anyio.to_thread.run_sync(analyze_clusters, str(DEFAULT_CSV_PATH), n_clusters)


def main():
    """Entry point for the MCP server."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    mcp.run()


if __name__ == "__main__":
    main()
