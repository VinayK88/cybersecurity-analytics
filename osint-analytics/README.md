# OSINT Analytics

Ten Jupyter notebook projects for ethical open-source intelligence analysis. The notebooks use deterministic synthetic data that resembles public-source records without collecting personal information or making network requests. Every project now includes polished embedded visuals, analyst takeaways, and an ML extension chosen to fit the evidence type.

## Projects

| # | Notebook | Baseline | ML / visual extension |
|---|---|---|---|
| 1 | [Domain infrastructure correlation](notebooks/01_domain_infrastructure_correlation.ipynb) | Shared-hosting pivots | Classifier benchmark and feature importance |
| 2 | [Certificate transparency patterns](notebooks/02_certificate_transparency_patterns.ipynb) | Certificate reuse score | Silhouette-selected clustering and PCA |
| 3 | [Passive DNS flux detection](notebooks/03_passive_dns_flux_detection.ipynb) | Behavioral aggregation | Held-out model comparison and ranking lift |
| 4 | [Coordinated activity detection](notebooks/04_social_coordination_detection.ipynb) | Time-content matching | Weighted graph and spectral communities |
| 5 | [Public document metadata](notebooks/05_public_document_metadata.ipynb) | Metadata grouping | K-means plus Isolation Forest |
| 6 | [Image geolocation confidence](notebooks/06_image_geolocation_confidence.ipynb) | Multi-signal score | Evidence visuals and surrogate-model audit |
| 7 | [Privacy-preserving entity resolution](notebooks/07_privacy_preserving_entity_resolution.ipynb) | Candidate linkage score | Logistic-vs-forest held-out benchmark |
| 8 | [News narrative trends](notebooks/08_news_narrative_trends.ipynb) | Volume and diversity | Surge classifier and feature importance |
| 9 | [Web exposure profiling](notebooks/09_web_exposure_profiling.ipynb) | Explainable risk score | Distribution views and surrogate audit |
| 10 | [Incident timeline fusion](notebooks/10_incident_timeline_fusion.ipynb) | Reliability-weighted fusion | Evidence-space plots and sensitivity model |

## Safety and scope

- No live scraping, authentication, tracking, or enrichment APIs.
- No real people, accounts, domains, locations, or sensitive identifiers.
- Outputs are analytical demonstrations, not attribution claims.
- Real investigations should document source terms, collection authority, provenance, uncertainty, and data-retention limits.

## Run and validate

Install the repository dependencies, open a notebook in JupyterLab, and run all cells. The checked-in notebooks already contain executed tables, insights, and figures. To rebuild and execute this folder:

```bash
python osint-analytics/build_notebooks.py
python osint-analytics/validate_notebooks.py
```
