"""
Audit command implementation for MailPrune.
"""

import logging
import time
from typing import Optional

import pandas as pd

from mailprune.utils.audit import (
    aggregate_and_score,
    fetch_message_ids,
    fetch_uncached_messages,
    process_messages,
    prune_cache,
    save_report,
    setup_audit,
)
from mailprune.utils.helpers import save_email_cache

logger = logging.getLogger(__name__)


def perform_audit(max_emails: int = 2000) -> Optional[pd.DataFrame]:
    """Perform Phase 1 Email Audit.

    The steps are as follows:

    1. Fetch the last N emails from Gmail API.
    2. Cache email metadata locally to avoid redundant API calls.
    3. Process emails to extract sender, date, labels.
    4. Prune cached emails that are no longer present (i.e., were deleted).
    5. Aggregate by sender to compute total volume, open rate, average recency.
    6. Calculate an "ignorance score" to identify potential noise makers.
    7. Save the audit report to data/noise_report.csv.
    """
    start_time: float = time.time()

    try:
        # Setup
        service_pool, email_cache = setup_audit()

        logger.info(f"Starting audit of the last {max_emails} emails...")

        # Fetch message IDs
        messages = fetch_message_ids(service_pool, max_emails)
        fetch_time: float = time.time()
        logger.info(f"Fetched {len(messages)} message IDs in {fetch_time - start_time:.2f}s")

        # Identify messages to fetch
        current_email_ids = {m["id"] for m in messages}
        messages_to_fetch = [m for m in messages if m["id"] not in email_cache]

        # Fetch uncached messages
        fetched_count = fetch_uncached_messages(service_pool, email_cache, messages_to_fetch)

        logger.info(f"Processed cache: {len(messages) - len(messages_to_fetch)} cached, {fetched_count} fetched")

        # Process messages
        data = process_messages(email_cache, messages)
        process_time: float = time.time()
        logger.info(
            f"Processed {len(data)} emails ({fetched_count} fetched from API, {len(data) - fetched_count} from cache) in {process_time - fetch_time:.2f}s"
        )

        # Prune cache
        prune_cache(email_cache, current_email_ids)

        # Save updated cache
        save_email_cache(email_cache)

        # Process with Pandas
        df: pd.DataFrame = pd.DataFrame(data)

        # Aggregate and score
        audit_summary = aggregate_and_score(df)
        agg_time: float = time.time()
        logger.info(f"Aggregated data for {len(audit_summary)} senders in {agg_time - process_time:.2f}s")

        # Save report
        save_report(audit_summary)
        save_time: float = time.time()
        logger.info(f"Audit complete! Total time: {save_time - start_time:.2f}s")

        return audit_summary

    except FileNotFoundError:
        return None
