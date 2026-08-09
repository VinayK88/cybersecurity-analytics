from __future__ import annotations

import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"


def clean(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": clean(text).splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": clean(text).splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SETUP = """
import numpy as np
import pandas as pd

SEED = 88
rng = np.random.default_rng(SEED)
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 130)
pd.set_option("display.max_colwidth", 70)
"""


PROJECTS = [
    {
        "filename": "01_domain_infrastructure_correlation.ipynb",
        "title": "Domain Infrastructure Correlation",
        "description": "Identify shared infrastructure pivots across synthetic domain-registration and hosting observations.",
        "goal": "Rank infrastructure clusters for analyst review without treating shared hosting as proof of common ownership.",
        "data": """
        domain_count = 72
        infrastructure = pd.DataFrame({
            "domain": [f"example-{index:03d}.test" for index in range(domain_count)],
            "registrar": rng.choice(["Registrar-A", "Registrar-B", "Registrar-C"], domain_count, p=[0.45, 0.35, 0.20]),
            "nameserver": rng.choice([f"ns{index}.synthetic.net" for index in range(1, 9)], domain_count),
            "asn": rng.choice([64510, 64511, 64512, 64513, 64514], domain_count),
            "domain_age_days": rng.integers(2, 1800, domain_count),
            "rare_tld": rng.binomial(1, 0.18, domain_count),
            "privacy_service": rng.binomial(1, 0.42, domain_count),
        })
        infrastructure["observed_alert"] = (
            (infrastructure["domain_age_days"] < 45)
            & (infrastructure["rare_tld"] == 1)
        ).astype(int)
        print(infrastructure.head(6).to_string(index=False))
        """,
        "analysis": """
        cluster_summary = (
            infrastructure.groupby(["nameserver", "asn"], as_index=False)
            .agg(domains=("domain", "count"), alerts=("observed_alert", "sum"), median_age=("domain_age_days", "median"))
        )
        cluster_summary["review_score"] = (
            0.45 * np.minimum(cluster_summary["domains"] / 8, 1)
            + 0.40 * np.minimum(cluster_summary["alerts"] / 3, 1)
            + 0.15 * (cluster_summary["median_age"] < 90)
        ).round(3)
        ranked_clusters = cluster_summary.sort_values(["review_score", "domains"], ascending=False)
        print(ranked_clusters.head(8).to_string(index=False))
        """,
        "checks": """
        assert infrastructure["domain"].is_unique
        assert ranked_clusters["review_score"].between(0, 1).all()
        assert ranked_clusters["domains"].sum() == len(infrastructure)
        print("Checks passed; shared infrastructure remains a review lead, not an attribution claim.")
        """,
        "next": ["Add passive-DNS timestamps and source provenance.", "Require an independent signal before escalating a cluster."],
    },
    {
        "filename": "02_certificate_transparency_patterns.ipynb",
        "title": "Certificate Transparency Pattern Analysis",
        "description": "Explore synthetic certificate records to find unusual fingerprint and subject-alternative-name reuse.",
        "goal": "Surface certificate clusters that may connect infrastructure while preserving uncertainty and context.",
        "data": """
        certificate_count = 96
        certificates = pd.DataFrame({
            "certificate_id": [f"cert-{index:04d}" for index in range(certificate_count)],
            "fingerprint_group": rng.choice([f"fp-{index:02d}" for index in range(18)], certificate_count),
            "issuer": rng.choice(["CA-One", "CA-Two", "CA-Three"], certificate_count),
            "san_count": rng.integers(1, 18, certificate_count),
            "validity_days": rng.choice([30, 90, 180, 365], certificate_count, p=[0.10, 0.55, 0.10, 0.25]),
            "domain_age_days": rng.integers(1, 1500, certificate_count),
        })
        certificates["new_domain"] = (certificates["domain_age_days"] < 30).astype(int)
        print(certificates.head(6).to_string(index=False))
        """,
        "analysis": """
        fingerprint_summary = (
            certificates.groupby("fingerprint_group", as_index=False)
            .agg(certificates=("certificate_id", "count"), issuers=("issuer", "nunique"), median_sans=("san_count", "median"), new_domains=("new_domain", "sum"))
        )
        fingerprint_summary["pattern_score"] = (
            0.50 * np.minimum(fingerprint_summary["certificates"] / 8, 1)
            + 0.30 * np.minimum(fingerprint_summary["new_domains"] / 3, 1)
            + 0.20 * np.minimum(fingerprint_summary["median_sans"] / 12, 1)
        ).round(3)
        ranked_fingerprints = fingerprint_summary.sort_values("pattern_score", ascending=False)
        print(ranked_fingerprints.head(8).to_string(index=False))
        """,
        "checks": """
        assert certificates["certificate_id"].is_unique
        assert ranked_fingerprints["pattern_score"].between(0, 1).all()
        assert ranked_fingerprints["certificates"].sum() == certificate_count
        print("Checks passed; certificate reuse is contextual evidence, not proof of control.")
        """,
        "next": ["Compare first-seen dates across transparent certificate sources.", "Separate CDN and managed-platform reuse before review."],
    },
    {
        "filename": "03_passive_dns_flux_detection.ipynb",
        "title": "Passive DNS Flux Detection",
        "description": "Measure address churn, geographic spread, and TTL behavior in synthetic passive-DNS observations.",
        "goal": "Prioritize domains with fast-changing resolution patterns for defensive investigation.",
        "data": """
        rows = []
        for domain_index in range(15):
            for day in range(14):
                burst = int(domain_index in {2, 7, 11})
                rows.append({
                    "domain": f"service-{domain_index:02d}.test",
                    "day": day,
                    "unique_ips": int(rng.poisson(1.5 + 3.5 * burst) + 1),
                    "countries": int(rng.integers(1, 3 + 4 * burst)),
                    "ttl_seconds": int(rng.choice([60, 120, 300] if burst else [300, 900, 3600])),
                    "address_changes": int(rng.poisson(0.7 + 3.0 * burst)),
                })
        passive_dns = pd.DataFrame(rows)
        print(passive_dns.head(8).to_string(index=False))
        """,
        "analysis": """
        domain_behavior = passive_dns.groupby("domain", as_index=False).agg(
            mean_ips=("unique_ips", "mean"),
            max_countries=("countries", "max"),
            median_ttl=("ttl_seconds", "median"),
            total_changes=("address_changes", "sum"),
        )
        domain_behavior["flux_score"] = (
            0.30 * np.minimum(domain_behavior["mean_ips"] / 6, 1)
            + 0.25 * np.minimum(domain_behavior["max_countries"] / 6, 1)
            + 0.30 * np.minimum(domain_behavior["total_changes"] / 45, 1)
            + 0.15 * (domain_behavior["median_ttl"] <= 120)
        ).round(3)
        ranked_domains = domain_behavior.sort_values("flux_score", ascending=False)
        print(ranked_domains.head(7).to_string(index=False))
        """,
        "checks": """
        assert len(passive_dns) == 210
        assert ranked_domains["flux_score"].between(0, 1).all()
        assert ranked_domains.iloc[0]["total_changes"] >= ranked_domains["total_changes"].median()
        print("Checks passed; results identify behavioral outliers for corroboration.")
        """,
        "next": ["Add provider baselines to reduce CDN false positives.", "Track source coverage and observation gaps by day."],
    },
    {
        "filename": "04_social_coordination_detection.ipynb",
        "title": "Coordinated Activity Detection",
        "description": "Find unusually synchronized content sharing in a synthetic public-post dataset.",
        "goal": "Generate transparent coordination leads without inferring identity, intent, or authenticity from timing alone.",
        "data": """
        post_count = 240
        posts = pd.DataFrame({
            "account": rng.choice([f"acct-{index:02d}" for index in range(36)], post_count),
            "time_bucket": rng.integers(0, 48, post_count),
            "phrase_id": rng.choice([f"phrase-{index:02d}" for index in range(24)], post_count),
            "url_id": rng.choice([f"url-{index:02d}" for index in range(20)], post_count),
        })
        coordinated_accounts = ["acct-02", "acct-09", "acct-17", "acct-25"]
        injected = pd.DataFrame({
            "account": coordinated_accounts * 3,
            "time_bucket": np.repeat([8, 21, 37], len(coordinated_accounts)),
            "phrase_id": np.repeat(["phrase-sync-a", "phrase-sync-b", "phrase-sync-c"], len(coordinated_accounts)),
            "url_id": np.repeat(["url-sync-a", "url-sync-b", "url-sync-c"], len(coordinated_accounts)),
        })
        posts = pd.concat([posts, injected], ignore_index=True)
        print(posts.tail(8).to_string(index=False))
        """,
        "analysis": """
        shared = posts.merge(posts, on=["time_bucket", "phrase_id", "url_id"], suffixes=("_left", "_right"))
        shared = shared[shared["account_left"] < shared["account_right"]]
        pair_scores = (
            shared.groupby(["account_left", "account_right"], as_index=False)
            .size().rename(columns={"size": "synchronized_posts"})
            .sort_values("synchronized_posts", ascending=False)
        )
        pair_scores["review_priority"] = np.minimum(pair_scores["synchronized_posts"] / 3, 1).round(3)
        print(pair_scores.head(10).to_string(index=False))
        """,
        "checks": """
        assert (pair_scores["account_left"] < pair_scores["account_right"]).all()
        assert pair_scores["review_priority"].between(0, 1).all()
        assert pair_scores["synchronized_posts"].max() >= 3
        print("Checks passed; synchronization is a lead requiring content and context review.")
        """,
        "next": ["Add source-specific rate baselines and reshare semantics.", "Review only public content allowed by source terms."],
    },
    {
        "filename": "05_public_document_metadata.ipynb",
        "title": "Public Document Metadata Analysis",
        "description": "Analyze synthetic metadata fields that resemble openly published documents.",
        "goal": "Group related production patterns and identify metadata-hygiene issues without exposing personal identifiers.",
        "data": """
        document_count = 80
        documents = pd.DataFrame({
            "document_id": [f"doc-{index:03d}" for index in range(document_count)],
            "creator_tool": rng.choice(["Writer-A", "Writer-B", "PDF-Engine-C", "Scanner-D"], document_count),
            "template_id": rng.choice([f"template-{index:02d}" for index in range(10)], document_count),
            "timezone_offset": rng.choice([-8, -5, 0, 1, 5, 8], document_count),
            "revision_count": rng.integers(1, 24, document_count),
            "author_field_present": rng.binomial(1, 0.35, document_count),
        })
        print(documents.head(7).to_string(index=False))
        """,
        "analysis": """
        production_patterns = (
            documents.groupby(["creator_tool", "template_id"], as_index=False)
            .agg(documents=("document_id", "count"), timezones=("timezone_offset", "nunique"), author_fields=("author_field_present", "sum"), median_revisions=("revision_count", "median"))
        )
        production_patterns["metadata_hygiene_score"] = (
            1 - np.minimum(production_patterns["author_fields"] / production_patterns["documents"], 1)
        ).round(3)
        ranked_patterns = production_patterns.sort_values(["documents", "metadata_hygiene_score"], ascending=[False, True])
        print(ranked_patterns.head(10).to_string(index=False))
        """,
        "checks": """
        assert documents["document_id"].is_unique
        assert ranked_patterns["documents"].sum() == document_count
        assert ranked_patterns["metadata_hygiene_score"].between(0, 1).all()
        print("Checks passed; metadata patterns do not establish authorship.")
        """,
        "next": ["Hash or redact direct identifiers before analysis.", "Record document provenance and publication timestamps."],
    },
    {
        "filename": "06_image_geolocation_confidence.ipynb",
        "title": "Image Geolocation Confidence Scoring",
        "description": "Combine synthetic visual and contextual signals into an auditable location-confidence score.",
        "goal": "Separate supporting, conflicting, and missing geolocation evidence without claiming an exact real-world location.",
        "data": """
        observation_count = 90
        image_evidence = pd.DataFrame({
            "image_id": [f"image-{index:03d}" for index in range(observation_count)],
            "landmark_match": rng.beta(2.2, 2.0, observation_count),
            "signage_match": rng.beta(2.0, 2.5, observation_count),
            "terrain_match": rng.beta(2.3, 2.1, observation_count),
            "sun_consistency": rng.beta(2.4, 1.8, observation_count),
            "time_context_match": rng.beta(2.0, 2.0, observation_count),
            "metadata_conflict": rng.binomial(1, 0.12, observation_count),
        })
        print(image_evidence.head(6).round(3).to_string(index=False))
        """,
        "analysis": """
        weights = {"landmark_match": 0.30, "signage_match": 0.20, "terrain_match": 0.20, "sun_consistency": 0.15, "time_context_match": 0.15}
        evidence_score = sum(image_evidence[column] * weight for column, weight in weights.items())
        image_evidence["confidence_score"] = np.clip(evidence_score - 0.25 * image_evidence["metadata_conflict"], 0, 1).round(3)
        image_evidence["confidence_band"] = pd.cut(image_evidence["confidence_score"], bins=[-0.01, 0.45, 0.70, 1.0], labels=["low", "medium", "high"])
        ranked_images = image_evidence.sort_values("confidence_score", ascending=False)
        print(ranked_images[["image_id", "confidence_score", "confidence_band", "metadata_conflict"]].head(10).to_string(index=False))
        """,
        "checks": """
        assert image_evidence["confidence_score"].between(0, 1).all()
        assert image_evidence["confidence_band"].notna().all()
        conflicted = image_evidence[image_evidence["metadata_conflict"] == 1]
        assert len(conflicted) > 0
        print("Checks passed; confidence bands preserve uncertainty and conflicting evidence.")
        """,
        "next": ["Calibrate weights against reviewed historical cases.", "Store evidence citations for every scored signal."],
    },
    {
        "filename": "07_privacy_preserving_entity_resolution.ipynb",
        "title": "Privacy-Preserving Entity Resolution",
        "description": "Score synthetic candidate pairs using abstracted similarity signals rather than raw personal data.",
        "goal": "Prioritize possible record links while making false-positive risk and privacy limits explicit.",
        "data": """
        pair_count = 180
        candidate_pairs = pd.DataFrame({
            "pair_id": [f"pair-{index:04d}" for index in range(pair_count)],
            "username_similarity": rng.beta(1.6, 2.4, pair_count),
            "avatar_hash_match": rng.binomial(1, 0.10, pair_count),
            "bio_token_overlap": rng.beta(1.4, 3.0, pair_count),
            "location_consistency": rng.binomial(1, 0.38, pair_count),
            "known_match": np.zeros(pair_count, dtype=int),
        })
        positive_index = rng.choice(pair_count, 24, replace=False)
        candidate_pairs.loc[positive_index, "known_match"] = 1
        candidate_pairs.loc[positive_index, "username_similarity"] = rng.uniform(0.72, 1.0, len(positive_index))
        candidate_pairs.loc[positive_index, "bio_token_overlap"] = rng.uniform(0.55, 1.0, len(positive_index))
        candidate_pairs.loc[positive_index, "avatar_hash_match"] = rng.binomial(1, 0.75, len(positive_index))
        print(candidate_pairs.head(7).round(3).to_string(index=False))
        """,
        "analysis": """
        candidate_pairs["link_score"] = (
            0.42 * candidate_pairs["username_similarity"]
            + 0.28 * candidate_pairs["avatar_hash_match"]
            + 0.20 * candidate_pairs["bio_token_overlap"]
            + 0.10 * candidate_pairs["location_consistency"]
        ).round(3)
        threshold = 0.68
        candidate_pairs["predicted_link"] = (candidate_pairs["link_score"] >= threshold).astype(int)
        tp = int(((candidate_pairs["known_match"] == 1) & (candidate_pairs["predicted_link"] == 1)).sum())
        fp = int(((candidate_pairs["known_match"] == 0) & (candidate_pairs["predicted_link"] == 1)).sum())
        fn = int(((candidate_pairs["known_match"] == 1) & (candidate_pairs["predicted_link"] == 0)).sum())
        print(pd.Series({"true_positives": tp, "false_positives": fp, "false_negatives": fn, "reviewed_pairs": pair_count}).to_string())
        print(candidate_pairs.sort_values("link_score", ascending=False).head(8).round(3).to_string(index=False))
        """,
        "checks": """
        assert candidate_pairs["pair_id"].is_unique
        assert candidate_pairs["link_score"].between(0, 1).all()
        assert tp > 0
        print("Checks passed; automated scores only prioritize human review and never establish identity.")
        """,
        "next": ["Measure precision and recall by source type.", "Minimize retention and keep raw identifiers outside analytical outputs."],
    },
    {
        "filename": "08_news_narrative_trends.ipynb",
        "title": "News Narrative Trend Analysis",
        "description": "Track synthetic topic volume and source diversity across a bounded news-style dataset.",
        "goal": "Distinguish broad narrative growth from spikes driven by a small number of sources.",
        "data": """
        topics = ["supply-chain", "ransomware", "cloud-risk", "identity", "ai-safety"]
        rows = []
        for day in range(30):
            for topic in topics:
                baseline = 4 + topics.index(topic)
                surge = 12 if topic == "cloud-risk" and 20 <= day <= 23 else 0
                article_count = int(rng.poisson(baseline + surge))
                for _ in range(article_count):
                    rows.append({"day": day, "topic": topic, "source": f"source-{rng.integers(1, 13):02d}"})
        articles = pd.DataFrame(rows)
        print("Rows:", len(articles))
        print(articles.head(8).to_string(index=False))
        """,
        "analysis": """
        daily = articles.groupby(["day", "topic"], as_index=False).agg(volume=("source", "count"), source_diversity=("source", "nunique"))
        topic_stats = daily.groupby("topic")["volume"].agg(["mean", "std"]).reset_index()
        daily = daily.merge(topic_stats, on="topic", how="left")
        daily["volume_zscore"] = ((daily["volume"] - daily["mean"]) / daily["std"].replace(0, 1)).round(2)
        daily["diversity_ratio"] = (daily["source_diversity"] / daily["volume"]).round(3)
        spikes = daily.sort_values("volume_zscore", ascending=False).head(10)
        print(spikes[["day", "topic", "volume", "source_diversity", "volume_zscore", "diversity_ratio"]].to_string(index=False))
        """,
        "checks": """
        assert daily["volume"].gt(0).all()
        assert daily["diversity_ratio"].between(0, 1).all()
        assert spikes.iloc[0]["volume_zscore"] > 1
        print("Checks passed; a volume spike is separated from breadth of source participation.")
        """,
        "next": ["Deduplicate syndicated copies before counting sources.", "Preserve article URLs, timestamps, and collection boundaries."],
    },
    {
        "filename": "09_web_exposure_profiling.ipynb",
        "title": "Public Web Exposure Profiling",
        "description": "Prioritize synthetic public-facing web assets using transparent security-hygiene indicators.",
        "goal": "Produce an explainable defensive review queue without scanning or interacting with live systems.",
        "data": """
        asset_count = 120
        assets = pd.DataFrame({
            "asset_id": [f"asset-{index:03d}" for index in range(asset_count)],
            "tls_age_days": rng.integers(0, 900, asset_count),
            "missing_security_headers": rng.integers(0, 6, asset_count),
            "login_surface": rng.binomial(1, 0.36, asset_count),
            "end_of_life_technology": rng.binomial(1, 0.14, asset_count),
            "public_admin_path": rng.binomial(1, 0.09, asset_count),
        })
        print(assets.head(7).to_string(index=False))
        """,
        "analysis": """
        assets["exposure_score"] = (
            0.20 * np.minimum(assets["tls_age_days"] / 730, 1)
            + 0.20 * np.minimum(assets["missing_security_headers"] / 5, 1)
            + 0.15 * assets["login_surface"]
            + 0.30 * assets["end_of_life_technology"]
            + 0.15 * assets["public_admin_path"]
        ).round(3)
        ranked_assets = assets.sort_values("exposure_score", ascending=False)
        print(ranked_assets.head(10).to_string(index=False))
        """,
        "checks": """
        assert assets["asset_id"].is_unique
        assert assets["exposure_score"].between(0, 1).all()
        assert ranked_assets["exposure_score"].is_monotonic_decreasing
        print("Checks passed; scores are for authorized defensive prioritization only.")
        """,
        "next": ["Validate ownership before any follow-up assessment.", "Use documented, non-invasive sources and respect robots and source terms."],
    },
    {
        "filename": "10_incident_timeline_fusion.ipynb",
        "title": "Incident Timeline Fusion",
        "description": "Combine synthetic public reports into reliability-weighted incident time windows.",
        "goal": "Create an auditable timeline that highlights corroborated events and visible contradictions.",
        "data": """
        observation_count = 160
        source_types = np.array(["official", "journalism", "technical-report", "community"])
        source_reliability = {"official": 0.90, "journalism": 0.78, "technical-report": 0.86, "community": 0.48}
        observations = pd.DataFrame({
            "observation_id": [f"obs-{index:04d}" for index in range(observation_count)],
            "source_type": rng.choice(source_types, observation_count, p=[0.18, 0.32, 0.28, 0.22]),
            "minute": rng.choice([30, 90, 150, 240, 360], observation_count, p=[0.12, 0.24, 0.30, 0.22, 0.12]) + rng.integers(-18, 19, observation_count),
            "event_type": rng.choice(["initial-access", "service-impact", "containment", "recovery"], observation_count),
            "contradiction": rng.binomial(1, 0.10, observation_count),
        })
        observations["reliability"] = observations["source_type"].map(source_reliability)
        observations["time_window"] = (observations["minute"] // 30) * 30
        print(observations.head(8).to_string(index=False))
        """,
        "analysis": """
        observations["evidence_weight"] = observations["reliability"] * (1 - 0.55 * observations["contradiction"])
        timeline = observations.groupby(["time_window", "event_type"], as_index=False).agg(
            reports=("observation_id", "count"),
            source_types=("source_type", "nunique"),
            evidence_weight=("evidence_weight", "sum"),
            contradictions=("contradiction", "sum"),
        )
        timeline["corroboration_score"] = (
            0.45 * np.minimum(timeline["evidence_weight"] / 8, 1)
            + 0.35 * np.minimum(timeline["source_types"] / 4, 1)
            + 0.20 * (1 - np.minimum(timeline["contradictions"] / timeline["reports"], 1))
        ).round(3)
        ranked_events = timeline.sort_values("corroboration_score", ascending=False)
        print(ranked_events.head(10).to_string(index=False))
        """,
        "checks": """
        assert observations["observation_id"].is_unique
        assert ranked_events["corroboration_score"].between(0, 1).all()
        assert ranked_events["reports"].sum() == observation_count
        print("Checks passed; contradictions remain visible instead of being silently discarded.")
        """,
        "next": ["Attach citations and archived source timestamps to every observation.", "Separate reported time, publication time, and analyst-inferred time."],
    },
]


def build_project(project: dict) -> dict:
    next_steps = "\n".join(f"- {item}" for item in project["next"])
    cells = [
        markdown(
            f"""
            # {project['title']}

            {project['description']}

            **Safety and scope:** This notebook uses deterministic synthetic data and makes no network requests. Its results are analytical leads, not attribution or identity claims.

            ## Goal

            {project['goal']}
            """
        ),
        markdown(
            """
            ## Setup

            The workflow runs offline with NumPy and Pandas. Parameters and source-like fields are visible so the analysis can be reviewed and rerun.

            ### Key Assumptions

            - All records are synthetic and contain no real people or infrastructure.
            - Scores prioritize review; they do not prove ownership, intent, identity, or location.
            - Real use requires documented authority, provenance, source terms, and retention limits.
            """
        ),
        code(SETUP),
        markdown("## Steps\n\n### 1. Create bounded synthetic observations"),
        code(project["data"]),
        markdown("### 2. Analyze and rank the observations"),
        code(project["analysis"]),
        markdown("## Checks\n\nRun deterministic integrity and reasonableness checks."),
        code(project["checks"]),
        markdown(f"## Next Steps\n\n{next_steps}"),
    ]
    return notebook(cells)


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    expected = {project["filename"] for project in PROJECTS}
    for old_path in NOTEBOOK_DIR.glob("*.ipynb"):
        if old_path.name not in expected:
            old_path.unlink()
    for project in PROJECTS:
        path = NOTEBOOK_DIR / project["filename"]
        path.write_text(
            json.dumps(build_project(project), indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"built {path.relative_to(ROOT)}")
    print(f"built {len(PROJECTS)} OSINT analytics notebooks")


if __name__ == "__main__":
    main()
