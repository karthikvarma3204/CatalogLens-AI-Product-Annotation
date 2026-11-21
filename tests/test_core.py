from cataloglens.core import audit, duplicate_candidates, agreement, normalize

def test_normalize():
    assert normalize("  Hi,  WORLD! ") == "hi world"

def test_missing_fields_and_invalid_price():
    flags = audit({"id": "1", "title": "Thing", "price": "-1"})
    assert any(x["code"] == "missing_field" for x in flags)
    assert any(x["code"] == "invalid_price" for x in flags)

def test_unknown_category_and_repeated_description():
    flags = audit({"id":"1","title":"Red Mug","description":"Red Mug","category":"Kitchenware","price":12,"currency":"USD","brand":"A"})
    assert {x["code"] for x in flags} == {"unknown_category", "low_information"}

def test_valid_record():
    assert audit({"id":"1","title":"Mug","description":"Stoneware cup","category":"home","price":12,"currency":"USD","brand":"A"}) == []

def test_duplicate_candidates_same_brand():
    items = [{"id":"a","title":"Wireless Earbuds X2","brand":"N"},{"id":"b","title":"Wireless Earbuds X2","brand":"N"},{"id":"c","title":"Wireless Earbuds X2","brand":"Other"}]
    assert duplicate_candidates(items) == [{"left":"a","right":"b","similarity":1.0}]

def test_agreement():
    rows = [{"item_id":"1","label":"home"},{"item_id":"1","label":"home"},{"item_id":"2","label":"home"},{"item_id":"2","label":"other"}]
    assert agreement(rows) == {"items_compared":2,"unanimous_agreement":0.5,"disagreements":["2"]}

def test_no_agreement_yet():
    assert agreement([{"item_id":"1","label":"home"}])["unanimous_agreement"] is None
