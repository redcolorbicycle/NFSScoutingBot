from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord

class ClubCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = bot.connection

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def add_club(self, ctx, club_name: str):
        """Add a new club to the database."""
        try:
            cursor = self.connection.cursor()

            # Check if the club already exists
            cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
            existing_club = cursor.fetchone()

            if existing_club:
                await ctx.send(f"The club '{club_name}' already exists in the database.")
            else:
                # Insert a new club
                cursor.execute(
                    """
                    INSERT INTO Club (Club_Name)
                    VALUES (%s)
                    """,
                    (club_name,),
                )
                self.connection.commit()
                await ctx.send(f"Added new club '{club_name}' to the database.")

            cursor.close()
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def rename_club(self, ctx, old_name: str, new_name: str):
        """Rename an existing club in the database."""
        try:
            with self.connection.cursor() as cursor:
                # Check if the club with the old name exists
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (old_name,))
                existing_club = cursor.fetchone()

                if not existing_club:
                    await ctx.send(f"No club found with the name '{old_name}'.")
                    return

                # Check if the new name already exists
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (new_name,))
                new_name_club = cursor.fetchone()

                if new_name_club:
                    await ctx.send(f"The name '{new_name}' is already taken by another club.")
                    return

                # Rename the club
                cursor.execute(
                    "UPDATE Club SET Club_Name = %s WHERE Club_Name = %s",
                    (new_name, old_name),
                )

                self.connection.commit()
                await ctx.send(f"Renamed club '{old_name}' to '{new_name}' and updated all associated players.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def delete_club(self, ctx, club_name: str):
        """Delete a club from the database if it has no players."""
        try:
            with self.connection.cursor() as cursor:
                # Check if the club exists
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
                club = cursor.fetchone()

                if not club:
                    await ctx.send(f"No club found with the name '{club_name}'.")
                    return

                # Check if the club has players
                cursor.execute("SELECT COUNT(*) FROM Player WHERE Club_Name = %s", (club_name,))
                player_count = cursor.fetchone()[0]

                if player_count > 0:
                    await ctx.send(f"The club '{club_name}' cannot be deleted because it has {player_count} players.")
                    return

                # Delete the club
                cursor.execute("DELETE FROM Club WHERE Club_Name = %s", (club_name,))
                self.connection.commit()
                await ctx.send(f"Club '{club_name}' has been successfully deleted.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def list_clubs(self, ctx):
        """List all clubs in the database."""
        try:
            with self.connection.cursor() as cursor:
                # Fetch all clubs from the database
                cursor.execute("SELECT Club_Name FROM Club")
                clubs = cursor.fetchall()

                if clubs:
                    club_list = "\n".join([club[0] for club in clubs])  # Extract club names into a formatted string
                    await ctx.send(f"**Clubs in the Database:**\n{club_list}")
                else:
                    await ctx.send("No clubs found in the database.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_club(self, ctx, club_name: str):
        """
        Fetch player details for a specific club and return them as a table image.
        """
        try:
            with self.connection.cursor() as cursor:
                # Fetch player details for the club
                cursor.execute(
                    """
                    SELECT Name, sp1_name, sp1_skills, sp2_name, sp2_skills, sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name,
                    sp5_skills, Nerf, PR, Most_Common_Batting_Skill, last_updated
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return

                # Combine SP Name and Skills into single columns (SP1 Info, SP2 Info, etc.)
                processed_players = [
                    (
                        player[0],  # Name
                        f"{player[1]} ({player[2]})",  # SP1 Info
                        f"{player[3]} ({player[4]})",  # SP2 Info
                        f"{player[5]} ({player[6]})",  # SP3 Info
                        f"{player[7]} ({player[8]})",  # SP4 Info
                        f"{player[9]} ({player[10]})",  # SP5 Info
                        player[11],  # Nerf
                        player[12],  # PR
                        player[13],  # Batting Skill
                        player[14],  # Last Updated
                    )
                    for player in players
                ]

                # Define new column headers
                columns = [
                    "Name", "SP1 Info", "SP2 Info", "SP3 Info", "SP4 Info", "SP5 Info",
                    "Nerf", "PR", "Batting Skill", "Last Updated"
                ]

                # Create a DataFrame from the processed data
                df = pd.DataFrame(processed_players, columns=columns)

                # Plot the table using matplotlib
                fig, ax = plt.subplots(figsize=(24, len(df) * 0.5 + 1))  # Dynamic height based on rows
                ax.axis("tight")
                ax.axis("off")
                table = ax.table(
                    cellText=df.values,
                    colLabels=df.columns,
                    cellLoc="center",
                    loc="center",
                )

                # Adjust table style
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.auto_set_column_width(col=list(range(len(df.columns))))

                cell_dict = table.get_celld()
                for (row, col), cell in cell_dict.items():
                    cell.set_height(0.1)  # Adjust the row height (experiment with values for desired size)

                # Save the table as an image in memory
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="club_table.png")
                await ctx.send(file=file)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_cupcake(self, ctx, club_name: str):
        """
        Fetch player details for a specific club and return them as a table image.
        """
        try:
            with self.connection.cursor() as cursor:
                # Fetch player details for the club
                cursor.execute(
                    """
                    SELECT Name, Nerf, PR, Most_Common_Batting_Skill, last_updated, nerf_updated, team_name
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return

                # Create a DataFrame from the fetched data
                columns = ["Name", "Nerf", "PR", "Batting Skill", "Last Updated", "Nerf Updated",
                        "Team Deck"]
                df = pd.DataFrame(players, columns=columns)

                # Plot the table using matplotlib
                fig, ax = plt.subplots(figsize=(5, len(df) * 2 + 1))  # Increase width and dynamic height
                ax.axis("tight")
                ax.axis("off")
                table = ax.table(
                    cellText=df.values,
                    colLabels=df.columns,
                    cellLoc="center",
                    loc="center",
                )

                # Adjust table style
                table.auto_set_font_size(False)
                table.set_fontsize(20)  # Increase font size for better readability
                table.auto_set_column_width(col=list(range(len(df.columns))))  # Ensure all columns fit
                
                cell_dict = table.get_celld()
                for (row, col), cell in cell_dict.items():
                    cell.set_height(0.08)  # Adjust the row height (experiment with values for desired size)

                # Save the table as an image in memory with minimal borders
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.1, dpi=200)  # Adjust DPI for higher quality
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="club_table.png")
                await ctx.send(file=file)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")








def setup(bot):
    bot.add_cog(ClubCommands(bot))