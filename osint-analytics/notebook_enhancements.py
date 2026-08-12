from __future__ import annotations

import textwrap


VISUAL_SETUP = """
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, mean_absolute_error, r2_score, roc_auc_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = globals().get("SEED", 88)

PALETTE = {
    "blue": "#2563EB",
    "gold": "#D4A72C",
    "orange": "#E76F51",
    "olive": "#708238",
    "pink": "#C65D86",
    "ink": "#172033",
    "muted": "#64748B",
    "grid": "#E2E8F0",
    "paper": "#FFFFFF",
}

plt.rcParams.update({
    "figure.facecolor": PALETTE["paper"],
    "axes.facecolor": PALETTE["paper"],
    "axes.edgecolor": PALETTE["grid"],
    "axes.labelcolor": PALETTE["ink"],
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "font.size": 10,
    "text.color": PALETTE["ink"],
    "xtick.color": PALETTE["muted"],
    "ytick.color": PALETTE["muted"],
    "grid.color": PALETTE["grid"],
    "grid.linewidth": 0.8,
})

def polish_axis(ax, title, subtitle, xlabel="", ylabel=""):
    ax.set_title(title, loc="left", pad=22)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=PALETTE["muted"], fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.75)
    ax.spines[["top", "right"]].set_visible(False)

def compare_binary_models(features, labels):
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.30,
        random_state=SEED,
        stratify=labels,
    )
    models = {
        "Logistic regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED),
        ),
        "Random forest": RandomForestClassifier(
            n_estimators=140,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=1,
        ),
    }
    rows, probabilities, fitted = [], {}, {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        probability = model.predict_proba(x_test)[:, 1]
        prediction = (probability >= 0.5).astype(int)
        rows.append({
            "model": name,
            "roc_auc": roc_auc_score(y_test, probability),
            "average_precision": average_precision_score(y_test, probability),
            "f1_at_0_5": f1_score(y_test, prediction, zero_division=0),
        })
        probabilities[name] = probability
        fitted[name] = model
    return pd.DataFrame(rows).set_index("model"), fitted, probabilities, y_test
"""


def clean(text: str) -> str:
    return textwrap.dedent(text).strip() + "\n"


