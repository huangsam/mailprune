# Email Assessment Guide

## Introduction

This comprehensive guide walks you through assessing and optimizing your Gmail inbox using MailPrune. Whether you're dealing with email overload, want to improve productivity, or simply want to maintain a clean inbox, this framework provides data-driven insights and actionable recommendations.

**What you'll accomplish:**
- Analyze your email patterns and engagement habits
- Identify noise makers and low-value senders
- Get personalized cleanup recommendations
- Set up automated filtering and archiving
- Establish ongoing maintenance routines

## Prerequisites

Before starting, ensure you have:

### 1. Technical Requirements
- **Python 3.12+**: Required for running MailPrune
- **Git**: For cloning the repository
- **uv package manager**: For dependency management (install via `pip install uv`)
- **Terminal/Command Line**: Basic familiarity with command-line tools

### 2. Gmail Account Access
- **Gmail account**: The tool analyzes Gmail data via API
- **Google account permissions**: Ability to enable APIs and create credentials
- **Recent email activity**: At least 100+ emails for meaningful analysis

### 3. System Requirements
- **Internet connection**: Required for Gmail API access
- **Storage space**: ~100MB for code and data files
- **Permissions**: Ability to create files in the project directory

## Setup

### Step 1: Install MailPrune
```bash
# Clone the repository
gh repo clone huangsam/mailprune
cd mailprune

# Install dependencies (this may take a few minutes)
uv sync --editable
```

### Step 2: Set Up Gmail API Access

MailPrune uses Google's Gmail API to analyze your emails securely. This requires a one-time setup:

1. **Enable Gmail API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Gmail API for your project

2. **Create Credentials**:
   - Go to "Credentials" in the left sidebar
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as application type
   - Download the credentials file as `credentials.json`

3. **Place Credentials**:
    ```bash
    # Create data directory if it doesn't exist
    mkdir -p data

    # Move credentials file to the correct location
    mv ~/Downloads/credentials.json data/
    ```

4. **First Run Authorization**:
    ```bash
    # This will open a browser for Google authentication
    uv run mailprune audit --max-emails 100
    ```
    - Grant permissions when prompted
    - A `token.json` file will be created automatically

### Step 3: Verify Setup
```bash
# Test that everything works
uv run mailprune --help
```

**Troubleshooting:**
- If you get authentication errors, delete `data/token.json` and re-run the audit command
- Ensure `credentials.json` is in the `data/` directory
- Check that your Google account has Gmail enabled

## Quick Start (30 minutes)

For the impatient, here's the complete workflow:

```bash
# 1. Install & Setup (5 min)
gh repo clone huangsam/mailprune && cd mailprune
uv sync --editable
# Set up Gmail API credentials in data/credentials.json

# 2. Run Full Assessment (25 min)
uv run mailprune audit --max-emails 2000
uv run mailprune report
uv run mailprune engagement
uv run mailprune patterns --top-n 10 --by volume
uv run mailprune cluster --n-clusters 5
```

**Expected Results:** Health score, cleanup recommendations, and filter templates.

## Detailed Assessment Steps

### Step 1: Data Collection
```bash
uv run mailprune audit --max-emails 2000
```
**What it does:** Downloads and analyzes your recent emails, creates `data/noise_report.csv`

**What to expect:** Progress bar showing email processing, final count of emails analyzed

### Step 2: Generate Report
```bash
uv run mailprune report
```
**What it does:** Calculates overall metrics and identifies top noise makers

**What to expect:** Unread rate, average open rate, sender statistics

### Step 3: Analyze Engagement
```bash
uv run mailprune engagement
```
**What it does:** Categorizes senders by engagement levels (high/medium/low/zero)

**What to expect:** Percentage breakdown of engagement tiers, zero-engagement sender count

### Step 4: Content Pattern Analysis
```bash
uv run mailprune patterns --top-n 10 --by volume
uv run mailprune patterns --top-n 10 --by ignorance
```
**What it does:** Analyzes email content for intent patterns using NLP

**What to expect:** Top senders with intent classifications (promotional/social/transactional/etc.)

### Step 5: Clustering Analysis
```bash
uv run mailprune cluster --n-clusters 5
```
**What it does:** Groups similar senders using machine learning clustering

**What to expect:** 5 sender clusters with cleanup recommendations and priority scores

## Assessment Framework

### Health Score Calculation
**Formula:** `Health Score = (Open Rate × 0.5) + ((100 - Unread Rate) × 0.5)`

**Interpretation:**
- **90-100: Excellent** - Clean, well-managed inbox
- **80-89: Good** - Minor cleanup needed
- **70-79: Moderate** - Significant cleanup recommended
- **60-69: Poor** - Major cleanup required
- **0-59: Critical** - Inbox management overhaul needed

### Success Metrics
- **Unread Rate:** <5% = Excellent, <10% = Good, >20% = Needs attention
- **Zero Engagement Senders:** <2% = Excellent, <5% = Good, >10% = Problematic
- **High Engagement Senders:** >90% = Excellent, >80% = Good

### Intent-Based Recommendations

**🎯 Promotional Emails:**
- **High Engagement:** Keep, but consider digest mode
- **Low/Zero Engagement:** Unsubscribe immediately
- **High Volume:** Create filters to skip inbox

**💳 Transactional Emails:**
- **High Engagement:** Keep with auto-archive after 30 days
- **Low Engagement:** Archive immediately
- **All:** Label as "Transactions"

**📧 Informational Emails:**
- **High Engagement:** Keep in inbox
- **Low Engagement:** Move to digest folder
- **Newsletters:** Consider weekly digest

