import pytest
from unittest.mock import patch, MagicMock
from streamfeed.feed_streamer import stream_feed


@patch("streamfeed.feed_streamer.detect_compression_from_url_or_content")
@patch("requests.get")
def test_stream_feed(mock_get, mock_detect):
    # Mock compression detection to return None (no compression)
    mock_detect.return_value = None

    # Create a proper mock response
    mock_response = MagicMock()
    mock_response.iter_lines.return_value = iter(["name,age", "John,30", "Alice,25"])
    mock_response.status_code = 200
    mock_response.content = b"name,age\nJohn,30\nAlice,25"
    mock_get.return_value = mock_response

    url = "https://example.com/datafeed.csv"
    result = list(stream_feed(url, limit_rows=2))

    assert len(result) == 2
    assert result[0] == {"name": "John", "age": "30"}


# Alternative approach with more specific mocking
# @patch("streamfeed.feed_streamer.stream_csv_feed")
# @patch("requests.get")
# def test_stream_feed_with_mocked_csv(mock_get, mock_csv_feed):
#     # Setup mock response
#     mock_response = MagicMock()
#     mock_get.return_value = mock_response

#     # Mock the CSV feed function to return predetermined rows
#     mock_csv_feed.return_value = [
#         {"name": "John", "age": "30"},
#         {"name": "Alice", "age": "25"},
#     ]

#     url = "https://example.com/datafeed.csv"
#     result = list(stream_feed(url, limit_rows=2))

#     assert len(result) == 2
#     assert result[0] == {"name": "John", "age": "30"}
