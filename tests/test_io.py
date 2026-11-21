import pytest

from cataloglens.io import CatalogValidationError, dataset_fingerprint, parse_catalog_csv


def test_parse_catalog_csv_trims_headers_and_values():
    assert parse_catalog_csv(b" id , title ,description\n 1 , Mug , Stoneware\n") == [
        {"id": "1", "title": "Mug", "description": "Stoneware"}
    ]


@pytest.mark.parametrize("content, message", [
    (b"id,title\n1,Mug\n1,Cup\n", "Duplicate product ID"),
    (b"id,title,title\n1,Mug,Cup\n", "duplicate column"),
    (b"id,title\n1\n", "fewer fields"),
    (b"id,title\n1,Mug,extra\n", "more fields"),
    (b"id,title\n,Mug\n", "no product ID"),
    (b"id,title\n\n", "no product records"),
    (b"id,title\n1,\"unterminated\n", "Malformed CSV"),
    (b"id\xff,title\n1,Mug\n", "UTF-8"),
    (b"title\nMug\n", "missing required"),
])
def test_invalid_csv_is_rejected(content, message):
    with pytest.raises(CatalogValidationError, match=message):
        parse_catalog_csv(content)


def test_dataset_fingerprint_depends_on_content_not_name_or_size():
    assert dataset_fingerprint([{"id": "1", "title": "Mug"}]) != dataset_fingerprint([{"id": "2", "title": "Cup"}])
    assert dataset_fingerprint([{"id": "1", "title": "Mug"}]) == dataset_fingerprint([{"title": "Mug", "id": "1"}])

