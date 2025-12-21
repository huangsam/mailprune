class GmailLabels:
    """GmailLabels contains Gmail system labels as constants.

    You can find the full list of Gmail system labels here:
    https://developers.google.com/workspace/gmail/api/guides/labels
    """

    # Can be manually applied.
    INBOX = "INBOX"

    # Can be manually applied.
    SPAM = "SPAM"

    # Can be manually applied.
    TRASH = "TRASH"

    # Can be manually applied.
    UNREAD = "UNREAD"

    # Can be manually applied.
    STARRED = "STARRED"

    # Can be manually applied.
    IMPORTANT = "IMPORTANT"

    # Cannot be manually applied. Applied automatically to messages that are sent with drafts.send or
    # messages.send, inserted with messages.insert and the user's email in the From header, or sent by the
    # user through the web interface.
    SENT = "SENT"

    # Cannot be manually applied. Automatically applied to all draft messages created with the Gmail API or Gmail interface.
    DRAFT = "DRAFT"

    # Can be manually applied. Corresponds to messages that are displayed in the Personal tab of the Gmail interface.
    CATEGORY_PERSONAL = "CATEGORY_PERSONAL"

    # Can be manually applied. Corresponds to messages that are displayed in the Social tab of the Gmail interface.
    CATEGORY_SOCIAL = "CATEGORY_SOCIAL"

    # Can be manually applied. Corresponds to messages that are displayed in the Promotions tab of the Gmail interface.
    CATEGORY_PROMOTIONS = "CATEGORY_PROMOTIONS"

    # Can be manually applied. Corresponds to messages that are displayed in the Updates tab of the Gmail interface.
    CATEGORY_UPDATES = "CATEGORY_UPDATES"

    # Can be manually applied. Corresponds to messages that are displayed in the Forums tab of the Gmail interface.
    CATEGORY_FORUMS = "CATEGORY_FORUMS"


# File paths
DEFAULT_CSV_PATH = "data/noise_report.csv"
DEFAULT_CACHE_PATH = "data/email_cache.json"
DEFAULT_CREDENTIALS_PATH = "data/credentials.json"
DEFAULT_TOKEN_PATH = "data/token.json"

# Gmail API configuration
GMAIL_API_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GMAIL_API_SERVICE_NAME = "gmail"
GMAIL_API_VERSION = "v1"

# Analysis thresholds
ENGAGEMENT_HIGH_THRESHOLD = 80
ENGAGEMENT_MEDIUM_THRESHOLD = 50
ENGAGEMENT_LOW_THRESHOLD = 1

# Audit defaults
DEFAULT_MAX_EMAILS = 2000
DEFAULT_BATCH_SIZE = 10
