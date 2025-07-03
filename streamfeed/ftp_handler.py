from urllib.parse import urlparse, unquote
import ftplib
import io

from typing import Tuple


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
