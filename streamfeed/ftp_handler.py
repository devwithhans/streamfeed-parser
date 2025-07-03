import queue
import threading
from urllib.parse import unquote, urlparse
import ftplib
import io

from typing import Generator, Tuple

import io
import threading
import queue
import ftplib
from urllib.parse import urlparse


class FTPStream(io.RawIOBase):
    def __init__(self, generator):
        self._iterator = generator
        self._buffer = b""

    def readable(self):
        return True

    def readinto(self, b):
        # Fill buffer if empty
        while len(self._buffer) < len(b):
            try:
                self._buffer += next(self._iterator)
            except StopIteration:
                break

        output = self._buffer[: len(b)]
        self._buffer = self._buffer[len(b) :]

        n = len(output)
        b[:n] = output
        return n


class FTPResponse:
    def __init__(self, ftp_generator):
        self.raw = io.BufferedReader(FTPStream(ftp_generator))

    def close(self):
        self.raw.close()

    @property
    def content(self):
        return self.raw.read()


def parse_ftp_url(url: str) -> Tuple[str, str, str, str]:
    """
    Parse an FTP URL into components: host, username, password, path.
    Format: ftp://[username:password@]host/path
    """
    print("here")

    # Handle URLs with special characters in credentials
    # First, extract credentials manually to avoid urlparse issues with special chars
    if "://" in url:
        protocol, rest = url.split("://", 1)

        # Check if there are credentials
        if "@" in rest:
            credentials, host_path = rest.split("@", 1)

            # Split credentials into username and password
            if ":" in credentials:
                username, password = credentials.split(":", 1)
                # URL decode the password to handle special characters
                password = unquote(password)
            else:
                username = credentials
                password = ""

            # Parse the host and path part
            if "/" in host_path:
                host, path = host_path.split("/", 1)
                path = "/" + path
            else:
                host = host_path
                path = "/"
        else:
            # No credentials in URL
            username = password = ""
            host_path = rest

            if "/" in host_path:
                host, path = host_path.split("/", 1)
                path = "/" + path
            else:
                host = host_path
                path = "/"
    else:
        raise ValueError(f"Invalid FTP URL format: {url}")

    # Make sure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    return host, username, password, path


def get_ftp_size(url: str):
    host, username, password, path = parse_ftp_url(url)
    ftp = ftplib.FTP(host)
    ftp.login(username, password) if username else ftp.login()
    try:
        size = ftp.size(path)
    finally:
        ftp.quit()
    return size


def stream_from_ftp(url: str, blocksize: int = 8192) -> Generator[bytes, None, None]:
    host, username, password, path = parse_ftp_url(url)

    ftp = ftplib.FTP(host)
    ftp.login(username, password) if username else ftp.login()

    q = queue.Queue()

    def callback(data):
        q.put(data)

    def downloader():
        try:
            ftp.retrbinary(f"RETR {path}", callback, blocksize=blocksize)
        finally:
            q.put(None)  # Sentinel to signal end of stream

    t = threading.Thread(target=downloader)
    t.start()

    try:
        while True:
            chunk = q.get()
            if chunk is None:
                break
            yield chunk
    finally:
        ftp.quit()
