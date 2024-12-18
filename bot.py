import discord
from discord.ext import commands
import psycopg2
import asyncio
from urllib.parse import urlparse
import os

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

# Initialize the bots
bot1 = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)
bot2 = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
result = urlparse(DATABASE_URL)
connection = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port,
)

bot1.connection = connection
bot2.connection = connection

@bot1.event
async def on_ready():
    print(f"Logged in as {bot1.user}")

@bot2.event
async def on_ready():
    print(f"Logged in as {bot2.user}")

# Load extensions (cogs)
async def load_extensions(bot):
    try:
        if bot == bot1:
            await bot.load_extension("bot_commands.player_commands")
            await bot.load_extension("bot_commands.club_commands")
            await bot.load_extension("bot_commands.stevie_commands")
        elif bot == bot2:
            await bot.load_extension("bot_commands.misc_commands")
            await bot.load_extension("bot_commands.server_commands")
            await bot.load_extension("bot_commands.notice_scraper")
    except Exception as e:
        print(f"Failed to load extension for {bot.user}: {e}")

# Run the bots in parallel
async def main():
    # Load extensions for both bots
    await asyncio.gather(load_extensions(bot1), load_extensions(bot2))

    # Start both bots
    await asyncio.gather(
        bot1.start(os.getenv("DISCORD_BOT_TOKEN")),
        bot2.start(os.getenv("DISCORD_BOT_TOKEN_2")),
    )

if __name__ == "__main__":
    asyncio.run(main())