def binary_classification(
    frame: str,
    label: str,
    features: list[str],
    title: str,
    x_feature: str,
    y_feature: str,
    prelude: str = "",
) -> str:
    return clean(
        f"""
        {prelude}
        ml_frame = {frame}.copy()
        ml_features = ml_frame[{features!r}]
        ml_labels = ml_frame["{label}"].to_numpy(int)

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.7), constrained_layout=True)
        for class_value, color, class_name in [
            (0, PALETTE["blue"], "Reference"),
            (1, PALETTE["orange"], "Injected / reviewed positive"),
        ]:
            subset = ml_frame[ml_frame["{label}"] == class_value]
            axes[0].scatter(subset["{x_feature}"], subset["{y_feature}"], s=30, alpha=0.58, color=color, edgecolors="none", label=class_name)
        axes[0].legend(frameon=False, fontsize=8)
        polish_axis(
            axes[0],
            "Signals overlap—review needs more than one clue",
            "Synthetic labels are exposed only to evaluate the learning workflow",
            "{x_feature.replace('_', ' ').title()}",
            "{y_feature.replace('_', ' ').title()}",
        )

        class_counts = ml_frame["{label}"].value_counts().sort_index()
        axes[1].bar(["Reference", "Positive"], class_counts.reindex([0, 1], fill_value=0), color=[PALETTE["blue"], PALETTE["orange"]])
        polish_axis(axes[1], "Class balance sets the evaluation context", "Counts are shown before the stratified train/test split", "", "Observations")
        fig.suptitle("{title} · evidence exploration", fontsize=16, fontweight="bold", x=0.01, ha="left")

        model_comparison, fitted_models, model_probabilities, test_labels = compare_binary_models(ml_features, ml_labels)
        forest = fitted_models["Random forest"]
        feature_importance = pd.Series(forest.feature_importances_, index=ml_features.columns).sort_values(ascending=False)
        best_model = model_comparison["average_precision"].idxmax()
        best_probability = model_probabilities[best_model]
        review_count = max(1, int(len(best_probability) * 0.10))
        top_positions = np.argsort(best_probability)[-review_count:]
        test_labels_array = np.asarray(test_labels)
        top_rate = float(test_labels_array[top_positions].mean())
        baseline_rate = float(test_labels_array.mean())

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
        comparison_display = model_comparison.rename(columns={{
            "roc_auc": "ROC AUC",
            "average_precision": "Average precision",
            "f1_at_0_5": "F1 @ 0.50",
        }})
        comparison_display.plot(kind="bar", ax=axes[0], color=[PALETTE["blue"], PALETTE["gold"], PALETTE["pink"]], width=0.72)
        axes[0].set_ylim(0, 1.05)
        axes[0].tick_params(axis="x", rotation=0)
        axes[0].legend(frameon=False, ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14))
        polish_axis(axes[0], "Transparent baseline versus nonlinear model", "Held-out synthetic observations; higher is better", "", "Score")

        importance_to_plot = feature_importance.head(7).sort_values()
        axes[1].barh(importance_to_plot.index.str.replace("_", " "), importance_to_plot.values, color=PALETTE["olive"])
        polish_axis(axes[1], "Random-forest feature importance", "Global split importance; it does not prove attribution or causality", "Relative importance", "")
        fig.suptitle("{title} · ML benchmark and explainability", fontsize=16, fontweight="bold", x=0.01, ha="left")

        print("Model comparison (held-out data):")
        print(model_comparison.round(3).to_string())
        print("\\nAnalyst takeaways:")
        print(f"- Best average precision: {{best_model}} ({{model_comparison.loc[best_model, 'average_precision']:.3f}}).")
        print(f"- The top-scored review decile contains {{top_rate / max(baseline_rate, 1e-9):.1f}}× the baseline positive rate.")
        print(f"- Strongest random-forest driver: {{feature_importance.index[0].replace('_', ' ')}}.")
        print("- These are synthetic review leads; independent corroboration and documented provenance remain mandatory.")
        """
    )


