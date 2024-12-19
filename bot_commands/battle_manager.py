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

    async def cog_check(self, ctx):
        # Restrict to only the bot owner or the bot itself
        allowed_users = [self.bot.user.id, 355004588186796035]  # Replace YOUR_USER_ID with your Discord ID
        return ctx.author.id in allowed_users

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

    @tasks.loop(minutes=1)  # Check every minute
    async def schedule_endbattle(self):
        """Automatically ends the battle daily at Singapore time 3 PM."""
        now = datetime.now(self.sg_timezone)
        if now.hour == 15 and now.minute == 0:  # 3 PM Singapore time
            channel = discord.utils.get(self.bot.get_all_channels(), name="battle-logs-bot")
            if channel:
                try:
                    with self.connection.cursor() as cursor:
                        # Reset battle_date
                        cursor.execute(
                            """
                            UPDATE battle_date SET id = 0;
                            """
                        )
                        self.connection.commit()

                    await channel.send("Daily battle reset completed at 3 PM SG time.")
                except Exception as e:
                    self.connection.rollback()
                    await channel.send(f"An error occurred during the daily reset: {e}")

    @schedule_endbattle.before_loop
    async def before_schedule(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

# Setup function for the cog
async def setup(bot):
    connection = bot.connection  # Retrieve the database connection
    await bot.add_cog(BattleManager(bot, connection))
