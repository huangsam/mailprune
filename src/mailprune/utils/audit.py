import logging
import os
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .constants import GmailLabels
from .helpers import load_email_cache, save_email_cache

logger = logging.getLogger(__name__)

# Same scopes as the sanity check
SCOPES: List[str] = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailServicePool:
    """Thread-safe pool of Gmail API service instances."""

    def __init__(self, token_path: str, pool_size: int = 5):
        self.pool: queue.Queue[Any] = queue.Queue(maxsize=pool_size)
        self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # Pre-initialize the pool with authorized service instances
        for _ in range(pool_size):
            # Each thread must have its own service instance
            service = build("gmail", "v1", credentials=self.creds)
            self.pool.put(service)

    def get_service(self):
        """Get a service instance from the pool."""
        return self.pool.get()

    def return_service(self, service):
        """Return a service instance to the pool."""
        self.pool.put(service)


def get_gmail_service() -> Optional[Any]:
    """Authenticate and return a Gmail API service instance."""
    creds: Optional[Credentials] = None
    token_path = "data/token.json"
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.error("Valid token.json not found in data/. Run main.py to authenticate.")
            return None
    return build("gmail", "v1", credentials=creds)


def setup_audit() -> Tuple[GmailServicePool, Dict[str, Any]]:
    """Set up service pool and load email cache for audit."""
    token_path = "data/token.json"
    if not os.path.exists(token_path):
        logger.error("Valid token.json not found in data/. Run main.py to authenticate.")
        raise FileNotFoundError("token.json not found")

    service_pool = GmailServicePool(token_path, pool_size=5)
    email_cache = load_email_cache()
    logger.info(f"Loaded {len(email_cache)} emails from cache")
    return service_pool, email_cache


def fetch_message_ids(service_pool: GmailServicePool, max_emails: int) -> List[Dict[str, str]]:
    """Fetch message IDs from Gmail API with pagination."""
    messages: List[Dict[str, str]] = []
    page_token: Optional[str] = None
    remaining_emails = max_emails

    while len(messages) < max_emails:
        batch_size = min(remaining_emails, 500)
        request_params = {"userId": "me", "maxResults": batch_size}
        if page_token:
            request_params["pageToken"] = page_token

        service = service_pool.get_service()
        try:
            results: Dict[str, Any] = service.users().messages().list(**request_params).execute()
            batch_messages: List[Dict[str, str]] = results.get("messages", [])
        finally:
            service_pool.return_service(service)

        messages.extend(batch_messages)
        logger.debug(f"Fetched batch of {len(batch_messages)} message IDs (total: {len(messages)})")

        page_token = results.get("nextPageToken")
        if not page_token:
            break

        remaining_emails = max_emails - len(messages)
        if remaining_emails <= 0:
            break

    logger.info(f"Fetched {len(messages)} message IDs")
    return messages


def fetch_uncached_messages(service_pool: GmailServicePool, email_cache: Dict[str, Any], messages_to_fetch: List[Dict[str, str]]) -> int:
    """Fetch uncached messages in parallel and update cache."""
    if not messages_to_fetch:
        return 0

    logger.info(f"Fetching {len(messages_to_fetch)} uncached emails in parallel...")
    fetched_count = 0

    def fetch_message(msg):
        msg_id = msg["id"]
        service = service_pool.get_service()
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    fetched_msg = (
                        service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=msg_id,
                            format="metadata",
                            metadataHeaders=["From", "Subject", "Date"],
                        )
                        .execute()
                    )
                    return msg_id, fetched_msg
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.warning(f"Failed to fetch message {msg_id} after {max_retries} attempts: {e}")
                        return msg_id, None
                    logger.debug(f"Retry {attempt + 1} for message {msg_id}: {e}")
                    time.sleep(0.1 * (2**attempt))  # Exponential backoff
        finally:
            service_pool.return_service(service)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_msg = {executor.submit(fetch_message, msg): msg for msg in messages_to_fetch}

        for future in as_completed(future_to_msg):
            msg_id, fetched_msg = future.result()
            if fetched_msg:
                email_cache[msg_id] = fetched_msg
                fetched_count += 1
                logger.debug(f"Fetched and cached message {msg_id}")

    return fetched_count


