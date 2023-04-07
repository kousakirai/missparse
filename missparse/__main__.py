from discord.ext import commands
from discord import Intents
import dotenv
import os
import logging


dotenv.load_dotenv()
bot = commands.Bot(command_prefix=".", intents=Intents.all())

@bot.event
async def setup_hook():
    await bot.load_extension("missparse.cogs.parse")
    await bot.load_extension("jishaku")

bot.run(token=os.getenv("bottoken"), log_level=int(os.getenv("log_level")))
