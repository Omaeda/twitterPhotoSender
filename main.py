import io
import logging
import os
import requests

import pyrogram
import snscrape.modules.twitter as sntwitter
from pyrogram.types import InputMediaPhoto

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("snscrape").setLevel(logging.WARNING)
app = pyrogram.Client("twitterUserbot", api_id=os.environ["API_ID"], api_hash=os.environ["API_HASH"])


@app.on_message(pyrogram.filters.outgoing & pyrogram.filters.regex(
    r"^.*twitter\.com\/(\w+)\/status\/(\d+).*$"))
async def _(client: pyrogram.Client, message: pyrogram.types.Message):
    tweet = next(sntwitter.TwitterTweetScraper(message.matches[0].group(2)).get_items())
    if tweet.media:
        album = []
        for media in tweet.media:
            if isinstance(media, sntwitter.Photo):
                if len(tweet.media) == 1:
                    album.append(media.fullUrl)
                else:
                    img = io.BytesIO(requests.get(media.fullUrl).content)
                    img.name = "image.jpg"
                    album.append(InputMediaPhoto(img, message.text if media == tweet.media[0] else ""))
        if not album:
            return
        if len(album) == 1:
            await client.send_photo(message.chat.id, album[0], message.text)
        else:
            await client.send_media_group(message.chat.id, album)
    await message.delete()
    logging.info("Processed: " + message.text)


if __name__ == '__main__':
    logging.info("Userbot started...")
    app.run()
