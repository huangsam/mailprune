#!/usr/bin/env python3
"""
Script to run Phase 1: Email Audit
This script performs the audit of the last N emails and generates a noise report.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from mailprune.audit import perform_audit


def main():
    # Default to 2000 emails as per the plan
    max_emails = 2000

    # Allow overriding via command line argument
    if len(sys.argv) > 1:
        try:
            max_emails = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid number: {sys.argv[1]}. Using default {max_emails}.")

    logger.info(f"Running Phase 1 Audit with {max_emails} emails...")
    perform_audit(max_emails)


if __name__ == "__main__":
    main()
