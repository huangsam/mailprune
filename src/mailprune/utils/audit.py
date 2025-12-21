import logging
import os
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..constants import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CACHE_PATH,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_TOKEN_PATH,
    GMAIL_API_SCOPES,
    GMAIL_API_SERVICE_NAME,
    GMAIL_API_VERSION,
    GmailLabels,
)
from .helpers import load_email_cache

logger = logging.getLogger(__name__)


def execute_batch_with_retry(batch, max_retries=5) -> None:
    """Execute a Gmail API batch request with exponential backoff retry on rate limits."""
    for attempt in range(max_retries):
        try:
            batch.execute()
            return
        except HttpError as e:
            if e.resp.status == 429:  # Rate limit exceeded
                wait_time = (2**attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                logger.warning(f"Rate limited on batch execute, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                raise  # Re-raise non-rate-limit errors
    raise HttpError("Max retries exceeded for rate limit on batch execute", None)


def get_gmail_service() -> Optional[Any]:
    """Authenticate and return a Gmail API service instance."""
    creds: Optional[Credentials] = None
    if os.path.exists(DEFAULT_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(DEFAULT_TOKEN_PATH, GMAIL_API_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.error(f"Valid {DEFAULT_TOKEN_PATH} not found in data. Check if {DEFAULT_CREDENTIALS_PATH} exists.")
            return None
    return build(GMAIL_API_SERVICE_NAME, GMAIL_API_VERSION, credentials=creds)


def setup_audit(cache_path: str = DEFAULT_CACHE_PATH) -> Tuple[Any, Dict[str, Any]]:
    """Set up service and load email cache for audit."""
    if not os.path.exists(DEFAULT_TOKEN_PATH):
        logger.error("Valid token.json not found in data/. Run main.py to authenticate.")
        raise FileNotFoundError("token.json not found")

    service = get_gmail_service()
    email_cache = load_email_cache(cache_path)
    logger.info(f"Loaded {len(email_cache)} emails from cache")
    return service, email_cache


def fetch_message_ids(service, max_emails: int, query: str = "") -> List[Dict[str, str]]:
    """Fetch message IDs from Gmail API with pagination."""
    messages: List[Dict[str, str]] = []
    page_token: Optional[str] = None
    remaining_emails = max_emails

    while len(messages) < max_emails:
        batch_size = min(remaining_emails, 500)
        request_params = {"userId": "me", "maxResults": batch_size}
        if query:
            request_params["q"] = query
        if page_token:
            request_params["pageToken"] = page_token

        results: Dict[str, Any] = service.users().messages().list(**request_params).execute()
        batch_messages: List[Dict[str, str]] = results.get("messages", [])

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


def fetch_uncached_messages(service, email_cache: Dict[str, Any], messages_to_fetch: List[Dict[str, str]]) -> int:
    """Fetch uncached messages in batches sequentially."""
    if not messages_to_fetch:
        return 0

    logger.info(f"Fetching {len(messages_to_fetch)} uncached emails in batches of {DEFAULT_BATCH_SIZE}...")
    fetched_count = 0
    batch_size = DEFAULT_BATCH_SIZE

    # Split into batches
    batches = [messages_to_fetch[i : i + batch_size] for i in range(0, len(messages_to_fetch), batch_size)]

    def fetch_batch(batch_messages):
        batch = service.new_batch_http_request()
        results = {}

        def callback(request_id, response, exception):
            results[request_id] = (response, exception)

        # Uses the users.messsages.get API:
        # https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get
        for msg in batch_messages:
            msg_id = msg["id"]
            request = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="full",  # Returns full message with all headers and body
                )
            )
            batch.add(request, callback=callback, request_id=msg_id)

        execute_batch_with_retry(batch)
        batch_fetched = 0
        for msg_id, (resp, exc) in results.items():
            if exc:
                logger.warning(f"Failed to fetch message {msg_id}: {exc}")
            else:
                email_cache[msg_id] = resp
                batch_fetched += 1
                logger.debug(f"Fetched and cached message {msg_id}")
        return batch_fetched

    # Process batches sequentially
    for batch in batches:
        fetched_count += fetch_batch(batch)

    logger.info(f"Fetched {fetched_count} messages in {len(batches)} batches")
    return fetched_count


def process_messages(email_cache: Dict[str, Any], messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Process cached email messages to extract metadata for analysis.

    Extracts relevant fields from Gmail API response data including sender,
    subject, date, labels, email snippet, and calculates email age. This prepares the data
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
            - snippet: Email content preview (first ~200 characters)
            - unread/starred/important: Boolean label flags
            - social/updates/promotions: Boolean category flags
    """
    data: List[Dict[str, Any]] = []
    now: datetime = datetime.now(timezone.utc)

    for m in messages:
        msg_id = m["id"]
        if msg_id not in email_cache:
            logger.warning(f"Skipping message {msg_id} - not in cache (likely failed to fetch due to rate limit)")
            continue
        cached_msg = email_cache[msg_id]
        headers: List[Dict[str, str]] = cached_msg.get("payload", {}).get("headers", [])
        from_header: str = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject: str = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        date_str: str = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

        # Extract email snippet (preview of body content)
        snippet: str = cached_msg.get("snippet", "")

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
            "snippet": snippet,  # Add email content snippet
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


def get_sender_subjects_from_cache(cache: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract sender-subject mapping from email cache."""
    sender_subjects = defaultdict(list)
    for email in cache.values():
        headers = email.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender_subjects[sender].append(subject)
    return dict(sender_subjects)


def get_sender_snippets_from_cache(cache: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract sender-snippet mapping from email cache for content analysis."""
    sender_snippets = defaultdict(list)
    for email in cache.values():
        headers = email.get("payload", {}).get("headers", [])
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
        snippet = email.get("snippet", "")
        if snippet:  # Only include emails with content snippets
            sender_snippets[sender].append(snippet)
    return dict(sender_snippets)
