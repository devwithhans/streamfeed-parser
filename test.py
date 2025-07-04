import json
from streamfeed import stream_feed

# URL-encode the special characters in the password: [ becomes %5B and ] becomes %5D
feed = "https://adtraction.com/productfeed.htm?type=feed&format=CSV&encoding=UTF8&epi=0&zip=0&cdelim=tab&tdelim=singlequote&sd=1&sn=1&flat=0&apid=1923513464&asid=1915586344&gsh=1&pfid=2405&gt=0"
# feed = "ftp://ps-ftp_5972963:9NC[TN~u6v@products.impact.com/Ellos-DK/Ellos-DK-NEW-Variants_GOOGLE.xml.gz"
# feed = "ftp://rkp_4369604:xP62OSFTsvC7hs4AJiXMGgYM@aftp.linksynergy.com/53153_4369604_mp.xml.gz"
# feed = "ftp://rkp_4369604:xP62OSFTsvC7hs4AJiXMGgYM@aftp.linksynergy.com/53085_4369604_mp.xml.gz"

for item in stream_feed(
    url=feed,
    add_content_length=True,
    # feed_logic={"xml_item_tag": "item"},
):
    """"""
    print(json.dumps(item.dict(), indent=2))
