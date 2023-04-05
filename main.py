from discord.ext import commands
from discord import Intents, Message, Embed
import discord
import aiohttp
import dotenv
import asyncio
import os
import pprint
import urllib.request
import cv2
import numpy as np
from io import BytesIO

dotenv.load_dotenv()
pp = pprint.PrettyPrinter(indent=4)
bot = commands.Bot(command_prefix=".", intents=Intents.all())
base_url = "https://misskey.io/api"
headers = {"Content-Type": "application/json"}

def get_opencv_img_from_buffer(buffer, flags):
    bytes_as_np_array = np.frombuffer(buffer.read(), dtype=np.uint8)
    return cv2.imdecode(bytes_as_np_array, flags)

def get_opencv_img_from_url(url, flags):
    req = urllib.request.Request(url)
    return get_opencv_img_from_buffer(urllib.request.urlopen(req), flags)

def mosaic(src, ratio=0.1):
    small = cv2.resize(src, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_NEAREST)
    return cv2.resize(small, src.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)

def get_images(note):
    images = []
    for i in range(len(note["files"])):
        images.append([note["files"][i]["url"], note["files"][i]["isSensitive"]])
    return images

def get_author_icon(note):
    return note["user"]["avatarUrl"]

def get_text(note):
    return note["text"]

def get_name(note):
    return f"{note['user']['name']}@{note['user']['username']}"

def get_user_name(note):
    return note["user"]["username"]

async def get_note(note_id):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://misskey.io/api/notes/show", json={"i": os.getenv("misskeytoken"), "noteId": note_id}) as resp:
            return await resp.json(content_type="application/json")


class Button(discord.ui.Button):
    def __init__(self, images):
        self.images = []
        for image in images:
            req = urllib.request.Request(image[0])
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
            self.images.append(discord.File(BytesIO(urllib.request.urlopen(req).read()), filename="SPOILER_image.png"))
        super().__init__(style=discord.ButtonStyle.primary, label="ImageShow")

    async def callback(self, inter: discord.Interaction):
        await inter.response.send_message(files=self.images, ephemeral=True)


@bot.listen()
async def on_message(message: Message):
    is_sensitive = False
    if "https://misskey.io/notes/" in message.content:
        note = await get_note(message.content[message.content.rfind('/') + 1:])
        print(message.content[message.content.rfind('/') + 1:])
        print(note)
        images = get_images(note)
        embed = Embed(title="リンク展開", description=get_text(note))
        embed.set_author(name=get_name(note), url=f"https://misskey.io/@{get_user_name(note)}", icon_url=get_author_icon(note))
        if images:
            for image in images:
                if image[1]:
                    is_sensitive = True
                    break

            if is_sensitive:
                image = mosaic(get_opencv_img_from_url(get_author_icon(note), cv2.IMREAD_UNCHANGED))
                file = discord.File(BytesIO(image), filename="image.png")
                embed.set_image(url="attachment://image.png")
                embed.add_field(name="ノートに含まれている画像に閲覧注意タグがついていたため、画像を表示しませんでした。\n表示したい場合は、下の画像ボタンを押してください。")

                view = discord.ui.View(timeout=None)
                view.add_item(Button(images))
                await message.channel.send(
                    embed=embed, view=view, file=file
                )
        else:
            await message.channel.send(
                embed=embed
            )

bot.run(token=os.getenv("bottoken"))
