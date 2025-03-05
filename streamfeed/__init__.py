from .detect import detect_compression
from .csv_parser import stream_csv_lines
from .xml_parser import stream_xml_items_iterparse
from .ftp_handler import ftp_get
from .feed_streamer import stream_feed, preview_feed

__all__ = [
    "detect_compression",
    "stream_csv_lines",
    "stream_xml_items_iterparse",
    "ftp_get",
    "stream_feed",
    "preview_feed",
]