def surrogate_regression(
    frame: str,
    target: str,
    features: list[str],
    title: str,
    x_feature: str,
    y_feature: str,
) -> str:
    return clean(
        f"""
        surrogate_frame = {frame}.copy()
        surrogate_features = surrogate_frame[{features!r}]
        surrogate_target = surrogate_frame["{target}"].astype(float)
        target_band = pd.qcut(surrogate_target.rank(method="first"), q=3, labels=["Lower", "Middle", "Higher"])

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.7), constrained_layout=True)
        band_colors = {{"Lower": PALETTE["blue"], "Middle": PALETTE["gold"], "Higher": PALETTE["orange"]}}
        for band in ["Lower", "Middle", "Higher"]:
            subset = surrogate_frame[target_band == band]
            axes[0].scatter(subset["{x_feature}"], subset["{y_feature}"], s=34, alpha=0.62, color=band_colors[band], edgecolors="none", label=f"{{band}} score")
        axes[0].legend(frameon=False, fontsize=8)
        polish_axis(axes[0], "Evidence space behind the review score", "Score bands are discrete to keep comparisons accessible", "{x_feature.replace('_', ' ').title()}", "{y_feature.replace('_', ' ').title()}")

        axes[1].hist(surrogate_target, bins=14, color=PALETTE["blue"], edgecolor=PALETTE["paper"], linewidth=0.8)
        axes[1].axvline(surrogate_target.median(), color=PALETTE["gold"], linestyle="--", linewidth=2, label=f"median = {{surrogate_target.median():.2f}}")
        axes[1].legend(frameon=False)
        polish_axis(axes[1], "Score distribution and operating range", "A narrow range can make tiny rank differences look more certain than they are", "{target.replace('_', ' ').title()}", "Observations")
        fig.suptitle("{title} · score diagnostics", fontsize=16, fontweight="bold", x=0.01, ha="left")

        x_train, x_test, y_train, y_test = train_test_split(
            surrogate_features, surrogate_target, test_size=0.30, random_state=SEED
        )
        regressors = {{
            "Random forest": RandomForestRegressor(n_estimators=160, min_samples_leaf=2, random_state=SEED, n_jobs=1),
            "Gradient boosting": GradientBoostingRegressor(n_estimators=120, max_depth=2, learning_rate=0.05, random_state=SEED),
        }}
        regression_rows, predictions = [], {{}}
        for name, model in regressors.items():
            model.fit(x_train, y_train)
            prediction = model.predict(x_test)
            predictions[name] = prediction
            regression_rows.append({{
                "model": name,
                "mae": mean_absolute_error(y_test, prediction),
                "r2": r2_score(y_test, prediction),
            }})
        surrogate_metrics = pd.DataFrame(regression_rows).set_index("model")
        best_regressor = surrogate_metrics["mae"].idxmin()
        surrogate_importance = pd.Series(
            regressors["Random forest"].feature_importances_, index=surrogate_features.columns
        ).sort_values(ascending=False)

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
        for name, color in [("Random forest", PALETTE["blue"]), ("Gradient boosting", PALETTE["orange"])]:
            axes[0].scatter(y_test, predictions[name], s=34, alpha=0.58, color=color, edgecolors="none", label=name)
        score_min = min(float(y_test.min()), min(float(value.min()) for value in predictions.values()))
        score_max = max(float(y_test.max()), max(float(value.max()) for value in predictions.values()))
        axes[0].plot([score_min, score_max], [score_min, score_max], color=PALETTE["ink"], linestyle="--", linewidth=1.2, label="perfect surrogate")
        axes[0].legend(frameon=False, fontsize=8)
        polish_axis(axes[0], "How closely ML reproduces the transparent score", "Held-out rows; this tests score behavior, not real-world truth", "Observed score", "Predicted score")

        importance_to_plot = surrogate_importance.head(7).sort_values()
        axes[1].barh(importance_to_plot.index.str.replace("_", " "), importance_to_plot.values, color=PALETTE["olive"])
        polish_axis(axes[1], "Surrogate feature importance", "Useful for sensitivity review; not a claim about the outside world", "Relative importance", "")
        fig.suptitle("{title} · ML surrogate audit", fontsize=16, fontweight="bold", x=0.01, ha="left")

        print("Surrogate model comparison:")
        print(surrogate_metrics.round(3).to_string())
        print("\\nAnalyst takeaways:")
        print(f"- {{best_regressor}} best reproduces the transparent score (MAE {{surrogate_metrics.loc[best_regressor, 'mae']:.3f}}).")
        print(f"- Strongest score driver in the random-forest surrogate: {{surrogate_importance.index[0].replace('_', ' ')}}.")
        print("- High surrogate accuracy only shows that the heuristic is learnable; it does not validate the heuristic against real outcomes.")
        """
    )


