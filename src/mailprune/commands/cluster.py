"""
Cluster command implementation for Mailprune.
"""

import click

from mailprune.utils import (
    cluster_senders_unsupervised,
    load_audit_data,
)


def analyze_clusters(csv_path: str, n_clusters: int = 5) -> None:
    """Analyze and display sender clusters for cleanup recommendations.

    This command performs unsupervised clustering on email senders based on their
    email volume, open rate, ignorance score, and unread count. It groups similar
    senders together to help identify patterns and prioritize cleanup efforts.

    The analysis includes:
    - Clustering senders into the specified number of groups
    - Displaying cluster statistics (total emails, average metrics)
    - Showing top senders within each cluster
    - Providing cleanup recommendations based on cluster characteristics
    """
    df = load_audit_data(csv_path)
    if df.empty:
        click.echo("No audit data found. Run 'mailprune audit' first.")
        return

    clusters = cluster_senders_unsupervised(df, n_clusters)
    if not clusters:
        click.echo("Not enough data for clustering analysis.")
        return

    # Group senders by cluster
    cluster_groups: dict[int, list[str]] = {}
    for sender, cluster_id in clusters.items():
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(sender)

    # Get sender data for analysis
    sender_data = {}
    for _, row in df.iterrows():
        sender_data[row["from"]] = {
            "total_volume": int(row["total_volume"]),
            "open_rate": row["open_rate"],
            "ignorance_score": row["ignorance_score"],
            "unread_count": int(row["unread_count"]),
        }

    click.echo("=== 📊 UNSUPERVISED SENDER CLUSTERING ANALYSIS ===")
    click.echo(f"Clustered {len(df)} senders into {n_clusters} groups based on volume, engagement, and noise patterns.")
    click.echo("")

    # Calculate statistics for all clusters first
    cluster_stats = {}
    for cluster_id in sorted(cluster_groups.keys()):
        senders = cluster_groups[cluster_id]
        total_emails = sum(sender_data[s]["total_volume"] for s in senders)
        avg_open_rate = sum(sender_data[s]["open_rate"] for s in senders) / len(senders)
        avg_ignorance = sum(sender_data[s]["ignorance_score"] for s in senders) / len(senders)
        total_unread = sum(sender_data[s]["unread_count"] for s in senders)

        cluster_stats[cluster_id] = {
            "senders": senders,
            "total_emails": total_emails,
            "avg_open_rate": avg_open_rate,
            "avg_ignorance": avg_ignorance,
            "total_unread": total_unread,
        }

    # Sort clusters by average open rate ascending (worst offenders first)
    sorted_clusters = sorted(cluster_stats.items(), key=lambda x: x[1]["avg_open_rate"])

    for cluster_id, stats in sorted_clusters:
        click.echo(f"🎯 CLUSTER {cluster_id} ({len(stats['senders'])} senders)")

        click.echo(
            f"   📈 Stats: {stats['total_emails']} emails, {stats['total_unread']} unread, "
            f"{stats['avg_open_rate']:.1f}% avg open rate, {stats['avg_ignorance']:.0f} avg ignorance"
        )
        click.echo("   🗑️  Potential cleanup targets:")

        # Sort senders in cluster by ignorance score for cleanup suggestions
        sorted_senders = sorted(stats["senders"], key=lambda s: sender_data[s]["ignorance_score"], reverse=True)

        for sender in sorted_senders[:5]:  # Show top 5 per cluster
            data = sender_data[sender]
            click.echo(f"    • {sender:<50} | Vol: {data['total_volume']:3d} | Open: {data['open_rate']:5.1f}% | Score: {data['ignorance_score']:6.0f}")

        click.echo("")
