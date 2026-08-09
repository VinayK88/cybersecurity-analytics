# OSINT Analytics

Ten Jupyter notebook projects for ethical open-source intelligence analysis. The notebooks use deterministic synthetic data that resembles public-source records without collecting personal information or making network requests.

## Projects

| # | Notebook | Project | Main technique |
|---|---|---|---|
| 1 | `01_domain_infrastructure_correlation.ipynb` | Domain infrastructure correlation | Shared-hosting pivots and risk ranking |
| 2 | `02_certificate_transparency_patterns.ipynb` | Certificate transparency patterns | Certificate reuse clustering |
| 3 | `03_passive_dns_flux_detection.ipynb` | Passive DNS flux detection | Behavioral scoring and aggregation |
| 4 | `04_social_coordination_detection.ipynb` | Coordinated activity detection | Time-content pair matching |
| 5 | `05_public_document_metadata.ipynb` | Public document metadata analysis | Metadata grouping and hygiene checks |
| 6 | `06_image_geolocation_confidence.ipynb` | Image geolocation confidence | Multi-signal evidence scoring |
| 7 | `07_privacy_preserving_entity_resolution.ipynb` | Privacy-preserving entity resolution | Candidate-pair linkage scoring |
| 8 | `08_news_narrative_trends.ipynb` | News narrative trend analysis | Volume, diversity, and anomaly detection |
| 9 | `09_web_exposure_profiling.ipynb` | Web exposure profiling | Explainable risk scoring |
| 10 | `10_incident_timeline_fusion.ipynb` | Incident timeline fusion | Reliability-weighted evidence aggregation |

## Safety and scope

- No live scraping, authentication, tracking, or enrichment APIs.
- No real people, accounts, domains, locations, or sensitive identifiers.
- Outputs are analytical demonstrations, not attribution claims.
- Real investigations should document source terms, collection authority, provenance, uncertainty, and data-retention limits.

## Run and validate

Install the repository dependencies, open a notebook in JupyterLab, and run all cells. To rebuild and execute this folder:

```bash
python osint-analytics/build_notebooks.py
python osint-analytics/validate_notebooks.py
```
