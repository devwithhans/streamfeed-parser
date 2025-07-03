import queue
import threading
from urllib.parse import urlparse
import ftplib
import io

from typing import Generator, Tuple


def parse_ftp_url(url: str) -> Tuple[str, str, str, str]:
    """
    Parse an FTP URL into components: host, username, password, path.
    Format: ftp://[username:password@]host/path
    """
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path

    # Extract username and password if present
    username = password = ""
    if "@" in host:
        auth, host = host.split("@", 1)
        if ":" in auth:
            username, password = auth.split(":", 1)
        else:
            username = auth

    # Make sure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    return host, username, password, path


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
