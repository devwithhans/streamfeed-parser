# StreamFeed Parser

[![PyPI version](https://img.shields.io/pypi/v/streamfeed-parser.svg)](https://pypi.org/project/streamfeed-parser/)
[![Python versions](https://img.shields.io/pypi/pyversions/streamfeed-parser.svg)](https://pypi.org/project/streamfeed-parser/)
[![License](https://img.shields.io/github/license/devwithhans/streamfeed-parser.svg)](https://github.com/devwithhans/streamfeed-parser/blob/main/LICENSE)

A lightweight streaming parser for CSV and XML feeds over HTTP/FTP with automatic compression handling. Designed to efficiently process large data feeds without loading the entire file into memory.

## Features

- **Memory-efficient streaming approach** - process gigabytes of data with minimal memory usage
- **Multiple format support** - seamlessly handle both CSV and XML feed formats
- **Automatic detection** - intelligently detects file formats and compression types
- **Multi-protocol support** - works with HTTP, HTTPS, and FTP protocols
- **Compression handling** - supports ZIP, GZIP, and BZ2 compressed files
- **Data transformation** - expand fields with multiple values into separate records

## Installation

```bash
pip install streamfeed-parser
```

## Quick Start

```python
from streamfeed import stream_feed, preview_feed

# Preview the first 10 rows from a feed
preview_data = preview_feed('https://example.com/large-feed.csv', limit_rows=10)
print(preview_data)

# Stream and process a large feed without memory constraints
for record in stream_feed('https://example.com/large-feed.csv'):
    # Process each record individually
    print(record)
```

## Detailed Usage

### Streaming Feeds

The main function for streaming data is `stream_feed`:

```python
from streamfeed import stream_feed

# Stream a CSV feed
for record in stream_feed('https://example.com/products.csv'):
    print(record)  # Record is a dictionary with column names as keys

# Stream an XML feed (default item tag is 'product')
for record in stream_feed('https://example.com/products.xml'):
    print(record)  # Record is a dictionary with XML elements as keys
```

### Preview Feeds

To preview the first few records without processing the entire feed:

```python
from streamfeed import preview_feed

# Get the first 100 records (default)
preview_data = preview_feed('https://example.com/large-feed.csv')

# Customize the number of records
preview_data = preview_feed('https://example.com/large-feed.csv', limit_rows=10)
```

### Feed Logic Configuration

You can customize how feeds are processed with the `feed_logic` parameter:

```python
from streamfeed import stream_feed

# Specify the XML item tag for XML feeds
feed_logic = {
    'xml_item_tag': 'item'  # Default is 'product'
}

for record in stream_feed('https://example.com/feed.xml', feed_logic=feed_logic):
    print(record)

# Explode comma-separated values into multiple records
feed_logic = {
    'explode_fields': ['size', 'color'],  # Fields to explode
    'divider': ','  # Character that separates values (default is ',')
}

# Input: {'id': '123', 'size': 'S,M,L', 'color': 'red,blue,green'}
# Output: Multiple records with each size-color combination
for record in stream_feed('https://example.com/feed.csv', feed_logic=feed_logic):
    print(record)
```

### FTP Support

The library handles FTP URLs seamlessly:

```python
from streamfeed import stream_feed

# Basic FTP
for record in stream_feed('ftp://example.com/path/to/feed.csv'):
    print(record)

# FTP with authentication (included in URL)
for record in stream_feed('ftp://username:password@example.com/feed.csv'):
    print(record)
```

### Compression Handling

The library automatically detects and handles compressed feeds:

```python
from streamfeed import stream_feed

# These will automatically be decompressed
for record in stream_feed('https://example.com/feed.csv.gz'):  # GZIP
    print(record)

for record in stream_feed('https://example.com/feed.csv.zip'):  # ZIP
    print(record)

for record in stream_feed('https://example.com/feed.xml.bz2'):  # BZ2
    print(record)
```

## Advanced Features

### Row Count Limiting

Limit the number of rows processed:

```python
from streamfeed import stream_feed

# Only process the first 1000 rows
for record in stream_feed('https://example.com/large-feed.csv', limit_rows=1000):
    print(record)
```

### Field Length Limiting

Limit the maximum length of fields to prevent memory issues:

```python
from streamfeed import stream_feed

# Limit each field to 10,000 characters
for record in stream_feed('https://example.com/feed.csv', max_field_length=10000):
    print(record)
```

## Low-Level Access

For more specialized needs, you can access the underlying functions:

```python
from streamfeed import detect_compression
from streamfeed import stream_csv_lines
from streamfeed import stream_xml_items_iterparse
from streamfeed import stream_from_ftp

# Example: Check compression type
compression = detect_compression('https://example.com/feed.csv.gz')
print(compression)  # 'gz'
```

## Error Handling

The library gracefully handles many common errors in feeds:

- Broken CSV lines (including quoted fields with newlines)
- Missing columns
- Inconsistent delimiters
- XML parsing errors

Errors are logged but processing continues when possible.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request to the [GitHub repository](https://github.com/devwithhans/streamfeed-parser).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms included in the [LICENSE](LICENSE) file.

## Author

Hans-Christian Bøge Pedersen - [devwithhans](https://github.com/devwithhans)