CERTIFICATE_CLUSTERING = clean(
    """
    certificate_features = fingerprint_summary[["certificates", "issuers", "median_sans", "new_domains", "pattern_score"]]
    certificate_scaled = StandardScaler().fit_transform(certificate_features)
    trials, fitted = [], {}
    for candidate_k in range(2, 7):
        model = KMeans(n_clusters=candidate_k, n_init=30, random_state=SEED)
        labels = model.fit_predict(certificate_scaled)
        trials.append({"clusters": candidate_k, "silhouette": silhouette_score(certificate_scaled, labels), "inertia": model.inertia_})
        fitted[candidate_k] = (model, labels)
    certificate_diagnostics = pd.DataFrame(trials)
    selected_k = int(certificate_diagnostics.loc[certificate_diagnostics["silhouette"].idxmax(), "clusters"])
    _, certificate_cluster = fitted[selected_k]
    certificate_projection = PCA(n_components=2, random_state=SEED).fit_transform(certificate_scaled)
    fingerprint_ml = fingerprint_summary.assign(ml_cluster=certificate_cluster)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    axes[0].plot(certificate_diagnostics["clusters"], certificate_diagnostics["silhouette"], marker="o", linewidth=2, color=PALETTE["blue"])
    axes[0].axvline(selected_k, linestyle="--", color=PALETTE["gold"], label=f"selected k={selected_k}")
    axes[0].legend(frameon=False)
    polish_axis(axes[0], "Silhouette guides cluster selection", "Fingerprint summaries standardized before K-means", "Number of clusters", "Silhouette score")

    colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["orange"], PALETTE["olive"], PALETTE["pink"], PALETTE["muted"]]
    for cluster_id in range(selected_k):
        member = certificate_cluster == cluster_id
        axes[1].scatter(certificate_projection[member, 0], certificate_projection[member, 1], s=68, alpha=0.75, color=colors[cluster_id], label=f"Cluster {cluster_id}")
    axes[1].legend(frameon=False, fontsize=8)
    polish_axis(axes[1], "PCA view of certificate-pattern clusters", "Visualization uses two components; the model uses all five features", "Principal component 1", "Principal component 2")
    fig.suptitle("Certificate transparency patterns · unsupervised ML", fontsize=16, fontweight="bold", x=0.01, ha="left")

    cluster_profiles = fingerprint_ml.groupby("ml_cluster")[certificate_features.columns].mean()
    profile_z = (cluster_profiles - certificate_features.mean()) / certificate_features.std()
    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    from matplotlib.colors import BoundaryNorm, ListedColormap
    profile_colors = ListedColormap(["#334155", "#64748B", "#F8FAFC", "#D4A72C", "#E76F51"])
    profile_norm = BoundaryNorm([-2.5, -1.0, -0.25, 0.25, 1.0, 2.5], profile_colors.N, clip=True)
    image = ax.imshow(profile_z, cmap=profile_colors, norm=profile_norm, aspect="auto")
    ax.set_xticks(range(len(profile_z.columns)), profile_z.columns.str.replace("_", " "), rotation=25, ha="right")
    ax.set_yticks(range(len(profile_z)), [f"Cluster {value}" for value in profile_z.index])
    ax.set_title("Cluster profiles reveal different reuse patterns", loc="left", pad=22)
    ax.text(0, 1.02, "Values are standardized relative to all fingerprint groups", transform=ax.transAxes, color=PALETTE["muted"], fontsize=9)
    colorbar = fig.colorbar(image, ax=ax, ticks=[-1.75, -0.625, 0, 0.625, 1.75])
    colorbar.ax.set_yticklabels(["≤ -1", "-1 to -0.25", "near mean", "0.25 to 1", "≥ 1"])
    colorbar.set_label("Standard deviations")

    print(certificate_diagnostics.round(3).to_string(index=False))
    print("\\nAnalyst takeaways:")
    print(f"- Silhouette analysis selects {selected_k} behavioral clusters.")
    print(f"- Cluster {int(cluster_profiles['pattern_score'].idxmax())} has the highest average review score.")
    print("- Certificate reuse is contextual evidence and requires provider, CDN, and managed-platform baselines.")
    """
)


DOCUMENT_ANOMALY = clean(
    """
    document_features = production_patterns[["documents", "timezones", "author_fields", "median_revisions", "metadata_hygiene_score"]]
    document_scaled = StandardScaler().fit_transform(document_features)
    document_model = IsolationForest(n_estimators=180, contamination=0.15, random_state=SEED, n_jobs=1)
    production_patterns["anomaly_score"] = -document_model.fit(document_scaled).score_samples(document_scaled)
    production_patterns["behavior_cluster"] = KMeans(n_clusters=4, n_init=30, random_state=SEED).fit_predict(document_scaled)
    document_projection = PCA(n_components=2, random_state=SEED).fit_transform(document_scaled)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["orange"], PALETTE["olive"]]
    for cluster_id, color in enumerate(colors):
        member = production_patterns["behavior_cluster"] == cluster_id
        axes[0].scatter(document_projection[member, 0], document_projection[member, 1], s=64, alpha=0.75, color=color, label=f"Cluster {cluster_id}")
    axes[0].legend(frameon=False, fontsize=8)
    polish_axis(axes[0], "Production patterns form distinct groups", "K-means uses five metadata summary features", "Principal component 1", "Principal component 2")

    top_anomalies = production_patterns.nlargest(10, "anomaly_score").sort_values("anomaly_score")
    anomaly_labels = top_anomalies["creator_tool"] + " / " + top_anomalies["template_id"]
    axes[1].barh(anomaly_labels, top_anomalies["anomaly_score"], color=PALETTE["orange"])
    polish_axis(axes[1], "Isolation Forest prioritizes unusual patterns", "Higher score means less similar to the synthetic portfolio baseline", "Anomaly score", "")
    fig.suptitle("Public document metadata · clustering and anomaly ML", fontsize=16, fontweight="bold", x=0.01, ha="left")

    cluster_summary = production_patterns.groupby("behavior_cluster").agg(patterns=("template_id", "count"), mean_documents=("documents", "mean"), mean_hygiene=("metadata_hygiene_score", "mean"), mean_anomaly=("anomaly_score", "mean"))
    print(cluster_summary.round(3).to_string())
    print("\\nAnalyst takeaways:")
    print(f"- The top 15% most unusual patterns are review candidates, not authorship claims.")
    print(f"- Cluster {int(cluster_summary['mean_anomaly'].idxmax())} is least typical of the generated portfolio.")
    print("- Hash or redact direct identifiers and retain source provenance before adapting this workflow.")
    """
)


