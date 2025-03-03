import pytest
from streamfeed.transform import explode_rows


def test_explode_rows():
    rows = iter(
        [
            {"id": "1", "size": "S,M,L", "ean": "111,222,333"},
            {"id": "2", "size": "XL,XXL", "ean": "444,555"},
        ]
    )
    feed_logic = {"explode_fields": ["size", "ean"], "divider": ","}

    result = list(explode_rows(rows, feed_logic))

    assert len(result) == 5
    assert result[0] == {"id": "1", "size": "S", "ean": "111"}
    assert result[1] == {"id": "1", "size": "M", "ean": "222"}
    assert result[2] == {"id": "1", "size": "L", "ean": "333"}
    assert result[3] == {"id": "2", "size": "XL", "ean": "444"}
    assert result[4] == {"id": "2", "size": "XXL", "ean": "555"}