**👥 Social Emails:**
- **High Engagement:** Keep in inbox
- **Low Engagement:** Review monthly
- **Personal:** Always keep

## Action Plan

### Phase 1: Quick Wins (Week 1)
**Goal:** Remove obvious noise with minimal effort

- ✅ Unsubscribe zero-engagement promotional senders
- ✅ Block spam-like senders (high volume, low engagement)
- ✅ Set up basic promotional filters
- **Impact:** 20-40% reduction in daily email volume

### Phase 2: Strategic Filtering (Week 2)
**Goal:** Automate email organization

- ✅ Create Gmail filters for promotional content
- ✅ Set up transactional email auto-archiving
- ✅ Label high-value informational senders
- **Impact:** 60-80% of emails now auto-organized

### Phase 3: Optimization (Week 3-4)
**Goal:** Fine-tune based on patterns

- ✅ Review medium-engagement senders
- ✅ Adjust filters based on clustering results
- ✅ Set up monthly audit reminders
- **Impact:** 90%+ email automation

### Phase 4: Maintenance (Ongoing)
**Goal:** Sustain clean inbox habits

- 📅 **Weekly:** Quick check of new subscriptions
- 📅 **Monthly:** `uv run mailprune audit --max-emails 500`
- 📅 **Quarterly:** Full assessment and filter review
- **Impact:** Prevent email accumulation

## Gmail Automation Setup

### Essential Filter Templates

**1. Promotional Content Filter:**
```
From: *@newsletter.com OR *@mailchimp.com OR *@constantcontact.com
Label: Promotions
Skip Inbox: yes
Apply label after 7 days: Archive
```

**2. Transactional Emails Filter:**
```
From: *@receipts.com OR *@orders.com OR *@billing.com OR *@support.com
Label: Transactions
Skip Inbox: yes
Apply label after 30 days: Archive
```

**3. Social & Personal Filter:**
```
From: *@facebook.com OR *@linkedin.com OR *@twitter.com
Label: Social
Skip Inbox: yes
Apply label after 14 days: Archive
```

**4. Banking & Finance Filter:**
```
From: *@bank.com OR *@credit.com OR *@financial.com
Label: Finance
Skip Inbox: yes
Mark as important: yes
```

### Advanced Automation

**Auto-Archive Rules:**
- Archive read emails older than 7 days
- Archive promotional emails after 3 days
- Keep unread emails in inbox

**Label Organization:**
- Use consistent color coding (red=urgent, blue=work, green=personal)
- Create sub-labels for better organization

## Maintenance & Monitoring

### Monthly Health Check (10 minutes)
```bash
# Quick assessment
uv run mailprune audit --max-emails 500
uv run mailprune report
```

**Track these metrics:**
- 📊 Unread rate trend (should stay <5%)
- 📊 Zero-engagement sender count (should stay <2%)
- 📊 New subscriptions added
- 📊 Filter effectiveness

### Quarterly Deep Review (30 minutes)
```bash
# Full assessment
uv run mailprune audit --max-emails 1000
uv run mailprune engagement
uv run mailprune patterns --top-n 5 --by volume
```

**Review and adjust:**
- Filter rules based on new patterns
- Subscription decisions
- Archive policies

### Tools for Ongoing Management

**Gmail Features to Leverage:**
- **Multiple Inboxes:** Show unread count only
- **Priority Inbox:** Let Gmail learn your preferences
- **Snooze:** Temporarily hide emails
- **Send & Archive:** Immediate cleanup

**Browser Extensions:**
- **Boomerang:** Schedule emails and reminders
- **ActiveInbox:** Advanced Gmail organization
- **Sortd:** Email prioritization

## FAQ

| Category | Question | Answer |
|----------|----------|--------|
| **Setup Issues** | "Gmail API has not been used in project" error? | Make sure you've enabled the Gmail API in Google Cloud Console and the credentials are for the correct project. |
| **Setup Issues** | Authentication keeps failing? | Delete `data/token.json` and re-run the audit command. Make sure you're using the correct Google account. |
| **Setup Issues** | "credentials.json not found"? | Ensure the file is in the `data/` directory, not `data/credentials/` or elsewhere. |
| **Assessment Issues** | Commands run but no output? | Check that you have emails in your account. Try with a smaller `--max-emails` value first. |
| **Assessment Issues** | Analysis shows no patterns? | You may need more email data. Try increasing `--max-emails` or ensure you have diverse senders. |
| **Assessment Issues** | Clustering fails? | Need at least 10-15 senders for meaningful clustering. Try with more emails. |
| **Performance Issues** | Audit takes too long? | Reduce `--max-emails` to 500-1000 for faster analysis. Full analysis of 2000+ emails can take 10-15 minutes. |
| **Performance Issues** | Memory errors? | Close other applications and try with fewer emails. The tool processes emails in batches. |
| **Gmail Integration** | Filters not working? | Check Gmail filter syntax. Test filters manually first. Ensure you're applying them to the correct account. |
| **Gmail Integration** | Can't create filters? | Make sure you're in Gmail web interface, not mobile app. Some Gmail features require web access. |
| **General Questions** | Is my data secure? | Yes - analysis happens locally. Only email metadata (subject, sender, dates) is processed, not content. |
| **General Questions** | Can I run this on multiple accounts? | Yes, but you'll need separate credentials and data directories for each account. |
| **General Questions** | How often should I run assessments? | Monthly for maintenance, quarterly for deep review, or whenever you feel overwhelmed by emails. |
| **General Questions** | What if I don't use Gmail? | Currently only Gmail is supported via the Gmail API. Other email providers would require different APIs. |
