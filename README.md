# StreamFeed Parser

[![PyPI version](https://img.shields.io/pypi/v/streamfeed-parser.svg)](https://pypi.org/project/streamfeed-parser/)
[![Python versions](https://img.shields.io/pypi/pyversions/streamfeed-parser.svg)](https://pypi.org/project/streamfeed-parser/)
[![License](https://img.shields.io/github/license/yourusername/streamfeed-parser.svg)](https://github.com/yourusername/streamfeed-parser/blob/main/LICENSE)

A lightweight streaming parser for CSV and XML feeds over HTTP/FTP with automatic compression handling.

## Features

- Memory-efficient streaming approach for handling large files
- Support for CSV and XML feed formats
- Automatic compression detection and handling
- Works with both HTTP and FTP protocols
- Simple, intuitive API

## Installation

```bash
pip install streamfeed-parser
```

## Usage

### Parsing CSV Feeds

```python
from streamfeed import CSVFeedParser

# Initialize a parser for a CSV feed
parser = CSVFeedParser('https://example.com/large-data.csv.gz')

# Iterate through records
for record in parser.parse():
    print(record)  # Each record is a dictionary with column names as keys
```

### Parsing XML Feeds

```python
from streamfeed import XMLFeedParser

# Initialize a parser for an XML feed
parser = XMLFeedParser('ftp://example.com/feed.xml',
                       record_tag='item')  # Specify which tag represents a record

# Iterate through records
for record in parser.parse():
    print(record['title'])  # Access elements by their tag names
```

### Handling Authentication

```python
from streamfeed import CSVFeedParser

# HTTP Basic Authentication
parser = CSVFeedParser('https://example.com/secure/feed.csv',
                      auth=('username', 'password'))

# FTP Authentication
parser = CSVFeedParser('ftp://example.com/secure/feed.csv',
                      auth=('username', 'password'))
```

## Advanced Configuration

```python
from streamfeed import CSVFeedParser

parser = CSVFeedParser(
    'https://example.com/data.csv',
    delimiter=';',  # Custom delimiter (default is ',')
    encoding='latin-1',  # Custom encoding (default is utf-8)
    chunk_size=8192,  # Custom chunk size for streaming (default is 4096)
    skip_lines=1  # Skip header line
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms included in the [LICENSE](LICENSE) file.
