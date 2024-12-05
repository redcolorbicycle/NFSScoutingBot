import discord
from discord.ext import commands
from database import get_connection
from commands import setup_commands
from dotenv import load_dotenv
import os

load_dotenv()
# Define intents
intents = discord.Intents.default()  # Default intents include basic events
intents.message_content = True       # Allows the bot to read message content

# Initialize the bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

connection = get_connection()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

setup_commands(bot, connection)


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))