from urllib.parse import urlparse
import ftplib
import io

from typing import Tuple


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


def stream_from_ftp(url: str) -> bytes:
    """
    Stream content from an FTP URL, returning the complete content as bytes.
    """
    host, username, password, path = parse_ftp_url(url)

    ftp = ftplib.FTP(host)
    try:
        if username:
            ftp.login(username, password)
        else:
            ftp.login()

        # Create a buffer to hold data chunks
        buffer = io.BytesIO()

        # RETR command is used for downloading files
        ftp.retrbinary(f"RETR {path}", buffer.write)

        # Return the complete content
        return buffer.getvalue()

    finally:
        try:
            ftp.quit()
        except:
            ftp.close()
