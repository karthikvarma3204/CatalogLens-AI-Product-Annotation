"""CatalogLens: human-in-the-loop e-commerce annotation and quality review."""
import csv
import io
import json
from pathlib import Path
import streamlit as st
from cataloglens.core import CATEGORIES, audit, duplicate_candidates, agreement

st.set_page_config(page_title="CatalogLens | Product Intelligence Lab", page_icon="🔎", layout="wide")
st.title("🔎 CatalogLens")
st.caption("Human-in-the-loop product labeling • quality evidence • reviewer agreement")
st.info("Portfolio demonstration using synthetic products. Rule-based flags are suggestions, not ground truth.")

sample_path = Path(__file__).parent / "data" / "synthetic_catalog.json"
sample = json.loads(sample_path.read_text(encoding="utf-8"))
file = st.file_uploader("Optional: upload a product CSV (id,title,description,category,price,currency,brand)", type="csv")
if file:
    try:
        items = list(csv.DictReader(io.StringIO(file.getvalue().decode("utf-8-sig"))))
        if not items or not {"id", "title"}.issubset(items[0]):
            st.error("CSV must contain id and title columns.")
            st.stop()
    except (UnicodeError, csv.Error) as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()
else:
    items = sample

if "labels" not in st.session_state:
    st.session_state.labels = []

issues = {str(p.get("id")): audit(p) for p in items}
duplicates = duplicate_candidates(items)
col1, col2, col3 = st.columns(3)
col1.metric("Products", len(items))
col2.metric("Flagged records", sum(bool(v) for v in issues.values()))
col3.metric("Possible duplicate pairs", len(duplicates))

review_tab, quality_tab, agreement_tab, guide_tab = st.tabs(["Labeling workbench", "Quality audit", "Reviewer agreement", "Annotation guide"])
with review_tab:
    options = {f"{p.get('id')} · {p.get('title')}": p for p in items}
    selected = st.selectbox("Select a product", list(options))
    product = options[selected]
    st.json(product)
    if issues.get(str(product.get("id"))):
        st.warning("Audit flags: " + "; ".join(x["reason"] for x in issues[str(product.get("id"))]))
    with st.form("annotation"):
        reviewer = st.text_input("Reviewer ID", value="reviewer-1")
        label = st.selectbox("Verified category", sorted(CATEGORIES))
        quality = st.selectbox("Listing quality", ["acceptable", "needs_correction", "insufficient_evidence"])
        confidence = st.slider("Confidence", 1, 5, 3)
        evidence = st.text_area("Evidence and correction rationale", placeholder="Reference the product fields supporting your decision")
        submitted = st.form_submit_button("Save annotation")
        if submitted:
            if not reviewer.strip() or not evidence.strip():
                st.error("Reviewer ID and evidence are required.")
            else:
                st.session_state.labels.append({"item_id": str(product.get("id")), "reviewer": reviewer.strip(), "label": label, "quality": quality, "confidence": confidence, "evidence": evidence.strip()})
                st.success("Annotation saved for this session.")
    if st.session_state.labels:
        st.dataframe(st.session_state.labels, use_container_width=True)
        st.download_button("Export annotations (JSON)", json.dumps(st.session_state.labels, indent=2), file_name="cataloglens_annotations.json", mime="application/json")
with quality_tab:
    st.subheader("Explainable quality flags")
    st.dataframe([{"id": k, "flag": f["code"], "field": f["field"], "evidence": f["reason"]} for k, fs in issues.items() for f in fs], use_container_width=True)
    st.subheader("Duplicate review queue")
    st.dataframe(duplicates, use_container_width=True)
    st.caption("Similarity is a candidate-generation heuristic; verify variants and packaging before merging.")
with agreement_tab:
    st.subheader("Inter-reviewer agreement")
    result = agreement(st.session_state.labels)
    st.json(result)
    st.caption("Unanimous agreement is descriptive, not Cohen's kappa; compare two or more reviewers on the same item.")
with guide_tab:
    st.markdown("""### Annotation protocol
1. Read title, description, brand, and category; do not infer missing product details.
2. Select the most defensible taxonomy category. Use **other** if none fits.
3. Mark **needs_correction** when data is inconsistent or inaccurate; mark **insufficient_evidence** when the source cannot support a decision.
4. Cite exact product fields in the evidence note; avoid assumptions.
5. Review duplicate candidates manually, including size, variant, and packaging differences.
6. A second reviewer should independently label the same item before adjudication.

**Limitations:** Synthetic catalog, no production integrations, no learned classifier, session-only annotation storage. Uploaded data stays within the running Streamlit session; do not upload sensitive information to an untrusted deployment.
""")
