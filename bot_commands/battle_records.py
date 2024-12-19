from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz

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
        """
        Pulls up opponent record
        """
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

            if not records:
                # No records found for the given club
                await ctx.send(f"No records found for **{opponent_club}**. Check your roster with !check clubname."
                               f"Start a new battle with !start homeclub opponentclub."
                               f"Log battles with !log homenumber opponentnumber result.")
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

    @commands.command()
    async def checkroster(self, ctx, hometeam):
        """
        Shows roster
        """
        try:
            with self.connection.cursor() as cursor:
                roster = ""
                cursor.execute("""
                    SELECT * FROM hometeam 
                               WHERE homeclub = %s;
                               """, (hometeam,))
                rows = cursor.fetchall()
                for row in rows:
                    roster.append(f"Player {row[0]} is designated {row[1]} and is on SP{row[2]}\n")
                await ctx.send(f"{roster}")
                await ctx.send("Please use command logroster if you want to use a new roster.")

        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command()
    async def startbattle(self, ctx, hometeam, opponent):
        """
        Start a new battle and lock the current date.
        """
        try:
            with self.connection.cursor() as cursor:
                # Lock the current date
                cursor.execute(
                    """
                    UPDATE battle_date SET locked_date = CURRENT_DATE,id = CASE WHEN id = 0 THEN 1 ELSE id END WHERE id = 0;

                    """
                )
                self.connection.commit()

                # Your existing logic to reset players
                cursor.execute("""
                    UPDATE hometeam
                    SET SP = 1
                    WHERE homeclub = %s
                """, (hometeam,))
                cursor.execute("""
                    UPDATE opponents
                    SET SP = 1
                    WHERE opponentclub = %s
                """, (opponent,))
                self.connection.commit()

            await ctx.send(f"Battle started between **{hometeam}** and **{opponent}**. Date locked to today's date.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")



async def setup(bot):
    connection = bot.connection
    await bot.add_cog(BattleRecords(bot, connection))
