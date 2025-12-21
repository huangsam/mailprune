# Email Assessment Guide

This guide provides a framework for assessing your email inbox using MailPrune. For AI agents and automated tools, see [AGENTS.md](AGENTS.md) for technical details.

## Prerequisites
- Install: `gh repo clone huangsam/mailprune; cd mailprune; uv sync --editable`
- Gmail API: Set up credentials in `data/` and run `uv run mailprune audit --max-emails 100`

## Step 1: Data Collection
```bash
uv run mailprune audit --max-emails 2000
```
Collects email data and generates initial noise report.

## Step 2: Generate Report
```bash
uv run mailprune report
```
Provides overview: unread rate, open rates, top noise makers.

## Step 3: Analyze Engagement
```bash
uv run mailprune engagement
```
Categorizes senders by engagement tiers (high/medium/low/zero).

## Step 4: Content Pattern Analysis
```bash
uv run mailprune patterns --top-n 10 --by volume
uv run mailprune patterns --top-n 10 --by ignorance
```
Analyzes sender content intents (promotional/transactional/informational/social).

## Step 5: Clustering
```bash
uv run mailprune cluster --n-clusters 5
```
Groups senders by patterns for deeper insights.

## Assessment Framework

### Health Score: `(Avg Open Rate × 0.4) + ((100 - Unread Rate) × 0.4) + (Sender Diversity × 0.2)`
- 80-100: Excellent
- 60-79: Good
- 40-59: Moderate
- 20-39: Poor
- 0-19: Critical

### Intent-Based Recommendations
- **Promotional**: Unsubscribe low/zero engagement; filter high volume.
- **Transactional**: Keep high engagement; archive low.
- **Informational**: Keep high; digest low.
- **Social**: Keep high; review low.

## Action Plan

### Phase 1: Quick Wins
- Unsubscribe zero-engagement promotional senders.
- Block spam-like senders.

### Phase 2: Strategic Filtering
- Create Gmail filters for promotional/transactional content.
- Set up auto-archiving.

### Phase 3: Optimization
- Review medium-engagement senders.
- Set up monthly audits.

### Phase 4: Maintenance
- Monthly: `uv run mailprune audit --max-emails 500`
- Quarterly: Review engagement patterns.

## Gmail Filter Templates
```
# Promotional
From: *@newsletter.com
Label: Promotions
Skip Inbox: yes

# Transactional
From: *@receipts.com
Label: Transactions
Skip Inbox: yes
Apply label after 30 days: Archive
```

## Monitoring
Track: Unread rate, open rate, processing time. Adjust filters monthly.
