import io
import urllib.request


def ftp_get(url):
    with urllib.request.urlopen(url) as response:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            yield io.BytesIO(chunk)

    print("DONW MTF")
