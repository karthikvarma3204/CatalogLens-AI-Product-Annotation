"""CatalogLens: evidence-first product data annotation workbench."""
import hashlib
import json
import os
from pathlib import Path
import streamlit as st
from cataloglens.core import CATEGORIES, audit, duplicate_candidates, agreement
from cataloglens.io import CatalogValidationError, dataset_fingerprint, parse_catalog_csv, validate_record_shape
from cataloglens.storage import AnnotationStore, export_records

st.set_page_config(page_title="CatalogLens | Annotation Studio", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {--ink:#e8edf9;--muted:#9aaac7;--accent:#8b9fff;--edge:#293755;}
html,body,[class*="css"],[data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
[data-testid="stApp"] {background:radial-gradient(ellipse at 70% -20%,#202c59 0%,transparent 42%),#0c1222;color:var(--ink);}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:#101a2d;border-right:1px solid #25324b;}
.block-container {padding-top:2rem;padding-bottom:3rem;max-width:1320px;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.04em;}
h1 {font-size:3rem!important;}
h3 {font-size:1.35rem!important;}
p,small,label,[data-testid="stCaptionContainer"],.stMarkdown p {color:#d3dded;}
[data-testid="stSidebar"] * {color:#e1e9f7;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#c2cee0;}
[data-testid="stSidebar"] button {border-color:#546582;color:#eef3fc;}
[data-testid="stSidebar"] [data-testid="stFileUploader"] {background:#18243a;border:1px solid #3c4d6b;}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label {color:#e2eaf7!important;}
[data-testid="stDataFrame"] {border:1px solid #384967;border-radius:12px;}
[data-testid="stAlert"] p {color:inherit!important;}
[data-testid="stProgressBar"] > div {background:#8395ff;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#192540,#111a2d);border:1px solid #31405e;padding:1.2rem 1.3rem;border-radius:17px;}
[data-testid="stMetricLabel"] {color:#a8b8d2;}
[data-testid="stMetricValue"] {color:#f4f7ff;font-family:'Space Grotesk';}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.45rem;border-bottom:1px solid #30405c;}
[data-testid="stTabs"] button {border-radius:10px 10px 0 0;padding:.65rem 1.1rem;color:#b9c7e2;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#d8dfff;background:#243252;}
div[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#30405b!important;border-radius:18px!important;background:#131e32;}
div[data-testid="stForm"] {border:1px solid #30405b;border-radius:17px;background:#111c30;padding:1rem;}
div.stButton button[kind="primary"],div.stFormSubmitButton button {background:linear-gradient(90deg,#637dff,#8b69ef);border:0;color:white;border-radius:10px;font-weight:700;}
div.stButton button,div.stDownloadButton button {border-radius:10px;}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,textarea {background:#18243a!important;border-color:#394967!important;color:#eef2ff!important;}
[data-testid="stFileUploader"] {background:#111c30;border-radius:14px;padding:.4rem;}
[data-testid="stAlert"] {border-radius:12px;}
.hero {padding:1.5rem 1.8rem;border:1px solid #34446a;border-radius:20px;background:linear-gradient(115deg,#202e54,#17243d 60%,#141c34);margin-bottom:1.2rem;}
.eyebrow {font-size:.73rem;font-weight:800;letter-spacing:.16em;color:#9ab2ff;margin-bottom:.5rem;}
.hero-title {font-family:'Space Grotesk';font-size:2.65rem;font-weight:700;letter-spacing:-.06em;color:#fff;line-height:1.15;}
.hero-sub {color:#b4c4df;font-size:.96rem;margin-top:.65rem;max-width:800px;}
.pill {display:inline-block;background:#22385a;color:#c4dcff;border:1px solid #425c84;border-radius:30px;padding:.3rem .7rem;font-size:.75rem;font-weight:700;margin-top:.8rem;}
.section-kicker {font-size:.75rem;letter-spacing:.12em;color:#9eb3d7;font-weight:800;text-transform:uppercase;margin-bottom:.5rem;}
.product-title {font-family:'Space Grotesk';font-size:1.55rem;font-weight:700;color:#f5f7ff;margin:.35rem 0;}
.product-desc {color:#b8c8e3;line-height:1.7;}
.meta {font-size:.84rem;color:#9bacc9;margin-top:.6rem;}
.footer {color:#8697b4;font-size:.78rem;margin-top:2rem;padding-top:1rem;border-top:1px solid #2a3852;}
@media (max-width: 760px) {
  .block-container {padding:1rem .8rem 2rem;}
  h1 {font-size:2.15rem!important;}
  .hero {padding:1rem;border-radius:14px;}
  .hero-title {font-size:1.9rem;}
  [data-testid="stMetric"] {padding:.8rem;border-radius:12px;}
  [data-testid="stTabs"] [data-baseweb="tab-list"] {overflow-x:auto;flex-wrap:nowrap;}
  [data-testid="stTabs"] button {padding:.55rem .65rem;white-space:nowrap;}
}
</style>
""", unsafe_allow_html=True)

sample = json.loads((Path(__file__).parent / "data" / "synthetic_catalog.json").read_text(encoding="utf-8"))
with st.sidebar:
    st.markdown("### ◈ CatalogLens")
    st.caption("PRODUCT INTELLIGENCE LAB")
    st.divider()
    st.markdown("**Workspace**")
    st.caption("Human-in-the-loop review · v1.1")
    upload = st.file_uploader("Import product catalog", type="csv", help="CSV with id,title,description,category,price,currency,brand")
    st.caption("No file? Explore the built-in synthetic dataset.")
    st.divider()
    st.markdown("**Review principles**")
    st.caption("01  Evidence before assumptions")
    st.caption("02  Human decisions stay in control")
    st.caption("03  Flag uncertainty explicitly")
    st.divider()
    st.info("Demo only · Synthetic data · Session-based annotations")

if upload:
    try:
        items = [validate_record_shape(item) for item in parse_catalog_csv(upload.getvalue())]
    except CatalogValidationError as exc:
        st.error(str(exc))
        st.stop()
    dataset_key = dataset_fingerprint(items)
else:
    items = sample
    dataset_key = dataset_fingerprint(items, source="synthetic-demo-v1")

store = None
storage_path = os.environ.get("CATALOGLENS_DB_PATH", "").strip()
if storage_path:
    try:
        store = AnnotationStore(storage_path)
    except (OSError, ValueError) as exc:
        st.warning(f"Persistent annotation storage is unavailable: {exc}")
if store:
    persisted = store.list(dataset_key)
    st.session_state.labels = persisted
else:
    session_key = "labels_" + dataset_key
    st.session_state.setdefault(session_key, [])
    st.session_state.labels = st.session_state[session_key]

issues = {str(p.get("id")): audit(p) for p in items}
duplicates = duplicate_candidates(items)
reviewed = len({x["item_id"] for x in st.session_state.labels})
flagged = sum(bool(v) for v in issues.values())
st.markdown("""<div class="hero"><div class="eyebrow">AI DATA QUALITY · ANNOTATION STUDIO</div>
<div class="hero-title">Turn messy catalogs into<br>trusted product data.</div>
<div class="hero-sub">An evidence-first workspace for product labeling, explainable quality audits, duplicate triage, and independent reviewer agreement.</div>
<div class="pill">◉ Interactive portfolio prototype</div></div>""", unsafe_allow_html=True)

a,b,c,d=st.columns(4)
a.metric("Catalog items",len(items))
b.metric("Flagged listings",flagged)
c.metric("Duplicate candidates",len(duplicates))
d.metric("Reviewed items",f"{reviewed} / {len(items)}")
st.progress(reviewed/len(items) if items else 0, text="Annotation coverage")

tab1,tab2,tab3,tab4=st.tabs(["◈  Annotation studio","◇  Quality intelligence","◎  Reviewer agreement","▤  Protocol & methodology"])
with tab1:
    st.markdown("### Review a product")
    st.caption("Inspect source fields, select a verified label, and explain your judgment.")
    options = {f"{p.get('id')}  ·  {p.get('title')}":p for p in items}
    selection = st.selectbox("Product queue",list(options),label_visibility="collapsed")
    p = options[selection]
    left,right=st.columns([1.08,1],gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="section-kicker">SOURCE LISTING · '+str(p.get("id",""))+'</div>',unsafe_allow_html=True)
            st.markdown('<div class="product-title">'+str(p.get("title","")).replace("<","&lt;").replace(">","&gt;")+'</div>',unsafe_allow_html=True)
            st.markdown('<div class="product-desc">'+str(p.get("description") or "No description supplied").replace("<","&lt;").replace(">","&gt;")+'</div>',unsafe_allow_html=True)
            st.markdown(f'**{p.get("currency","")} {p.get("price","—")}**')
            st.markdown(f'**Brand:** {p.get("brand") or "Not provided"}')
            st.markdown(f'**Source category:** {p.get("category") or "Not provided"}')
            with st.expander("Inspect complete source JSON"):
                st.json(p)
        flags=issues.get(str(p.get("id")),[])
        if flags:
            st.warning(f"{len(flags)} audit flag(s): "+ "; ".join(f["reason"] for f in flags))
        else:
            st.success("No automated quality flags for this listing.")
    with right:
        with st.form("annotation",clear_on_submit=False):
            st.markdown("#### Reviewer decision")
            reviewer=st.text_input("Reviewer ID",value="reviewer-1")
            categories=sorted(CATEGORIES)
            proposed=str(p.get("category","")).casefold()
            default=categories.index(proposed) if proposed in categories else categories.index("other")
            label=st.selectbox("Verified category",categories,index=default)
            quality=st.selectbox("Listing quality",["acceptable","needs_correction","insufficient_evidence"])
            confidence=st.slider("Decision confidence",1,5,3)
            evidence=st.text_area("Evidence and correction rationale",placeholder="Example: Title and description identify wireless earbuds, supporting Electronics.",height=125)
            submitted=st.form_submit_button("Save review decision",width="stretch")
            if submitted:
                if not reviewer.strip() or not evidence.strip():
                    st.error("Reviewer ID and evidence are required.")
                else:
                    record={"item_id":str(p.get("id")),"reviewer":reviewer.strip(),"label":label,"quality":quality,"confidence":confidence,"evidence":evidence.strip()}
                    if store:
                        store.save(dataset_key, record)
                        st.session_state.labels = store.list(dataset_key)
                    else:
                        prior = [r for r in st.session_state.labels if not (r["item_id"] == record["item_id"] and r["reviewer"].casefold() == record["reviewer"].casefold())]
                        prior.append(record)
                        st.session_state.labels = prior
                        st.session_state["labels_" + dataset_key] = prior
                    st.success("Decision saved persistently." if store else "Decision saved in this session.")
    if st.session_state.labels:
        st.markdown("#### Saved decisions")
        st.dataframe(export_records(st.session_state.labels),width="stretch",hide_index=True)
        st.download_button("↓ Export annotation JSON",json.dumps(export_records(st.session_state.labels),indent=2),file_name="cataloglens_annotations.json",mime="application/json")
with tab2:
    st.markdown("### Quality intelligence")
    st.caption("Transparent, rule-based signals for human triage—not automated truth labels.")
    records=[{"Product":k,"Issue":f["code"].replace("_"," ").title(),"Field":f["field"],"Evidence":f["reason"]} for k,fs in issues.items() for f in fs]
    st.markdown("#### Listing integrity checks")
    if records: st.dataframe(records,width="stretch",hide_index=True)
    else: st.success("No issues detected by the configured rules.")
    st.markdown("#### Potential duplicate pairs")
    if duplicates:
        st.dataframe([{"Product A":x["left"],"Product B":x["right"],"Title similarity":x["similarity"]} for x in duplicates],width="stretch",hide_index=True)
    else: st.info("No duplicate candidates found at the current threshold.")
    st.caption("Brand-aware fuzzy title matching may include product variants. Review packaging and SKUs before merging.")
with tab3:
    st.markdown("### Independent review consistency")
    st.caption("Compare decisions on the same item across two or more reviewer IDs.")
    result=agreement(st.session_state.labels)
    # Tolerate a stale imported module during Streamlit Cloud hot reloads.
    result.setdefault("quality_agreement", None)
    result.setdefault("quality_disagreements", [])
    result.setdefault("adjudicated", [])
    x,y,z=st.columns(3)
    x.metric("Items with multiple reviews",result["items_compared"])
    y.metric("Unanimous agreement",f'{result["unanimous_agreement"]:.0%}' if result["unanimous_agreement"] is not None else "Not yet available")
    z.metric("Quality agreement",f'{result["quality_agreement"]:.0%}' if result["quality_agreement"] is not None else "Not yet available")
    if result["disagreements"]:
        st.warning("Adjudication required for: "+", ".join(result["disagreements"]))
    else:
        st.info("Create reviews for the same item under different reviewer IDs to compare labels.")
    adjudication_queue = sorted(set(result["disagreements"] + result["quality_disagreements"]))
    if adjudication_queue:
        item_id = st.selectbox("Item to adjudicate", adjudication_queue)
        adjudicator = st.text_input("Adjudicator ID", key="adjudicator_id")
        final_label = st.selectbox("Final category", sorted(CATEGORIES), key="final_category")
        final_quality = st.selectbox("Final quality decision", ["acceptable", "needs_correction", "insufficient_evidence"], key="final_quality")
        final_evidence = st.text_area("Adjudication rationale", key="final_evidence")
        if st.button("Save adjudication"):
            if not adjudicator.strip() or not final_evidence.strip():
                st.error("Adjudicator ID and rationale are required.")
            else:
                record={"item_id":item_id,"reviewer":adjudicator.strip(),"label":final_label,"quality":final_quality,"confidence":5,"evidence":final_evidence.strip(),"adjudicated":True,"adjudicator":adjudicator.strip()}
                if store:
                    store.adjudicate(dataset_key,item_id,record["adjudicator"],final_label,final_quality,record["evidence"])
                    st.session_state.labels=store.list(dataset_key)
                else:
                    st.session_state.labels.append(record)
                    st.session_state["labels_"+dataset_key]=st.session_state.labels
                st.success("Adjudication recorded.")
    elif result["items_compared"]:
        st.success("No unresolved category or quality disagreements.")
    st.caption("Agreement is item-level unanimous reviewer consensus, calculated once per reviewer. It is not Cohen's kappa or model accuracy.")
with tab4:
    st.markdown("### Annotation protocol")
    st.markdown("""**01 · Inspect** — Read title, description, brand, category and price. Do not infer missing details.

**02 · Classify** — Choose the best supported category from the controlled taxonomy; select *other* when necessary.

**03 · Assess** — Mark *needs_correction* for inaccurate data or *insufficient_evidence* when the listing cannot support a decision.

**04 · Justify** — Record concrete field-level evidence and a confidence rating.

**05 · Cross-check** — Independently label the same item with another reviewer ID and investigate disagreements.

**06 · Export** — Download annotation JSON before ending the session.

**Limitations:** Synthetic example catalog, deterministic QA heuristics, no trained model or production data integrations. Uploads are fingerprinted by content. Annotations stay in the session unless an operator configures `CATALOGLENS_DB_PATH` to a durable, private SQLite volume. Streamlit Community Cloud local storage is ephemeral; use an externally managed persistent volume for cross-restart retention.""")
st.markdown('<div class="footer">CATALOGLENS / PRODUCT INTELLIGENCE LAB · Built for transparent, human-led AI data quality evaluation · Portfolio demonstration</div>',unsafe_allow_html=True)

