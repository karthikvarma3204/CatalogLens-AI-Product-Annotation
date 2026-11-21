# 🔎 CatalogLens — Human-in-the-Loop Product Intelligence Lab

A portfolio project demonstrating **e-commerce data labeling, product taxonomy review, data-quality auditing, duplicate detection, and inter-reviewer agreement**. Built as an explainable annotation workbench rather than a black-box classifier.

> **Project status:** Functional portfolio prototype. Synthetic data only. No claim of production-scale annotation or paid data-labeling experience.

## What makes it different

- **Evidence-first annotations:** each reviewer records category, quality decision, confidence, and justification.
- **Transparent QA rules:** missing fields, invalid prices, unknown categories, and low-information descriptions are surfaced with reasons.
- **Duplicate triage:** brand-aware fuzzy title matching generates a human review queue; it does not automatically merge listings.
- **Independent reviewer comparison:** compares category and quality decisions once per reviewer and highlights items needing adjudication.
- **Append-only decision history:** optional SQLite persistence keeps reviewer submissions and explicit final adjudications separate.
- **Exportable JSON annotations:** portable review results for later analysis.
- **Synthetic demo dataset:** includes intentional duplicate and quality issues; no personal or scraped customer data.
- **Automated tests:** pytest + GitHub Actions.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run tests: `python -m pytest -q`.

## Demo walkthrough

1. Open the **Labeling workbench** and select product P004 to see an invalid-price and repeated-description flag.
2. Enter a reviewer ID, category, quality decision, confidence, and a reason tied to source fields.
3. Save the annotation. Change reviewer ID and independently label the same item.
4. Inspect **Reviewer agreement** for agreement or disagreement; download annotation JSON.
5. Inspect **Quality audit** for flagged records and duplicate candidates P001/P002. Use **Reviewer agreement** to record an explicit adjudication when reviewers disagree.
6. Upload your own non-sensitive CSV with at least `id,title` headers to inspect another catalog.

## Data schema

| Field | Purpose |
|---|---|
| id | Stable product identifier |
| title, description | Source listing text |
| category | Proposed source taxonomy category |
| price, currency | Product pricing |
| brand | Duplicate-triage context |

The demo uses `electronics`, `clothing`, `home`, `grocery`, `beauty`, `sports`, `other` as controlled category labels. Unknown source categories are flagged, not silently converted.

## Design decisions and limitations

- Rule-based QA is deterministic and explainable, but cannot verify real-world product claims.
- Duplicate similarity does not establish identical SKUs; variants must be reviewed.
- Reviewer agreement is **unanimous agreement**, not Cohen's kappa or a model accuracy metric.
- Session-only storage by default. Configure `CATALOGLENS_DB_PATH` to use SQLite on a durable, private volume; submissions and adjudications are append-only and scoped by catalog content fingerprint.
- Streamlit Community Cloud's local filesystem is ephemeral across restarts. Use an external persistent volume or hosted database if annotations must survive app restarts; do not store SQLite on a temporary deployment filesystem.
- No user accounts, durable database, model training, external APIs, or production deployment.
- CSV content is processed in the running app; do not upload confidential data to third-party deployments.

## Roadmap

- [x] Optional SQLite annotation store with reviewer identity and audit trail
- [x] Reviewer disagreement and adjudication workflow
- [ ] Hierarchical taxonomy and configurable labeling guidelines
- [ ] Evaluation against human-reviewed gold labels (precision/recall by category)
- [ ] More rigorous duplicate matching with variant-aware features

## Tech

Python · Streamlit · pytest · GitHub Actions · CSV/JSON

## License

MIT License (see LICENSE).

