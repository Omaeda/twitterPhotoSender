import logging
import os
import re
import urllib.request
from xml.dom.minidom import parseString

import pyrogram

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
app = pyrogram.Client("twitterUserbot", api_id=os.environ["API_ID"], api_hash=os.environ["API_HASH"])


@app.on_message(pyrogram.filters.outgoing & pyrogram.filters.regex(
    r"^.*twitter\.com\/(\w+)\/status\/(\d+).*$"))
async def _(client: pyrogram.Client, message: pyrogram.types.Message):
    img_urls = slow_mode(message)
    if not img_urls:
        return
    await message.delete()

    for url in img_urls:
        await client.send_photo(message.chat.id, url, message.text)

    logging.info("Processed: " + message.text)


def fast_mode(message):
    return [message.text]


def slow_mode(message):
    rss_url = "https://nitter.pussthecat.org/{}/rss".format(message.matches[0].group(1))
    request = urllib.request.Request(rss_url, headers={"Accept": "application/xml"})
    req = urllib.request.urlopen(request)
    if req.getcode() != 200:
        logging.warning("\nresponse error code: " + req.getcode() + "\nurl: " + rss_url)
        return
    xml = parseString(req.read().decode("utf-8"))
    img_urls = []
    for item in xml.getElementsByTagName("item"):
        guid = item.getElementsByTagName("guid")[0].firstChild.data
        if message.matches[0].group(2) in guid:
            description = item.getElementsByTagName("description")[0].firstChild.data
            img_urls = re.findall(r".*?<img src=\"([^\"]*).*?", description, re.DOTALL)
            for url in img_urls:
                if "video_thumb" in url or "card_img" in url:
                    img_urls.remove(url)
            break
    return img_urls


if __name__ == '__main__':
    logging.info("Userbot started...")
    app.run()
