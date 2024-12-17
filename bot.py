import discord
from discord.ext import commands
import psycopg2
import asyncio
from urllib.parse import urlparse
import os

#source ~/.bash_profile    f

# Define intents
intents = discord.Intents.default()  # Default intents include basic events
intents.message_content = True       # Allows the bot to read message content
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True 

# Initialize the bot with intents
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive = True)

DATABASE_URL = os.getenv("DATABASE_URL")
result = urlparse(DATABASE_URL)
connection = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)

bot.connection = connection

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Load extensions (cogs)
async def load_extensions():
    try:
        await bot.load_extension("bot_commands.player_commands")
        await bot.load_extension("bot_commands.club_commands")
        await bot.load_extension("bot_commands.misc_commands")
        await bot.load_extension("bot_commands.server_commands")
    except Exception as e:
        print(f"Failed to load extension: {e}")

# Run the bot
async def main():
    await load_extensions()
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())