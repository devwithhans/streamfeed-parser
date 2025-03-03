import pytest
from streamfeed.xml_parser import stream_xml_items_iterparse
import io


def test_stream_xml_items_iterparse():
    xml_content = io.BytesIO(
        b"""
    <root>
            <product><id>1</id><name>Shirt</name></product>
            <product><id>2</id><name>Pants</name></product>
        </root>
    """
    )

    result = list(
        stream_xml_items_iterparse(xml_content, item_tag="product", limit_rows=None)
    )

    assert len(result) == 2
    assert result[0] == {"id": "1", "name": "Shirt"}
    assert result[1] == {"id": "2", "name": "Pants"}
