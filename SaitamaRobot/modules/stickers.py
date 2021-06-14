#kang is ported from DaisyX full credits goes to them


import datetime
import io
import os
import math
import requests
import cloudscraper
from io import BytesIO
import urllib.request as urllib
from PIL import Image
from html import escape
from bs4 import BeautifulSoup as bs

from telethon import *
from telethon.errors.rpcerrorlist import StickersetInvalidError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import (
    DocumentAttributeSticker,
    InputStickerSetID,
    InputStickerSetShortName,
    MessageMediaPhoto,
)

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError, Update
from telegram.ext import run_async, CallbackContext
from telegram.utils.helpers import mention_html

from SaitamaRobot import bot
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.utils.telethonub import ubot
from SaitamaRobot.events import register as Eren
from SaitamaRobot import telethn as tbot

combot_stickers_url = "https://combot.org/telegram/stickers?q="


@run_async
def stickerid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", The sticker id you are replying is :\n <code>"
            + escape(msg.reply_to_message.sticker.file_id)
            + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", Please reply to sticker message to get id sticker",
            parse_mode=ParseMode.HTML,
        )


@run_async
def cb_sticker(update: Update, context: CallbackContext):
    msg = update.effective_message
    split = msg.text.split(" ", 1)
    if len(split) == 1:
        msg.reply_text("Provide some name to search for pack.")
        return

    scraper = cloudscraper.create_scraper()
    text = scraper.get(combot_stickers_url + split[1]).text
    soup = bs(text, "lxml")
    results = soup.find_all("a", {"class": "sticker-pack__btn"})
    titles = soup.find_all("div", "sticker-pack__title")
    if not results:
        msg.reply_text("No results found :(.")
        return
    reply = f"Stickers for *{split[1]}*:"
    for result, title in zip(results, titles):
        link = result["href"]
        reply += f"\n• [{title.get_text()}]({link})"
    msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

def getsticker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        new_file = bot.get_file(file_id)
        new_file.download("sticker.png")
        bot.send_document(chat_id, document=open("sticker.png", "rb"))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text(
            "Please reply to a sticker for me to upload its PNG."
        )


def is_it_animated_sticker(message):
    try:
        if message.media and message.media.document:
            mime_type = message.media.document.mime_type
            if "tgsticker" in mime_type:
                return True
            return False
        return False
    except BaseException:
        return False


def is_message_image(message):
    if message.media:
        if isinstance(message.media, MessageMediaPhoto):
            return True
        if message.media.document:
            if message.media.document.mime_type.split("/")[0] == "image":
                return True
        return False
    return False


async def silently_send_message(conv, text):
    await conv.send_message(text)
    response = await conv.get_response()
    await conv.mark_read(message=response)
    return response


async def stickerset_exists(conv, setname):
    try:
        await tbot(GetStickerSetRequest(InputStickerSetShortName(setname)))
        response = await silently_send_message(conv, "/addsticker")
        if response.text == "Invalid pack selected.":
            await silently_send_message(conv, "/cancel")
            return False
        await silently_send_message(conv, "/cancel")
        return True
    except StickersetInvalidError:
        return False


def resize_image(image, save_locaton):
    """Copyright Rhyse Simpson:
    https://github.com/skittles9823/SkittBot/blob/master/tg_bot/modules/stickers.py
    """
    im = Image.open(image)
    maxsize = (512, 512)
    if (im.width and im.height) < 512:
        size1 = im.width
        size2 = im.height
        if im.width > im.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = math.floor(size1new)
        size2new = math.floor(size2new)
        sizenew = (size1new, size2new)
        im = im.resize(sizenew)
    else:
        im.thumbnail(maxsize)
    im.save(save_locaton, "PNG")


def find_instance(items, class_or_tuple):
    for item in items:
        if isinstance(item, class_or_tuple):
            return item
    return None



