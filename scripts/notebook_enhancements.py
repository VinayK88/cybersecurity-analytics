from __future__ import annotations

import textwrap


VISUAL_SETUP = """
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = globals().get("SEED", 42)

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

def binary_model_comparison(features, labels):
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.28,
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
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=1,
        ),
    }
    rows = []
    probabilities = {}
    fitted = {}
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


def numeric_classification(
    frame: str,
    label: str,
    title: str,
    x_feature: str,
    y_feature: str,
) -> str:
    return clean(
        f"""
        model_frame = {frame}.copy()
        ml_features = model_frame.drop(columns=["{label}"]).select_dtypes(include=[np.number])
        ml_labels = model_frame["{label}"].to_numpy(int)

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), constrained_layout=True)
        for class_value, color, class_name in [
            (0, PALETTE["blue"], "Benign / lower risk"),
            (1, PALETTE["orange"], "Positive security outcome"),
        ]:
            subset = model_frame[model_frame["{label}"] == class_value]
            axes[0].scatter(
                subset["{x_feature}"], subset["{y_feature}"],
                s=22, alpha=0.48, color=color, edgecolors="none", label=class_name,
            )
        polish_axis(
            axes[0],
            "Where positive outcomes concentrate",
            "Synthetic observations; color encodes the simulated label",
            "{x_feature.replace('_', ' ').title()}",
            "{y_feature.replace('_', ' ').title()}",
        )
        axes[0].legend(frameon=False, fontsize=9)

        risk_bins = pd.qcut(model_frame["{x_feature}"], q=5, duplicates="drop")
        rate_by_bin = model_frame.groupby(risk_bins, observed=True)["{label}"].agg(["mean", "size"])
        axes[1].bar(
            range(len(rate_by_bin)), rate_by_bin["mean"],
            color=PALETTE["gold"], edgecolor=PALETTE["ink"], linewidth=0.4,
        )
        axes[1].set_xticks(range(len(rate_by_bin)), [f"Q{{index + 1}}" for index in range(len(rate_by_bin))])
        axes[1].set_ylim(0, max(0.05, rate_by_bin["mean"].max() * 1.2))
        polish_axis(
            axes[1],
            "Outcome rate rises across feature quantiles",
            "Bars show observed positive rate; quantiles keep group sizes comparable",
            "{x_feature.replace('_', ' ').title()} quantile",
            "Positive rate",
        )
        fig.suptitle("{title} · visual exploration", fontsize=16, fontweight="bold", x=0.01, ha="left")

        model_comparison, fitted_models, model_probabilities, comparison_labels = binary_model_comparison(
            ml_features, ml_labels
        )
        best_model_name = model_comparison["average_precision"].idxmax()
        best_probability = model_probabilities[best_model_name]
        review_count = max(1, int(len(best_probability) * 0.10))
        top_positions = np.argsort(best_probability)[-review_count:]
        comparison_labels_array = np.asarray(comparison_labels)
        base_rate = float(comparison_labels_array.mean())
        top_rate = float(comparison_labels_array[top_positions].mean())
        top_decile_lift = top_rate / max(base_rate, 1e-9)

        forest = fitted_models["Random forest"]
        feature_importance = pd.Series(
            forest.feature_importances_, index=ml_features.columns, name="importance"
        ).sort_values(ascending=False)

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
        metric_colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["pink"]]
        comparison_display = model_comparison.rename(columns={{
            "roc_auc": "ROC AUC",
            "average_precision": "Average precision",
            "f1_at_0_5": "F1 @ 0.50",
        }})
        comparison_display.plot(kind="bar", ax=axes[0], color=metric_colors, width=0.72)
        axes[0].set_ylim(0, 1.05)
        axes[0].tick_params(axis="x", rotation=0)
        axes[0].legend(frameon=False, ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14))
        polish_axis(
            axes[0],
            "Two model families, three detection views",
            "Held-out stratified test set; higher is better",
            "",
            "Score",
        )

        top_importance = feature_importance.head(7).sort_values()
        axes[1].barh(top_importance.index.str.replace("_", " "), top_importance.values, color=PALETTE["olive"])
        polish_axis(
            axes[1],
            "Random-forest feature importance",
            "Global split importance; association is not causation",
            "Relative importance",
            "",
        )
        fig.suptitle("{title} · ML comparison and explainability", fontsize=16, fontweight="bold", x=0.01, ha="left")

        print("Model comparison (held-out data):")
        print(model_comparison.round(3).to_string())
        print("\\nAnalyst takeaways:")
        print(f"- Best average precision: {{best_model_name}} ({{model_comparison.loc[best_model_name, 'average_precision']:.3f}}).")
        print(f"- The highest-scored 10% is {{top_decile_lift:.1f}}× denser in positives than the test-set baseline.")
        print(f"- Strongest random-forest driver: {{feature_importance.index[0].replace('_', ' ')}}.")
        print("- Treat these synthetic benchmarks as a workflow example; production thresholds require temporal validation and drift monitoring.")
        """
    )


def text_classification(frame: str, text_column: str, label: str, title: str) -> str:
    return clean(
        f"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB

        text_frame = {frame}.copy()
        text_frame["token_count"] = text_frame["{text_column}"].str.split().str.len()

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), constrained_layout=True)
        class_counts = text_frame["{label}"].value_counts().sort_index()
        axes[0].bar(["Benign", "Security-positive"], class_counts.values, color=[PALETTE["blue"], PALETTE["orange"]])
        polish_axis(axes[0], "Balanced synthetic corpus", "Class counts before the train/test split", "", "Messages")

        for class_value, color, class_name in [
            (0, PALETTE["blue"], "Benign"),
            (1, PALETTE["orange"], "Security-positive"),
        ]:
            axes[1].hist(
                text_frame.loc[text_frame["{label}"] == class_value, "token_count"],
                bins=np.arange(text_frame["token_count"].min(), text_frame["token_count"].max() + 2) - 0.5,
                alpha=0.55, color=color, label=class_name,
            )
        axes[1].legend(frameon=False)
        polish_axis(axes[1], "Length is not the primary signal", "Overlapping token-count distributions reduce shortcut learning", "Tokens per message", "Messages")
        fig.suptitle("{title} · corpus diagnostics", fontsize=16, fontweight="bold", x=0.01, ha="left")

        train_texts, test_texts, train_targets, test_targets = train_test_split(
            text_frame["{text_column}"],
            text_frame["{label}"],
            test_size=0.28,
            random_state=SEED,
            stratify=text_frame["{label}"],
        )
        tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        train_tfidf = tfidf.fit_transform(train_texts)
        test_tfidf = tfidf.transform(test_texts)
        text_models = {{
            "TF-IDF logistic": LogisticRegression(max_iter=1200, class_weight="balanced", random_state=SEED),
            "TF-IDF Naive Bayes": MultinomialNB(alpha=0.8),
        }}
        rows = []
        text_probabilities = {{}}
        for name, model in text_models.items():
            model.fit(train_tfidf, train_targets)
            probability = model.predict_proba(test_tfidf)[:, 1]
            prediction = (probability >= 0.5).astype(int)
            rows.append({{
                "model": name,
                "roc_auc": roc_auc_score(test_targets, probability),
                "average_precision": average_precision_score(test_targets, probability),
                "f1_at_0_5": f1_score(test_targets, prediction, zero_division=0),
            }})
            text_probabilities[name] = probability
        text_model_comparison = pd.DataFrame(rows).set_index("model")

        logistic_model = text_models["TF-IDF logistic"]
        feature_names_tfidf = np.asarray(tfidf.get_feature_names_out())
        positive_terms = pd.Series(
            logistic_model.coef_[0], index=feature_names_tfidf
        ).sort_values(ascending=False).head(10).sort_values()

        fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
        text_comparison_display = text_model_comparison.rename(columns={{
            "roc_auc": "ROC AUC",
            "average_precision": "Average precision",
            "f1_at_0_5": "F1 @ 0.50",
        }})
        text_comparison_display.plot(
            kind="bar", ax=axes[0], color=[PALETTE["blue"], PALETTE["gold"], PALETTE["pink"]], width=0.72
        )
        axes[0].set_ylim(0, 1.05)
        axes[0].tick_params(axis="x", rotation=0)
        axes[0].legend(frameon=False, ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14))
        polish_axis(axes[0], "Model comparison on held-out messages", "Higher is better; thresholded F1 uses 0.50", "", "Score")

        axes[1].barh(positive_terms.index, positive_terms.values, color=PALETTE["olive"])
        polish_axis(axes[1], "Highest-weight positive n-grams", "TF-IDF logistic coefficients support analyst review", "Coefficient", "")
        fig.suptitle("{title} · stronger text ML", fontsize=16, fontweight="bold", x=0.01, ha="left")

        best_text_model = text_model_comparison["average_precision"].idxmax()
        print("Model comparison (held-out data):")
        print(text_model_comparison.round(3).to_string())
        print("\\nAnalyst takeaways:")
        print(f"- Best average precision: {{best_text_model}} ({{text_model_comparison.loc[best_text_model, 'average_precision']:.3f}}).")
        print(f"- The vocabulary contains {{len(feature_names_tfidf):,}} reviewable unigram and bigram features.")
        print(f"- Highest positive n-gram: '{{positive_terms.index[-1]}}'.")
        print("- Validate on time-separated, adversarial, multilingual, and template-shifted examples before operational use.")
        """
    )