SOCIAL_GRAPH = clean(
    """
    import networkx as nx

    coordination_graph = nx.Graph()
    for row in pair_scores.itertuples(index=False):
        coordination_graph.add_edge(row.account_left, row.account_right, weight=float(row.synchronized_posts))
    graph_nodes = sorted(coordination_graph.nodes())
    weighted_adjacency = nx.to_numpy_array(coordination_graph, nodelist=graph_nodes, weight="weight")
    degree = weighted_adjacency.sum(axis=1)
    inv_sqrt_degree = np.diag(1 / np.sqrt(np.maximum(degree, 1)))
    laplacian = np.eye(len(graph_nodes)) - inv_sqrt_degree @ weighted_adjacency @ inv_sqrt_degree
    _, eigenvectors = np.linalg.eigh(laplacian)
    graph_embedding = eigenvectors[:, 1:4]
    graph_cluster = KMeans(n_clusters=4, n_init=30, random_state=SEED).fit_predict(graph_embedding)
    node_table = pd.DataFrame({"account": graph_nodes, "spectral_cluster": graph_cluster, "weighted_degree": degree})
    node_table["injected_coordination"] = node_table["account"].isin(coordinated_accounts).astype(int)

    position = nx.spring_layout(coordination_graph, seed=SEED, weight="weight")
    colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["orange"], PALETTE["olive"]]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), constrained_layout=True)
    nx.draw_networkx_edges(coordination_graph, position, ax=axes[0], edge_color=PALETTE["grid"], alpha=0.8)
    nx.draw_networkx_nodes(coordination_graph, position, ax=axes[0], node_color=[colors[value] for value in graph_cluster], node_size=170 + 24 * degree, edgecolors=PALETTE["ink"], linewidths=0.4)
    nx.draw_networkx_labels(coordination_graph, position, ax=axes[0], font_size=6)
    axes[0].set_title("Spectral communities summarize synchronized pairs", loc="left", pad=22)
    axes[0].text(0, 1.02, "Node size = weighted synchronization; color = unsupervised cluster", transform=axes[0].transAxes, color=PALETTE["muted"], fontsize=9)
    axes[0].axis("off")

    ranked_nodes = node_table.nlargest(12, "weighted_degree").sort_values("weighted_degree")
    bar_colors = [PALETTE["orange"] if value else PALETTE["blue"] for value in ranked_nodes["injected_coordination"]]
    axes[1].barh(ranked_nodes["account"], ranked_nodes["weighted_degree"], color=bar_colors)
    polish_axis(axes[1], "Weighted degree surfaces dense synchronizers", "Orange marks injected examples used only for evaluation", "Weighted synchronized-post count", "")
    fig.suptitle("Coordinated activity · graph ML and review ranking", fontsize=16, fontweight="bold", x=0.01, ha="left")

    injected_cluster_counts = node_table[node_table["injected_coordination"] == 1]["spectral_cluster"].value_counts()
    print(node_table.groupby("spectral_cluster").agg(accounts=("account", "count"), mean_weighted_degree=("weighted_degree", "mean"), injected_examples=("injected_coordination", "sum")).round(2).to_string())
    print("\\nAnalyst takeaways:")
    print(f"- The four injected accounts concentrate most in spectral cluster {int(injected_cluster_counts.idxmax())}.")
    print("- Timing and content synchronization create review leads; they do not establish common control, identity, or intent.")
    print("- Source-specific posting rates and reshare semantics are essential before operational interpretation.")
    """
)


