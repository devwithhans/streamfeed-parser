import io
import queue
import threading
from ftplib import FTP


class FTPStreamWrapper(io.RawIOBase):
    """
    A file-like wrapper around FTPResponse.iter_content().
    This allows things like gzip.GzipFile(fileobj=...) to read from .raw.
    """

    def __init__(self, ftp_response: "FTPResponse"):
        self._iter = ftp_response.iter_content()
        self._buffer = b""
        self._closed = False

    def close(self):
        self._closed = True

    def read(self, size=-1):
        """
        Read up to `size` bytes. If size == -1, read all data until EOF.
        """
        if self._closed:
            return b""

        # If size == -1, read the entire stream
        if size == -1:
            chunks = [self._buffer]
            self._buffer = b""
            # Drain the generator
            for chunk in self._iter:
                chunks.append(chunk)
            return b"".join(chunks)

        # Otherwise, read exactly 'size' bytes (or until EOF)
        out = []
        while len(b"".join(out)) < size:
            # If we have enough in the buffer, pull from there
            needed = size - len(b"".join(out))
            if self._buffer:
                out.append(self._buffer[:needed])
                self._buffer = self._buffer[needed:]
            else:
                try:
                    chunk = next(self._iter)
                    self._buffer += chunk
                except StopIteration:
                    break
        return b"".join(out)

    def readable(self):
        return True


class FTPResponse:
    """
    A minimal, streaming-friendly class that mimics part of requests.Response,
    allowing .iter_content() and .iter_lines() for data over FTP,
    and now provides .raw so it works in places that expect a file-like object.
    """

    def __init__(self, url: str, chunk_size: int = 8192):
        self.url = url
        self.chunk_size = chunk_size

        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._download_in_thread, daemon=True)
        self._thread.start()

        # Provide a file-like object wrapper around iter_content
        self._raw = FTPStreamWrapper(self)

    @property
    def raw(self):
        """
        Return a file-like object so code like `gzip.GzipFile(fileobj=response.raw)` works.
        """
        return self._raw

    def _download_in_thread(self):
        try:
            hostname, user, passwd, path = _parse_ftp_url(self.url)
            with FTP(hostname) as ftp:
                ftp.login(user, passwd)

                def callback(data):
                    self._queue.put(data)

                ftp.retrbinary(f"RETR {path}", callback, blocksize=self.chunk_size)
        except Exception as e:
            self._queue.put(e)
        finally:
            self._queue.put(None)

    def iter_content(self, chunk_size: int = 8192):
        while True:
            chunk = self._queue.get()
            if chunk is None:
                break
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    def iter_lines(self, chunk_size: int = 8192):
        pending = b""
        for chunk in self.iter_content(chunk_size=chunk_size):
            if chunk:
                pending += chunk
                lines = pending.split(b"\n")
                for line in lines[:-1]:
                    yield line
                pending = lines[-1]
        if pending:
            yield pending

    def raise_for_status(self):
        pass

    def close(self):
        """
        Close the underlying file-like object, if desired.
        """
        self._raw.close()
        self._stop_event.set()


def _parse_ftp_url(url):
    # Remove ftp://
    no_scheme = url.replace("ftp://", "")
    # Split out user:password@host/path
    parts = no_scheme.split("/", 1)
    user_host = parts[0]
    path = parts[1] if len(parts) > 1 else ""

    if "@" in user_host:
        userpass, hostname = user_host.split("@", 1)
        if ":" in userpass:
            username, password = userpass.split(":", 1)
        else:
            username, password = userpass, ""
    else:
        hostname = user_host
        username, password = "", ""

    return hostname, username, password, path
