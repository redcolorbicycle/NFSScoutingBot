import random
from io import BytesIO
from PIL import Image
import discord
import os
from discord.ext import commands

class PlayerRegistration(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    @commands.command()
    async def register(self, ctx, playername: str, status: str):
        """
        Register a player with a status of 'high', 'middle', or 'low'.
        """
        status = status.lower()
        # Validate the status
        valid_statuses = {"high", "middle", "low"}
        if status.lower() not in valid_statuses:
            await ctx.send(f"Invalid status: {status}. Please choose 'high', 'middle', or 'low'.")
            return

        try:
            with self.connection.cursor() as cursor:
                # Insert the player into the `needfriends` table
                cursor.execute(
                    """
                    INSERT INTO needfriends (playername, status)
                    VALUES (%s, %s)
                    ON CONFLICT (playername) DO UPDATE
                    SET status = EXCLUDED.status
                    """,
                    (playername.lower(), status.lower()),
                )
                self.connection.commit()
                await ctx.send(f"Player '{playername}' has been registered with status '{status}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def tinder2us(self, ctx):
        """
        Print all players and their statuses in the database.
        """
        try:
            with self.connection.cursor() as cursor:
                # Retrieve all players and their statuses
                cursor.execute("SELECT playername, status FROM needfriends ORDER BY playername;")
                records = cursor.fetchall()

                if not records:
                    await ctx.send("No players are currently registered.")
                else:
                    # Format the output
                    response = "\n".join([f"**{player}**: {status}" for player, status in records])
                    await ctx.send(f"**Registered Players:**\n{response}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")




async def setup(bot):
    await bot.add_cog(PlayerRegistration(bot))
