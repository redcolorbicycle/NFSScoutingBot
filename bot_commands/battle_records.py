from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord

class BattleRecords(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    async def cog_check(self, ctx):
        """
        Restrict commands to users with specific roles.
        Only users with the specified roles can call the commands.
        """
        # List of allowed roles
        allowed_roles = [
            "TooDank Leaders", "Vice", "TokyoDrift Leaders", "NFS Ops", "NFS OG Leaders", 
            "NeedForSpeed Leaders", "M16Speed Spy Daddies", "GoldyLeads", "Burnout Leaders", 
            "Dugout Leads", "Kerchoo Leaders", "Rush Hour Leaders", "Speed Bump Leaders", 
            "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad"
        ]
        
        # Check if the user has at least one of the allowed roles
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in allowed_roles for role in user_roles)

    @commands.command()
    async def checkbattle(self, ctx, opponent_club):
        try:
            cursor = self.connection.cursor()

            # Query to get win, loss, and draw counts grouped by opponent
            cursor.execute("""
                SELECT player_club, 
                    SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) AS losses,
                    SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) AS draws
                FROM club_records
                WHERE opponent_club_name = %s
                GROUP BY player_club
            """, (opponent_club,))

            records = cursor.fetchall()  # Fetch all results

            cursor.execute("""
                           """)

            if not records:
                # No records found for the given club
                await ctx.send(f"No records found for **{opponent_club}**. Please log a new battle with logclubbattle.")
            else:
                # Format the results
                result_message = f"Battle records for **{opponent_club}**:\n\n"
                for record in records:
                    player_club, wins, losses, draws = record
                    result_message += f"**{player_club}** - Wins: {wins}, Losses: {losses}, Draws: {draws}\n"

                await ctx.send(result_message)
                await ctx.send()

        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")




async def setup(bot):
    connection = bot.connection
    await bot.add_cog(BattleRecords(bot, connection))