NETWORK_CLUSTERING = clean(
    """
    cluster_features = flows[["log_packets", "log_bytes", "log_destinations", "syn_ratio"]]
    cluster_scaled = StandardScaler().fit_transform(cluster_features)
    cluster_trials = []
    fitted_trials = {}
    for candidate_k in range(2, 8):
        candidate_model = KMeans(n_clusters=candidate_k, n_init=20, random_state=SEED)
        candidate_labels = candidate_model.fit_predict(cluster_scaled)
        cluster_trials.append({
            "clusters": candidate_k,
            "silhouette": silhouette_score(cluster_scaled, candidate_labels),
            "inertia": candidate_model.inertia_,
        })
        fitted_trials[candidate_k] = (candidate_model, candidate_labels)
    cluster_diagnostics = pd.DataFrame(cluster_trials)
    selected_k = int(cluster_diagnostics.loc[cluster_diagnostics["silhouette"].idxmax(), "clusters"])
    selected_model, selected_labels = fitted_trials[selected_k]
    projection = PCA(n_components=2, random_state=SEED).fit_transform(cluster_scaled)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    axes[0].plot(cluster_diagnostics["clusters"], cluster_diagnostics["silhouette"], marker="o", color=PALETTE["blue"], linewidth=2)
    axes[0].axvline(selected_k, color=PALETTE["gold"], linestyle="--", label=f"selected k={selected_k}")
    axes[0].legend(frameon=False)
    polish_axis(axes[0], "Silhouette selects a stable cluster count", "Candidate k values evaluated on standardized flow features", "Number of clusters", "Silhouette score")

    cluster_colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["orange"], PALETTE["olive"], PALETTE["pink"], PALETTE["muted"]]
    for cluster_id in range(selected_k):
        member = selected_labels == cluster_id
        axes[1].scatter(projection[member, 0], projection[member, 1], s=20, alpha=0.55, color=cluster_colors[cluster_id % len(cluster_colors)], label=f"Cluster {cluster_id}")
    axes[1].legend(frameon=False, ncol=2, fontsize=8)
    polish_axis(axes[1], "PCA view of learned traffic behaviors", "Two-dimensional view for interpretation; clustering used all four features", "Principal component 1", "Principal component 2")
    fig.suptitle("Network traffic clustering · model selection", fontsize=16, fontweight="bold", x=0.01, ha="left")

    selected_profiles = flows.assign(ml_cluster=selected_labels).groupby("ml_cluster")[["log_packets", "log_bytes", "log_destinations", "syn_ratio"]].mean()
    profile_z = (selected_profiles - cluster_features.mean()) / cluster_features.std()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    from matplotlib.colors import BoundaryNorm, ListedColormap
    profile_colors = ListedColormap(["#334155", "#64748B", "#F8FAFC", "#D4A72C", "#E76F51"])
    profile_norm = BoundaryNorm([-2.5, -1.0, -0.25, 0.25, 1.0, 2.5], profile_colors.N, clip=True)
    heatmap = axes[0].imshow(profile_z, cmap=profile_colors, norm=profile_norm, aspect="auto")
    axes[0].set_xticks(range(len(profile_z.columns)), profile_z.columns.str.replace("_", " "), rotation=25, ha="right")
    axes[0].set_yticks(range(len(profile_z)), [f"Cluster {value}" for value in profile_z.index])
    axes[0].set_title("Standardized cluster profiles", loc="left", pad=22)
    axes[0].text(0, 1.02, "Positive values sit above the portfolio average", transform=axes[0].transAxes, color=PALETTE["muted"], fontsize=9)
    colorbar = fig.colorbar(heatmap, ax=axes[0], ticks=[-1.75, -0.625, 0, 0.625, 1.75])
    colorbar.ax.set_yticklabels(["≤ -1", "-1 to -0.25", "near mean", "0.25 to 1", "≥ 1"])
    colorbar.set_label("Standard deviations")

    cluster_sizes = pd.Series(selected_labels).value_counts().sort_index()
    axes[1].bar(cluster_sizes.index.astype(str), cluster_sizes.values, color=cluster_colors[:len(cluster_sizes)])
    polish_axis(axes[1], "Cluster sizes remain visible", "Small clusters merit review but are not automatically malicious", "Cluster", "Flows")
    fig.suptitle("Network traffic clustering · behavioral profiles", fontsize=16, fontweight="bold", x=0.01, ha="left")

    scan_like_cluster = int(selected_profiles["syn_ratio"].idxmax())
    print(cluster_diagnostics.round(3).to_string(index=False))
    print("\\nAnalyst takeaways:")
    print(f"- Silhouette analysis selects {selected_k} clusters (score {cluster_diagnostics['silhouette'].max():.3f}).")
    print(f"- Cluster {scan_like_cluster} has the highest mean SYN ratio and is the best candidate for scan-behavior review.")
    print("- PCA is used only for visualization; the cluster model retains the full standardized feature space.")
    print("- Refit against time windows and segment by protocol before using cluster rarity as an alert.")
    """
)


