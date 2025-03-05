# Import standard library modules first to avoid any circular import issues
import gzip
import bz2
import zipfile

# Then import your package components
from .detect import detect_compression
from .csv_parser import stream_csv_lines
from .xml_parser import stream_xml_items_iterparse
from .ftp_handler import stream_from_ftp
from .feed_streamer import stream_feed, preview_feed

__all__ = [
    "detect_compression",
    "stream_csv_lines",
    "stream_xml_items_iterparse",
    "stream_from_ftp",
    "stream_feed",
    "preview_feed",
]
