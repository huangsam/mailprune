import logging
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .constants import GmailLabels
from .utils import load_email_cache, save_email_cache

logger = logging.getLogger(__name__)

# Same scopes as the sanity check
SCOPES: List[str] = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service() -> Optional[Any]:
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


def perform_audit(max_emails: int = 2000) -> Optional[pd.DataFrame]:
    start_time: float = time.time()
    service: Optional[Any] = get_gmail_service()
    if not service:
        return None

    # Load existing cache
    email_cache = load_email_cache()
    logger.info(f"Loaded {len(email_cache)} emails from cache")

    logger.info(f"Starting audit of the last {max_emails} emails...")
    results: Dict[str, Any] = service.users().messages().list(userId="me", maxResults=max_emails).execute()
    messages: List[Dict[str, str]] = results.get("messages", [])
    fetch_time: float = time.time()
    logger.info(f"Fetched {len(messages)} message IDs in {fetch_time - start_time:.2f}s")

    data: List[Dict[str, Any]] = []
    now: datetime = datetime.now(timezone.utc)
    fetched_count = 0

    for m in messages:
        msg_id = m["id"]
        if msg_id in email_cache:
            # Use cached data
            cached_msg = email_cache[msg_id]
            logger.debug(f"Using cached data for message {msg_id}")
        else:
            # Fetch from API
            msg: Dict[str, Any] = (
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
            fetched_count += 1
            # Cache the raw message data
            email_cache[msg_id] = msg
            cached_msg = msg
            logger.debug(f"Fetched and cached message {msg_id}")

        # Process the message (same as before)
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

        # Check if unread
        labels: List[str] = cached_msg.get("labelIds", [])
        is_unread: bool = GmailLabels.UNREAD in labels
        is_starred: bool = GmailLabels.STARRED in labels
        is_important: bool = GmailLabels.IMPORTANT in labels
        is_social: bool = GmailLabels.CATEGORY_SOCIAL in labels
        is_updates: bool = GmailLabels.CATEGORY_UPDATES in labels
        is_promotions: bool = GmailLabels.CATEGORY_PROMOTIONS in labels
        logger.debug(f"Email ID: {msg_id}, From: {from_header}, Subject: {subject}, Date: {date_str}")

        # Build data row for a single email
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

    process_time: float = time.time()
    logger.info(f"Processed {len(data)} emails ({fetched_count} fetched from API, {len(data) - fetched_count} from cache) in {process_time - fetch_time:.2f}s")

    # Save updated cache
    save_email_cache(email_cache)

    # Process with Pandas
    df: pd.DataFrame = pd.DataFrame(data)

    # Filter out rows with invalid dates
    df = df.dropna(subset=["age_days"])
    logger.info(f"Filtered to {len(df)} valid emails with parseable dates")

    # Aggregating by Sender
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
    agg_time: float = time.time()
    logger.info(f"Aggregated data for {len(audit_summary)} senders in {agg_time - process_time:.2f}s")

    # Calculate Open Rate (percentage read)
    audit_summary["open_rate"] = ((audit_summary["total_volume"] - audit_summary["unread_count"]) / audit_summary["total_volume"]) * 100

    # Calculate Ignorance Score: High Volume + Low Open Rate
    # Using total_volume * (100 - open_rate) to combine
    audit_summary["ignorance_score"] = audit_summary["total_volume"] * (100 - audit_summary["open_rate"])

    # Sort by Ignorance Score descending
    audit_summary = audit_summary.sort_values(by="ignorance_score", ascending=False)

    # Save to data folder
    output_path: str = "data/noise_report.csv"
    audit_summary.to_csv(output_path, index=False)
    save_time: float = time.time()
    logger.info(f"Audit complete! Report saved to {output_path} in total {save_time - start_time:.2f}s")

    return audit_summary
