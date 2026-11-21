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
        if float(item.get("price", "")) <= 0:
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
    """Observed agreement across item IDs with at least two independent labels."""
    groups = {}
    for row in rows:
        groups.setdefault(row["item_id"], []).append(row["label"])
    compared = [v for v in groups.values() if len(v) >= 2]
    if not compared:
        return {"items_compared": 0, "unanimous_agreement": None, "disagreements": []}
    unanimous = sum(len(set(labels)) == 1 for labels in compared)
    disagreements = [key for key, labels in groups.items() if len(labels) >= 2 and len(set(labels)) > 1]
    return {"items_compared": len(compared), "unanimous_agreement": round(unanimous / len(compared), 3), "disagreements": disagreements}