ENDPOINT_ANOMALY = clean(
    """
    endpoint_features = process_events.drop(columns="suspicious").select_dtypes(include=[np.number])
    endpoint_labels = process_events["suspicious"].to_numpy(int)
    normal_features = endpoint_features[endpoint_labels == 0]
    endpoint_scaler = StandardScaler().fit(normal_features)
    endpoint_scaled = endpoint_scaler.transform(endpoint_features)
    normal_scaled = endpoint_scaler.transform(normal_features)

    isolation_model = IsolationForest(
        n_estimators=180,
        contamination=float(endpoint_labels.mean()),
        random_state=SEED,
        n_jobs=1,
    ).fit(normal_scaled)
    isolation_score = -isolation_model.score_samples(endpoint_scaled)
    mahalanobis_score = ranked_processes.sort_index()["anomaly_score"].to_numpy()
    anomaly_comparison = pd.DataFrame({
        "average_precision": [
            average_precision_score(endpoint_labels, mahalanobis_score),
            average_precision_score(endpoint_labels, isolation_score),
        ],
        "roc_auc": [
            roc_auc_score(endpoint_labels, mahalanobis_score),
            roc_auc_score(endpoint_labels, isolation_score),
        ],
    }, index=["Mahalanobis", "Isolation forest"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
    for class_value, color, name in [(0, PALETTE["blue"], "Routine"), (1, PALETTE["orange"], "Suspicious")]:
        subset = process_events[process_events["suspicious"] == class_value]
        axes[0].scatter(subset["command_length"], subset["network_connections"], s=22, alpha=0.48, color=color, edgecolors="none", label=name)
    axes[0].legend(frameon=False)
    polish_axis(axes[0], "Suspicious processes occupy a distinct region", "Synthetic process events; labels are shown only for evaluation", "Command length", "Network connections")

    anomaly_display = anomaly_comparison.rename(columns={
        "average_precision": "Average precision",
        "roc_auc": "ROC AUC",
    })
    anomaly_display.plot(kind="bar", ax=axes[1], color=[PALETTE["blue"], PALETTE["gold"]], width=0.72)
    axes[1].set_ylim(0, 1.05)
    axes[1].tick_params(axis="x", rotation=0)
    axes[1].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    polish_axis(axes[1], "Two unsupervised detectors compared", "Labels evaluate ranking quality; neither model trains on suspicious rows", "", "Score")
    fig.suptitle("Endpoint anomaly detection · visual and ML comparison", fontsize=16, fontweight="bold", x=0.01, ha="left")

    fig, ax = plt.subplots(figsize=(10.5, 4.8), constrained_layout=True)
    ax.hist(isolation_score[endpoint_labels == 0], bins=30, alpha=0.65, color=PALETTE["blue"], label="Routine")
    ax.hist(isolation_score[endpoint_labels == 1], bins=18, alpha=0.65, color=PALETTE["orange"], label="Suspicious")
    ax.legend(frameon=False)
    polish_axis(ax, "Isolation-forest scores separate the simulated populations", "Higher scores indicate behavior less consistent with the clean baseline", "Anomaly score", "Processes")

    best_detector = anomaly_comparison["average_precision"].idxmax()
    print(anomaly_comparison.round(3).to_string())
    print("\\nAnalyst takeaways:")
    print(f"- {best_detector} ranks the simulated suspicious processes best by average precision.")
    print(f"- Isolation forest improves on a single global-distance assumption by modeling nonlinear partitions across {endpoint_features.shape[1]} features.")
    print("- Production baselines should be segmented by host role and signed-software inventory to reduce false positives.")
    """
)


