"""Input validation and stable dataset identity helpers."""
import csv
import hashlib
import io
import json
import math


class CatalogValidationError(ValueError):
    """Raised when an imported catalog cannot be reviewed safely."""


def parse_catalog_csv(content, *, required=("id", "title")):
    """Parse CSV bytes and reject ambiguous, malformed, or unusable records."""
    try:
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else str(content)
    except UnicodeDecodeError as exc:
        raise CatalogValidationError("File must use UTF-8 encoding.") from exc
    if not text.strip():
        raise CatalogValidationError("CSV file is empty.")
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        headers = reader.fieldnames
        if not headers:
            raise CatalogValidationError("CSV header row is missing.")
        cleaned = [h.strip() if h is not None else "" for h in headers]
        if any(not h for h in cleaned):
            raise CatalogValidationError("CSV headers cannot be blank.")
        if len(set(cleaned)) != len(cleaned):
            raise CatalogValidationError("CSV contains duplicate column names.")
        reader.fieldnames = cleaned
        missing = set(required) - set(cleaned)
        if missing:
            raise CatalogValidationError("CSV is missing required column(s): " + ", ".join(sorted(missing)))
        records = []
        seen_ids = set()
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise CatalogValidationError(f"Record on line {line} has more fields than the header.")
            if any(value is None for value in row.values()):
                raise CatalogValidationError(f"Record on line {line} has fewer fields than the header.")
            record = {key: value.strip() for key, value in row.items()}
            if not any(record.values()):
                raise CatalogValidationError(f"Record on line {line} is blank.")
            item_id = record.get("id", "").strip()
            if not item_id:
                raise CatalogValidationError(f"Record on line {line} has no product ID.")
            if item_id in seen_ids:
                raise CatalogValidationError(f"Duplicate product ID {item_id!r} on line {line}.")
            seen_ids.add(item_id)
            records.append(record)
        if not records:
            raise CatalogValidationError("CSV has a header but no product records.")
        return records
    except csv.Error as exc:
        raise CatalogValidationError(f"Malformed CSV: {exc}") from exc


def dataset_fingerprint(items, *, source="upload"):
    """Hash canonical contents so annotations cannot cross different uploads."""
    payload = json.dumps(items, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256((source + "\0" + payload).encode("utf-8")).hexdigest()


def validate_record_shape(item):
    """Validate values used by the UI and audit code are finite and renderable."""
    if not isinstance(item, dict):
        raise CatalogValidationError("Every catalog record must be an object.")
    if "price" in item and str(item["price"]).strip():
        try:
            value = float(item["price"])
        except (TypeError, ValueError) as exc:
            raise CatalogValidationError(f"Product {item.get('id', '')!r} has a malformed price.") from exc
        if not math.isfinite(value):
            raise CatalogValidationError(f"Product {item.get('id', '')!r} has a non-finite price.")
    return item

