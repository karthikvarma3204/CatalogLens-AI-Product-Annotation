from cataloglens.storage import AnnotationStore, export_records


def test_store_scopes_records_and_keeps_review_history():
    store = AnnotationStore(":memory:")
    first = {"item_id": "1", "reviewer": "a", "label": "home", "quality": "acceptable", "confidence": 3, "evidence": "title"}
    second = {**first, "reviewer": "b", "label": "other"}
    store.save("dataset-a", first)
    store.save("dataset-a", second)
    assert len(store.list("dataset-a")) == 2
    assert store.list("dataset-b") == []


def test_store_adjudication_is_append_only_and_exportable():
    store = AnnotationStore(":memory:")
    store.save("dataset", {"item_id": "x", "reviewer": "a", "label": "home", "quality": "acceptable", "confidence": 2, "evidence": "title"})
    store.adjudicate("dataset", "x", "lead", "home", "acceptable", "final rationale")
    rows = store.list("dataset")
    assert len(rows) == 2
    assert rows[1]["adjudicated"] == 1
    assert export_records(rows)[1]["adjudicator"] == "lead"

