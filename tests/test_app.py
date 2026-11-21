from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_dashboard_renders_and_has_accessible_review_controls():
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert not app.exception
    assert any("Review a product" in item.value for item in app.markdown)
    assert any(select.label == "Product queue" for select in app.selectbox)
    assert any(uploader.label == "Import product catalog" for uploader in app.get("file_uploader"))


def test_reviewer_form_requires_reviewer_and_evidence():
    app = AppTest.from_file(APP, default_timeout=15).run()
    app.text_input[0].set_value("")
    app.text_area[0].set_value("")
    app.button[0].click().run()
    assert any("Reviewer ID and evidence are required" in item.value for item in app.error)