GRAPH_ANALYTICS = clean(
    """
    import networkx as nx

    graph = nx.Graph()
    graph.add_nodes_from(node_types)
    graph.add_edges_from((source, target) for source, target, _ in edges)
    graph_nodes = list(graph.nodes())
    adjacency_matrix = nx.to_numpy_array(graph, nodelist=graph_nodes)
    degrees = adjacency_matrix.sum(axis=1)
    inv_sqrt_degree = np.diag(1 / np.sqrt(np.maximum(degrees, 1)))
    normalized_laplacian = np.eye(len(graph_nodes)) - inv_sqrt_degree @ adjacency_matrix @ inv_sqrt_degree
    eigenvalues, eigenvectors = np.linalg.eigh(normalized_laplacian)
    graph_embedding = eigenvectors[:, 1:4]
    graph_clusters = KMeans(n_clusters=4, n_init=30, random_state=SEED).fit_predict(graph_embedding)
    graph_cluster_table = pd.DataFrame({
        "entity": graph_nodes,
        "type": [node_types[node] for node in graph_nodes],
        "spectral_cluster": graph_clusters,
        "pagerank": [centrality[node] for node in graph_nodes],
        "degree": degrees.astype(int),
    }).sort_values("pagerank", ascending=False)

    position = nx.spring_layout(graph, seed=SEED, k=0.85)
    graph_colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["orange"], PALETTE["olive"]]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)
    nx.draw_networkx_edges(graph, position, ax=axes[0], edge_color=PALETTE["grid"], width=1.4)
    nx.draw_networkx_nodes(
        graph,
        position,
        ax=axes[0],
        node_color=[graph_colors[value] for value in graph_clusters],
        node_size=[420 + 5000 * centrality[node] for node in graph_nodes],
        edgecolors=PALETTE["ink"],
        linewidths=0.5,
    )
    short_labels = {node: node.split(":", 1)[-1] for node in graph_nodes}
    nx.draw_networkx_labels(graph, position, labels=short_labels, ax=axes[0], font_size=7)
    axes[0].set_title("Spectral communities expose evidence neighborhoods", loc="left", pad=22)
    axes[0].text(0, 1.02, "Node size = PageRank; color = unsupervised graph cluster", transform=axes[0].transAxes, color=PALETTE["muted"], fontsize=9)
    axes[0].axis("off")

    for cluster_id, color in enumerate(graph_colors):
        subset = graph_cluster_table[graph_cluster_table["spectral_cluster"] == cluster_id]
        axes[1].scatter(subset["degree"], subset["pagerank"], s=80, alpha=0.78, color=color, label=f"Cluster {cluster_id}")
    for _, row in graph_cluster_table.head(4).iterrows():
        axes[1].annotate(row["entity"].split(":", 1)[-1], (row["degree"], row["pagerank"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    axes[1].legend(frameon=False)
    polish_axis(axes[1], "Centrality and connectivity agree on key pivots", "Annotations show the four highest-PageRank entities", "Degree", "PageRank")
    fig.suptitle("Threat-intelligence graph · spectral ML and centrality", fontsize=16, fontweight="bold", x=0.01, ha="left")

    cluster_summary = graph_cluster_table.groupby("spectral_cluster").agg(nodes=("entity", "count"), mean_pagerank=("pagerank", "mean"), entity_types=("type", "nunique"))
    print(cluster_summary.round(4).to_string())
    print("\\nAnalyst takeaways:")
    print(f"- Four spectral clusters summarize {len(graph_nodes)} entities without using node-type labels.")
    print(f"- {graph_cluster_table.iloc[0]['entity']} remains the strongest central pivot by PageRank.")
    print("- Community membership is an investigation aid, not evidence of common ownership or attribution.")
    """
)


