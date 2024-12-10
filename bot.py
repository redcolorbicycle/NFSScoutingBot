import discord
from discord.ext import commands
from commands import setup_commands
import psycopg2
from urllib.parse import urlparse
import os

#source ~/.bash_profile    

# Define intents
intents = discord.Intents.default()  # Default intents include basic events
intents.message_content = True       # Allows the bot to read message content

# Initialize the bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

DATABASE_URL = os.getenv("DATABASE_URL")
result = urlparse(DATABASE_URL)
connection = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.load_extension("commands.club_commands")
bot.load_extension("commands.player_commands")


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))