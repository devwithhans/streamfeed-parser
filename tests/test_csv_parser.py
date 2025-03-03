import pytest
from streamfeed.csv_parser import stream_csv_lines


def test_stream_csv_lines():
    csv_data = iter(["name,age", "John,30", "Alice,25"])
    result = list(stream_csv_lines(csv_data, limit_rows=None, max_field_length=None))

    assert len(result) == 2
    assert result[0] == {"name": "John", "age": "30"}
    assert result[1] == {"name": "Alice", "age": "25"}
