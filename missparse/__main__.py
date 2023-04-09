from discord.ext import commands
from discord import Intents, Object, Game, Status
import dotenv
import os


dotenv.load_dotenv("../.env")
bot = commands.Bot(command_prefix=".", intents=Intents.all())

@bot.event
async def setup_hook():
    bot.tree.copy_global_to(guild=Object(id=1069962727390457897))
    await bot.load_extension("missparse.cogs.parse")
    await bot.load_extension("jishaku")
    await bot.tree.sync()

@bot.event
async def on_ready():
    game = Game(f"{bot.guilds}鯖で稼働中")
    await bot.change_presence(status=Status.online, activity=game)

@bot.event
async def on_guild_join(guild):
    game = Game(f"{len(bot.guilds)}鯖で稼働中")
    await bot.change_presence(status=Status.online, activity=game)

bot.run(token=os.getenv("bottoken"), log_level=int(os.getenv("log_level")))