ENHANCEMENT_CODE = {
    "01_authentication_anomaly_detection.ipynb": numeric_classification(
        "auth_events", "compromised", "Authentication anomaly detection", "source_reputation", "failed_attempts"
    ),
    "02_network_traffic_clustering.ipynb": NETWORK_CLUSTERING,
    "03_phishing_email_classifier.ipynb": text_classification(
        "email_data", "text", "phishing", "Phishing email classification"
    ),
    "04_dns_tunneling_detection.ipynb": numeric_classification(
        "dns_queries", "tunnel", "DNS tunneling detection", "entropy", "subdomain_length"
    ),
    "05_endpoint_process_anomaly_detection.ipynb": ENDPOINT_ANOMALY,
    "06_siem_alert_prioritization.ipynb": numeric_classification(
        "alerts", "confirmed_incident", "SIEM alert prioritization", "detection_confidence", "severity"
    ),
    "07_threat_intelligence_graph_analytics.ipynb": GRAPH_ANALYTICS,
    "08_malware_static_feature_classification.ipynb": numeric_classification(
        "static_features", "malicious", "Static malware-metadata classification", "file_entropy", "suspicious_imports"
    ),
    "09_prompt_injection_detection.ipynb": text_classification(
        "rag_data", "passage", "prompt_injection", "Prompt-injection detection"
    ),
    "10_cloud_iam_risk_scoring.ipynb": numeric_classification(
        "iam_principals", "confirmed_risky", "Cloud IAM risk scoring", "access_key_age_days", "anomalous_api_calls"
    ),
}


def enhancement_cells(filename: str, markdown, code) -> list[dict]:
    if filename not in ENHANCEMENT_CODE:
        raise KeyError(f"No enhancement registered for {filename}")
    return [
        markdown(
            """
            ## Visual Insights & ML Extension

            The original transparent method remains intact. This extension adds an explicit visual story, a stronger scikit-learn benchmark, and analyst-focused interpretation. All evaluation uses held-out or label-free synthetic examples as appropriate.

            **Reading the results:** model scores describe this generated dataset only. They are not production performance claims and should not replace temporal validation, calibration, drift checks, or human review.
            """
        ),
        code(VISUAL_SETUP + "\n" + ENHANCEMENT_CODE[filename]),
    ]
