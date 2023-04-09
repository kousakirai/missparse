from discord.ext import commands
from discord import app_commands
import discord
import aiohttp
import os
import io
import urllib
import numpy as np
import cv2
from PIL import Image
from datetime import datetime as dt
import re


class ImageShow(discord.ui.Button):
    def __init__(self, images):
        self.images = []
        for i, image in enumerate(images):
            self.images.append(discord.File(image["bytes"], filename=f"image_{i}.png", spoiler=True))
        super().__init__(style=discord.ButtonStyle.primary, label="ImageShow")

    async def callback(self, inter: discord.Interaction):
        await inter.response.send_message(files=self.images, ephemeral=True)

class ReplySource(discord.ui.Button):
    def __init__(self, reply_id):
        super().__init__(style=discord.ButtonStyle.link, label="リプライ元へ", url=f"http://misskey.io/notes/{reply_id}")

class OriginalNote(discord.ui.Button):
    def __init__(self, note_id):
        super().__init__(style=discord.ButtonStyle.link, label="元のノートへ", url=f"http://misskey.io/notes/{note_id}")

class NoteData:
    def __init__(self, note):
        self.note = note
        self.base_urls = ["https://misskey.io/api"]

    def _get_opencv_img_from_buffer(self, buffer):
        bytes_as_np_array = np.frombuffer(buffer.read(), dtype=np.uint8)
        return cv2.imdecode(bytes_as_np_array, cv2.IMREAD_UNCHANGED)

    def _mosaic(self, src, ratio=0.1):
        src = self._get_opencv_img_from_buffer(src)
        small = cv2.resize(src, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_NEAREST)
        big = cv2.resize(small, src.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
        frame = cv2.cvtColor(big, cv2.COLOR_BGR2RGB)
        png = io.BytesIO()
        image = Image.fromarray(frame)
        image.save(png, format="png")
        return png

    def _url_convert_to_bytes(self, url):
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
        bytes = urllib.request.urlopen(req).read()
        return io.BytesIO(bytes)

    def get_first_image(self):
        images = self.get_images()
        if images[0]["issensitive"]:
            return self._mosaic(images[0]["bytes"])
        else:
            return images[0]["bytes"]

    def get_images(self):
        images = []
        for file in self.note["files"]:
            bytes = self._url_convert_to_bytes(file["url"])
            images.append({"bytes": bytes, "issensitive": file["isSensitive"]})
        return images

    def get_avatar_url(self):
        return self.note["user"]["avatarUrl"]

    def get_message(self):
        return self.note["text"]

    def get_surface_name(self):
        return f"{self.note['user']['name']}@{self.note['user']['username']}"

    def get_user_name(self):
        return self.note["user"]["username"]

    def get_replyid(self):
        if self.note["replyId"] == "null":
            return None
        else:
            return self.note["replyId"]

    def get_created_at(self) -> dt:
        return dt.fromisoformat(self.note["createdAt"].replace('Z', '+00:00'))

    @classmethod
    async def create(cls, note_id):
        async with aiohttp.ClientSession() as session:
            async with session.post("https://misskey.io/api/notes/show", json={"i": os.getenv("misskeytoken"), "noteId": note_id}) as resp:
                note = await resp.json(content_type="application/json")
        notedata = cls(note)
        return notedata


class MissParser(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.urls = ["https://misskey.io"]
        self.context_menu = app_commands.ContextMenu(
            name="リンク展開",
            callback=self.from_message,
        )
        self.bot.tree.add_command(self.context_menu)

    async def _parse_note(self, url: str, found_url: str):
        note = await NoteData.create(found_url[found_url.rfind('/') + 1:])
        file = None
        embed = discord.Embed(
            title="リンク展開",
            description=note.get_message(),
            color=discord.Colour.green(),
            timestamp=note.get_created_at()
        )
        view = discord.ui.View(timeout=None)
        embed.set_footer(text="By Misskey")
        embed.set_author(name=note.get_surface_name(), url=f"{url}/@{note.get_user_name()}", icon_url=note.get_avatar_url())
        if note.get_images():
            file = discord.File(note.get_first_image(), filename="image.png")
            embed.set_image(url="attachment://image.png")
            view.add_item(ImageShow(note.get_images()))

        if note.get_replyid() is not None:
            view.add_item(ReplySource(note.get_replyid()))
        view.add_item(OriginalNote(found_url[found_url.rfind('/') + 1:]))
        return file, embed, view

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message):
        url_list = re.findall(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", message.content)
        for found_url in url_list:
            print(found_url)
            for url in self.urls:
                if url + "/notes/" in found_url:
                    file, embed, view = await self._parse_note(url, found_url)
                    if file:
                        await message.channel.send(
                            embed=embed,
                            file=file,
                            view=view
                        )
                    else:
                        await message.channel.send(
                            embed=embed,
                            view=view
                        )

    async def from_message(self, interaction: discord.Interaction, message: discord.Message):
        url_list = re.findall(r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+", message.content)
        for found_url in url_list:
            print(found_url)
            for url in self.urls:
                if url + "/notes/" in found_url:
                    file, embed, view = await self._parse_note(url, found_url)
                    if file:
                        await interaction.response.send_message(
                            embed=embed,
                            file=file,
                            view=view
                        )
                    else:
                        await interaction.response.send_message(
                            embed=embed,
                            view=view
                        )


async def setup(bot):
    return await bot.add_cog(MissParser(bot))