DEFAULTUSER = "Eren"
FILLED_UP_DADDY = "Invalid pack selected."


async def get_sticker_emoji(event):
    reply_message = await event.get_reply_message()
    try:
        final_emoji = reply_message.media.document.attributes[1].alt
    except:
        final_emoji = "🌏"
    return final_emoji


@Eren(pattern="^/kang ?(.*)")
async def _(event):
    if not event.is_reply:
        await event.reply("I can Only Kang images and stickers mate")
        return
    reply_message = await event.get_reply_message()
    sticker_emoji = await get_sticker_emoji(event)
    input_str = event.pattern_match.group(1)
    if input_str:
        sticker_emoji = input_str
    user = await event.get_sender()
    if not user.first_name:
        user.first_name = user.id
    pack = 1
    userid = event.sender_id
    first_name = user.first_name
    packname = f"{first_name}'s Sticker Vol.{pack}"
    packshortname = f"Eren_stickers_{userid}"
    kanga = await event.reply("Hello, This Sticker Looks Noice. Mind if I steal it?")
    is_a_s = is_it_animated_sticker(reply_message)
    file_ext_ns_ion = "Stickers.png"
    file = await event.client.download_file(reply_message.media)
    uploaded_sticker = None
    if is_a_s:
        file_ext_ns_ion = "AnimatedSticker.tgs"
        uploaded_sticker = await ubot.upload_file(file, file_name=file_ext_ns_ion)
        packname = f"{first_name}'s Animated Sticker Vol.{pack}"
        packshortname = f"Eren_animated_{userid}"
    elif not is_message_image(reply_message):
        await kanga.edit("Oh no.. This Message type is invalid")
        return
    else:
        with BytesIO(file) as mem_file, BytesIO() as sticker:
            resize_image(mem_file, sticker)
            sticker.seek(0)
            uploaded_sticker = await ubot.upload_file(
                sticker, file_name=file_ext_ns_ion
            )

    await kanga.edit("Proccessing Stealing the sticker with blek mejik")

    async with ubot.conversation("@Stickers") as d_conv:
        now = datetime.datetime.now()
        dt = now + datetime.timedelta(minutes=1)
        if not await stickerset_exists(d_conv, packshortname):

            await silently_send_message(d_conv, "/cancel")
            if is_a_s:
                response = await silently_send_message(d_conv, "/newanimated")
            else:
                response = await silently_send_message(d_conv, "/newpack")
            if "Yay!" not in response.text:
                await tbot.edit_message(
                    kanga, f"**Error**! @Stickers replied: {response.text}"
                )
                return
            response = await silently_send_message(d_conv, packname)
            if not response.text.startswith("Alright!"):
                await tbot.edit_message(
                    kanga, f"**Error**! @Stickers replied: {response.text}"
                )
                return
            w = await d_conv.send_file(
                file=uploaded_sticker, allow_cache=False, force_document=True
            )
            response = await d_conv.get_response()
            if "Sorry" in response.text:
                await tbot.edit_message(
                    kanga, f"**Error**! @Stickers replied: {response.text}"
                )
                return
            await silently_send_message(d_conv, sticker_emoji)
            await silently_send_message(d_conv, "💫")
            await silently_send_message(d_conv, "/publish")
            response = await silently_send_message(d_conv, f"<{packname}>")
            await silently_send_message(d_conv, "/skip")
            response = await silently_send_message(d_conv, packshortname)
            if response.text == "Sorry, this short name is already taken.":
                await tbot.edit_message(
                    kanga, f"**Error**! @Stickers replied: {response.text}"
                )
                return
        else:
            await silently_send_message(d_conv, "/cancel")
            await silently_send_message(d_conv, "/addsticker")            
            await silently_send_message(d_conv, packshortname)            
            await d_conv.send_file(
                file=uploaded_sticker, allow_cache=False, force_document=True
            )
            response = await d_conv.get_response()
            if response.text == FILLED_UP_DADDY:
                while response.text == FILLED_UP_DADDY:
                    pack += 1
                    prevv = int(pack) - 1
                    packname = f"{first_name}'s Sticker Vol.{pack}"
                    packshortname = f"Vol_{pack}_with_{userid}"

                    if not await stickerset_exists(d_conv, packshortname):
                        await tbot.edit_message(
                            kanga,
                            "**Pack No. **"
                            + str(prevv)
                            + "** is full! Making a new Pack, Vol. **"
                            + str(pack),
                        )
                        if is_a_s:
                            response = await silently_send_message(
                                d_conv, "/newanimated"
                            )
                        else:
                            response = await silently_send_message(d_conv, "/newpack")
                        if "Yay!" not in response.text:
                            await tbot.edit_message(
                                kanga, f"**Error**! @Stickers replied: {response.text}"
                            )
                            return
                        response = await silently_send_message(d_conv, packname)
                        if not response.text.startswith("Alright!"):
                            await tbot.edit_message(
                                kanga, f"**Error**! @Stickers replied: {response.text}"
                            )
                            return
                        w = await d_conv.send_file(
                            file=uploaded_sticker,
                            allow_cache=False,
                            force_document=True,
                        )
                        response = await d_conv.get_response()
                        if "Sorry" in response.text:
                            await tbot.edit_message(
                                kanga, f"**Error**! @Stickers replied: {response.text}"
                            )
                            return
                        await silently_send_message(d_conv, sticker_emoji)
                        await silently_send_message(d_conv, "💫")
                        await silently_send_message(d_conv, "/publish")
                        response = await silently_send_message(
                            bot_conv, f"<{packname}>"
                        )
                        await silently_send_message(d_conv, "/skip")
                        response = await silently_send_message(d_conv, packshortname)
                        if response.text == "Sorry, this short name is already taken.":
                            await tbot.edit_message(
                                kanga, f"**Error**! @Stickers replied: {response.text}"
                            )
                            return
                    else:
                        await tbot.edit_message(
                            kanga,
                            "**Pack No. **"
                            + str(prevv)
                            + "** is full! Switching to Vol. **"
                            + str(pack),
                        )
                        await silently_send_message(d_conv, "/addsticker")
                        await silently_send_message(d_conv, packshortname)
                        await d_conv.send_file(
                            file=uploaded_sticker,
                            allow_cache=False,
                            force_document=True,
                        )
                        response = await d_conv.get_response()
                        if "Sorry" in response.text:
                            await tbot.edit_message(
                                kanga, f"**Error**! @Stickers replied: {response.text}"
                            )
                            return
                        await silently_send_message(d_conv, sticker_emoji)
                        await silently_send_message(d_conv, "💫")
                        await silently_send_message(d_conv, "/done")
            else:
                if "Sorry" in response.text:
                    await tbot.edit_message(
                        kanga, f"**Error**! @Stickers replied: {response.text}"
                    )
                    return                
                await silently_send_message(d_conv, sticker_emoji)
                await silently_send_message(d_conv, "💫")
                await silently_send_message(d_conv, "/done")
    await kanga.edit("Almost Done stealing...")
    await kanga.edit(
        f" Successfully kanged the sticker to your [pack](t.me/addstickers/{packshortname})"
    )
    os.system("rm -rf  Stickers.png")
    os.system("rm -rf  AnimatedSticker.tgs")
    os.system("rm -rf *.webp")

__help__ = """
  /stickerid*:* reply to a sticker to me to tell you its file ID.
  /getsticker*:* reply to a sticker to me to upload its raw PNG file.
  /kang*:* reply to a sticker to add it to your pack.
  /stickers*:* Find stickers for given term on combot sticker catalogue
"""

__mod_name__ = "Stickers"
STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
STICKERS_HANDLER = DisableAbleCommandHandler("stickers", cb_sticker)

dispatcher.add_handler(STICKERS_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)

