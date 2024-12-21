from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz  # For handling Singapore timezone
import discord

class BattleManager(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.sg_timezone = pytz.timezone("Asia/Singapore")
        self.schedule_endbattle.start()  # Start the scheduled task

    @commands.command()
    async def endbattle(self, ctx):
        """Ends the current battle."""

        try:
            with self.connection.cursor() as cursor:
                # Reset battle_date
                cursor.execute(
                    """
                    UPDATE battle_date SET id = 0;
                    """
                )
                self.connection.commit()

            await ctx.send("Battle ended, and the date lock has been reset.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


# Setup function for the cog
async def setup(bot):
    connection = bot.connection  # Retrieve the database connection
    await bot.add_cog(BattleManager(bot, connection))