def process_messages(email_cache: Dict[str, Any], messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Process cached email messages to extract metadata for analysis.

    Extracts relevant fields from Gmail API response data including sender,
    subject, date, labels, and calculates email age. This prepares the data
    for aggregation and scoring.

    Args:
        email_cache: Dictionary mapping message IDs to cached Gmail API responses
        messages: List of message dictionaries with 'id' keys

    Returns:
        List of dictionaries with extracted email metadata:
            - id: Message ID
            - from: Sender email address
            - subject: Email subject line
            - date: Original date string
            - age_days: Days since email was sent (None if unparseable)
            - unread/starred/important: Boolean label flags
            - social/updates/promotions: Boolean category flags
    """
    data: List[Dict[str, Any]] = []
    now: datetime = datetime.now(timezone.utc)

    for m in messages:
        msg_id = m["id"]
        cached_msg = email_cache[msg_id]
        headers: List[Dict[str, str]] = cached_msg.get("payload", {}).get("headers", [])
        from_header: str = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject: str = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        date_str: str = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

        # Parse date
        age_days: Optional[float] = None
        try:
            date_parsed: datetime = parsedate_to_datetime(date_str)
            age_days = (now - date_parsed).days
        except Exception:
            pass  # Skip invalid dates

        # Check labels
        labels: List[str] = cached_msg.get("labelIds", [])
        is_unread: bool = GmailLabels.UNREAD in labels
        is_starred: bool = GmailLabels.STARRED in labels
        is_important: bool = GmailLabels.IMPORTANT in labels
        is_social: bool = GmailLabels.CATEGORY_SOCIAL in labels
        is_updates: bool = GmailLabels.CATEGORY_UPDATES in labels
        is_promotions: bool = GmailLabels.CATEGORY_PROMOTIONS in labels

        logger.debug(f"Email ID: {msg_id}, From: {from_header}, Subject: {subject}, Date: {date_str}")

        row: Dict[str, Any] = {
            "id": msg_id,
            "unread": is_unread,
            "starred": is_starred,
            "important": is_important,
            "social": is_social,
            "updates": is_updates,
            "promotions": is_promotions,
            "from": from_header,
            "subject": subject,
            "date": date_str,
            "age_days": age_days,
        }
        data.append(row)

    logger.info(f"Processed {len(data)} emails")
    return data


def prune_cache(email_cache: Dict[str, Any], current_email_ids: Set[str]) -> int:
    """Prune emails from cache that are no longer present."""
    pruned_count = 0
    for msg_id in list(email_cache.keys()):
        if msg_id not in current_email_ids:
            del email_cache[msg_id]
            pruned_count += 1
    if pruned_count > 0:
        logger.info(f"Pruned {pruned_count} removed emails from cache")
    return pruned_count


def aggregate_and_score(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate email data by sender and calculate ignorance scores.

    Groups emails by sender and computes various metrics including an "ignorance score"
    that combines email volume with unread percentage to identify potential noise makers.

    The ignorance score is calculated as: volume × (100 - open_rate)
    This gives higher scores to senders who send many emails that remain unread.

    Args:
        df: DataFrame with individual email data containing columns:
            - from: Sender email address
            - id: Email ID (for counting)
            - unread: Boolean indicating if email is unread
            - starred: Boolean for starred status
            - important: Boolean for important status
            - social/updates/promotions: Boolean for category labels
            - age_days: Days since email was sent

    Returns:
        DataFrame aggregated by sender with columns:
            - from: Sender email address
            - total_volume: Total emails from this sender
            - unread_count: Number of unread emails
            - starred_count/important_count/social_count/etc.: Category counts
            - avg_recency_days: Average age of emails in days
            - open_rate: Percentage of emails that were opened (100 - unread%)
            - ignorance_score: Calculated noise score (higher = more problematic)
    """
    # Filter out rows with invalid dates
    df = df.dropna(subset=["age_days"])
    logger.info(f"Filtered to {len(df)} valid emails with parseable dates")

    # Aggregate by sender
    audit_summary: pd.DataFrame = (
        df.groupby("from")
        .agg(
            total_volume=("id", "count"),
            unread_count=("unread", "sum"),
            starred_count=("starred", "sum"),
            important_count=("important", "sum"),
            social_count=("social", "sum"),
            updates_count=("updates", "sum"),
            promotions_count=("promotions", "sum"),
            avg_recency_days=("age_days", "mean"),
        )
        .reset_index()
    )

    # Calculate scores
    audit_summary["open_rate"] = ((audit_summary["total_volume"] - audit_summary["unread_count"]) / audit_summary["total_volume"]) * 100
    audit_summary["ignorance_score"] = audit_summary["total_volume"] * (100 - audit_summary["open_rate"])

    # Sort by ignorance score
    audit_summary = audit_summary.sort_values(by="ignorance_score", ascending=False)

    logger.info(f"Aggregated data for {len(audit_summary)} senders")
    return audit_summary


def save_report(audit_summary: pd.DataFrame) -> None:
    """Save audit report to CSV file."""
    output_path: str = "data/noise_report.csv"
    audit_summary.to_csv(output_path, index=False)
    logger.info(f"Audit complete! Report saved to {output_path}")


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
