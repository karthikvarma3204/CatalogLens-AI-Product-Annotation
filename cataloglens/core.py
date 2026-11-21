"""Deterministic product-data quality checks and annotation agreement metrics."""
import re
from difflib import SequenceMatcher

CATEGORIES = {"electronics", "clothing", "home", "grocery", "beauty", "sports", "other"}
REQUIRED = ("id", "title", "description", "category", "price", "currency", "brand")

def normalize(value):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(value).casefold())).strip()

def audit(item):
    """Return evidence-backed flags; never silently overwrite source values."""
    flags = []
    for field in REQUIRED:
        if not str(item.get(field, "")).strip():
            flags.append({"code": "missing_field", "field": field, "reason": f"Missing {field}"})
    try:
        price = float(item.get("price", ""))
        if not (price > 0 and price < float("inf")):
            flags.append({"code": "invalid_price", "field": "price", "reason": "Price must be positive"})
    except (TypeError, ValueError):
        if str(item.get("price", "")).strip():
            flags.append({"code": "invalid_price", "field": "price", "reason": "Price must be numeric"})
    category = normalize(item.get("category", ""))
    if category and category not in CATEGORIES:
        flags.append({"code": "unknown_category", "field": "category", "reason": "Category not in controlled taxonomy"})
    title, desc = normalize(item.get("title", "")), normalize(item.get("description", ""))
    if title and desc and title == desc:
        flags.append({"code": "low_information", "field": "description", "reason": "Description repeats title verbatim"})
    return flags

def duplicate_candidates(items, threshold=0.87):
    """Surface possible duplicates for human review, not automatic deletion."""
    pairs = []
    for i, left in enumerate(items):
        for right in items[i + 1:]:
            if normalize(left.get("brand", "")) != normalize(right.get("brand", "")):
                continue
            if not normalize(left.get("brand", "")):
                continue
            score = SequenceMatcher(None, normalize(left.get("title", "")), normalize(right.get("title", ""))).ratio()
            if score >= threshold:
                pairs.append({"left": left["id"], "right": right["id"], "similarity": round(score, 3)})
    return pairs

def agreement(rows):
    """Compare one current decision per reviewer and expose adjudication status."""
    groups = {}
    legacy_count = {}
    adjudicated = set()
    for row in rows:
        if row.get("adjudicated"):
            adjudicated.add(row["item_id"])
            continue
        reviewer = row.get("reviewer")
        if reviewer is None:
            index = legacy_count.get(row["item_id"], 0) + 1
            legacy_count[row["item_id"]] = index
            reviewer = f"legacy-{index}"
        reviewer = str(reviewer).strip().casefold()
        if not reviewer:
            continue
        groups.setdefault(row["item_id"], {})[reviewer] = row
    compared = {key: list(reviewers.values()) for key, reviewers in groups.items() if len(reviewers) >= 2}
    if not compared:
        return {"items_compared": 0, "unanimous_agreement": None, "quality_agreement": None, "disagreements": [], "quality_disagreements": [], "adjudicated": sorted(adjudicated)}
    labels_agree = {key: len({row["label"] for row in rows}) == 1 for key, rows in compared.items()}
    quality_agree = {key: len({row.get("quality") for row in rows}) == 1 for key, rows in compared.items()}
    return {
        "items_compared": len(compared),
        "unanimous_agreement": round(sum(labels_agree.values()) / len(compared), 3),
        "quality_agreement": round(sum(quality_agree.values()) / len(compared), 3),
        "disagreements": sorted(key for key, agree in labels_agree.items() if not agree),
        "quality_disagreements": sorted(key for key, agree in quality_agree.items() if not agree),
        "adjudicated": sorted(adjudicated),
    }

