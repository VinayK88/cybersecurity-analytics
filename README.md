# Cybersecurity Analytics & AI

Defensive Jupyter notebook projects covering security telemetry, machine learning, anomaly detection, graph analytics, and AI safety.

Every project:

- uses deterministic synthetic data;
- runs offline without credentials or external APIs;
- focuses on defensive detection, triage, or risk analysis;
- includes checks and practical next steps;
- avoids malware execution, exploitation, and real sensitive data.

## Projects

| # | Notebook | Project | Main technique |
|---|---|---|---|
| 1 | 01_authentication_anomaly_detection.ipynb | Authentication anomaly detection | Logistic regression from scratch |
| 2 | 02_network_traffic_clustering.ipynb | Network traffic behavior discovery | K-means clustering from scratch |
| 3 | 03_phishing_email_classifier.ipynb | Phishing email classification | Bag-of-words Naive Bayes |
| 4 | 04_dns_tunneling_detection.ipynb | DNS tunneling detection | Entropy features + logistic regression |
| 5 | 05_endpoint_process_anomaly_detection.ipynb | Endpoint process anomaly detection | Mahalanobis distance |
| 6 | 06_siem_alert_prioritization.ipynb | Explainable SIEM alert prioritization | Risk ranking + feature contributions |
| 7 | 07_threat_intelligence_graph_analytics.ipynb | Threat intelligence graph analytics | PageRank + evidence paths |
| 8 | 08_malware_static_feature_classification.ipynb | Safe malware metadata classification | Static PE-like features + logistic regression |
| 9 | 09_prompt_injection_detection.ipynb | Prompt-injection detection for RAG | Text classification |
| 10 | 10_cloud_iam_risk_scoring.ipynb | Cloud IAM risk scoring | Explainable risk modeling |

## OSINT analytics

The [`osint-analytics`](osint-analytics/) folder contains ten additional notebooks for ethical open-source intelligence analysis using synthetic, offline data.

## Run the notebooks

1. Create and activate a Python virtual environment.
2. Install dependencies with: pip install -r requirements.txt
3. Start JupyterLab with: jupyter lab
4. Open any notebook from the notebooks folder and run all cells.

The notebooks require only NumPy and Pandas for their analytics code. JupyterLab is included for interactive use.

## Rebuild and validate

- Rebuild notebooks: python scripts/build_notebooks.py
- Validate and execute all code cells: python scripts/validate_notebooks.py

The validator executes every code cell top-to-bottom in an isolated namespace and saves bounded text outputs into each notebook.

## Extending the projects

For each project, add a short architecture diagram, replace the synthetic generator with a documented public dataset, and record data-quality assumptions before presenting model performance as a real-world claim.
