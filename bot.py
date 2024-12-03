import discord
from discord.ext import commands
from database import Database
from commands import Command
from config import DATABASE_URL, DISCORD_BOT_TOKEN

# Initialize the database
db = Database(DATABASE_URL)

# Define bot intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Add the commands cog
bot.add_cog(Command(bot, db))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
