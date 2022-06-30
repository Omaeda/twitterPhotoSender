import io
import logging
import os
import re
import urllib.request
from xml.dom.minidom import parseString

import pyrogram
from pyrogram.errors import MediaEmpty
from pyrogram.types import InputMediaPhoto

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
app = pyrogram.Client("twitterUserbot", api_id=os.environ["API_ID"], api_hash=os.environ["API_HASH"])


@app.on_message(pyrogram.filters.outgoing & pyrogram.filters.regex(
    r"^.*twitter\.com\/(\w+)\/status\/(\d+).*$"))
async def _(client: pyrogram.Client, message: pyrogram.types.Message):
    send_as_album = ":a" in message.text
    if send_as_album:
        try:
            img_urls = slow_mode(message)
            if len(img_urls) == 1:
                await client.send_photo(message.chat.id, img_urls[0], message.text)
            else:
                album = []
                for url in img_urls:
                    img = io.BytesIO(urllib.request.urlopen(url).read())
                    img.name = "image.jpg"
                    album.append(InputMediaPhoto(img, message.text if url == img_urls[0] else ""))
                await client.send_media_group(message.chat.id, album)
        except MediaEmpty:
            return
    else:
        try:
            await client.send_photo(message.chat.id, message.text, message.text)
        except MediaEmpty:
            return

    await message.delete()

    logging.info("Processed: " + message.text)


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
            break
    for url in img_urls:
        if "video_thumb" in url or "card_img" in url:
            img_urls.remove(url)
    return img_urls


if __name__ == '__main__':
    logging.info("Userbot started...")
    app.run()
