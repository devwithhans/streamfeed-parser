from streamfeed import stream_feed


def test_from_feed():
    feed_url = "ftp://rkp_4369604:xP62OSFTsvC7hs4AJiXMGgYM@aftp.linksynergy.com/53085_4369604_mp.xml.gz"

    result = list(stream_feed(feed_url, limit_rows=2))

    print(result)

    # assert len(result) == 2
    # assert result[0] == {"id": "1", "name": "Shirt"}
    # assert result[1] == {"id": "2", "name": "Pants"}


if __name__ == "__main__":
    test_from_feed()