ENHANCEMENT_CODE = {
    "01_domain_infrastructure_correlation.ipynb": binary_classification(
        "infrastructure",
        "simulated_review_label",
        ["domain_age_days", "rare_tld", "privacy_service"],
        "Domain infrastructure correlation",
        "domain_age_days",
        "rare_tld",
        prelude='infrastructure["simulated_review_label"] = ((infrastructure["domain_age_days"] < 365) & ((infrastructure["rare_tld"] == 1) | (infrastructure["privacy_service"] == 1))).astype(int)',
    ),
    "02_certificate_transparency_patterns.ipynb": CERTIFICATE_CLUSTERING,
    "03_passive_dns_flux_detection.ipynb": binary_classification(
        "domain_behavior",
        "simulated_flux",
        ["mean_ips", "max_countries", "median_ttl", "total_changes", "flux_score"],
        "Passive DNS flux detection",
        "mean_ips",
        "total_changes",
        prelude='domain_behavior["simulated_flux"] = domain_behavior["domain"].isin(["service-02.test", "service-07.test", "service-11.test"]).astype(int)',
    ),
    "04_social_coordination_detection.ipynb": SOCIAL_GRAPH,
    "05_public_document_metadata.ipynb": DOCUMENT_ANOMALY,
    "06_image_geolocation_confidence.ipynb": surrogate_regression(
        "image_evidence",
        "confidence_score",
        ["landmark_match", "signage_match", "terrain_match", "sun_consistency", "time_context_match", "metadata_conflict"],
        "Image geolocation confidence",
        "landmark_match",
        "signage_match",
    ),
    "07_privacy_preserving_entity_resolution.ipynb": binary_classification(
        "candidate_pairs",
        "known_match",
        ["username_similarity", "avatar_hash_match", "bio_token_overlap", "location_consistency"],
        "Privacy-preserving entity resolution",
        "username_similarity",
        "bio_token_overlap",
    ),
    "08_news_narrative_trends.ipynb": binary_classification(
        "daily",
        "simulated_surge",
        ["volume", "source_diversity", "volume_zscore", "diversity_ratio"],
        "News narrative trend analysis",
        "volume",
        "source_diversity",
        prelude='daily["simulated_surge"] = ((daily["topic"] == "cloud-risk") & daily["day"].between(20, 23)).astype(int)',
    ),
    "09_web_exposure_profiling.ipynb": surrogate_regression(
        "assets",
        "exposure_score",
        ["tls_age_days", "missing_security_headers", "login_surface", "end_of_life_technology", "public_admin_path"],
        "Public web exposure profiling",
        "tls_age_days",
        "missing_security_headers",
    ),
    "10_incident_timeline_fusion.ipynb": surrogate_regression(
        "timeline",
        "corroboration_score",
        ["reports", "source_types", "evidence_weight", "contradictions"],
        "Incident timeline fusion",
        "reports",
        "contradictions",
    ),
}


def enhancement_cells(filename: str, markdown, code) -> list[dict]:
    if filename not in ENHANCEMENT_CODE:
        raise KeyError(f"No enhancement registered for {filename}")
    return [
        markdown(
            """
            ## Visual Insights & ML Extension

            This section adds a polished visual story and a project-appropriate machine-learning extension while preserving the original transparent score or aggregation. Supervised labels are synthetic evaluation aids; unsupervised clusters and anomalies are review leads only.

            **Interpretation boundary:** these results do not prove identity, ownership, intent, attribution, or location. Real use requires lawful authority, source provenance, independent corroboration, and retention controls.
            """
        ),
        code(VISUAL_SETUP + "\n" + ENHANCEMENT_CODE[filename]),
    ]
