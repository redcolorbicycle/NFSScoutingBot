from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord
import shlex
from player_commands import addplayer
from player_commands import updateclub

class ClubCommands(commands.Cog):
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
    async def addclub(self, ctx, club_name: str):
        """Add a new club to the database."""
        try:
            cursor = self.connection.cursor()
            club_name = club_name.lower()

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
    async def renameclub(self, ctx, old_name: str, new_name: str):
        """Rename an existing club in the database."""
        old_name = old_name.lower()
        new_name = new_name.lower()
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
    async def deleteclub(self, ctx, club_name: str):
        """Delete a club from the database if it has no players."""
        club_name = club_name.lower()
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
    async def listclubs(self, ctx):
        """List all clubs in the database."""
        try:
            with self.connection.cursor() as cursor:
                # Fetch all clubs from the database
                cursor.execute("SELECT Club_Name FROM Club ORDER BY Club_Name ASC")
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
    async def scoutclub(self, ctx, club_name: str):
        """
        Fetch player details for a specific club and return them as a table image.
        """
        club_name = club_name.lower()
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
                df = df.sort_values(by = "PR")

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

                # Apply conditional formatting for PR column
                cell_dict = table.get_celld()
                pr_index = columns.index("PR")  # Find the index of the PR column
                for (row, col), cell in cell_dict.items():
                    if col == pr_index and row > 0:  # Exclude header row
                        pr_value = df.iloc[row - 1, pr_index]  # Get PR value
                        if pr_value <= 50:
                            cell.set_facecolor("#FF0000")  # Sharp red for top 50
                        elif pr_value <= 200:
                            cell.set_facecolor("#FFA500")  # Orange for 51-200
                        elif pr_value <= 500:
                            cell.set_facecolor("#FFFF00")  # Yellow for 200-500
                        elif pr_value <= 1000:
                            cell.set_facecolor("#ADD8E6")  # Light blue for 500-1000
                        elif pr_value <= 2000:
                            cell.set_facecolor("#800080")  # Purple for 1001-2000

                    cell.set_height(0.1)  # Adjust the row height (experiment with values for desired size)

                # Save the table as an image in memory
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="club_table.png")
                await ctx.send("Applebee's 🍎")
                await ctx.send("we Eatn Good in the neighborhood")
                await ctx.send("unless Bieber's the waiter")
                await ctx.send(file=file)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def scoutclubez(self, ctx, club_name: str):
        """
        Fetch player details for a specific club and return them as a table image.
        """
        club_name = club_name.lower()
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
                df = df.sort_values(by = "PR")

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
                pr_index = columns.index("PR")  # Find the index of the PR column
                for (row, col), cell in cell_dict.items():
                    if col == pr_index and row > 0:  # Exclude header row
                        pr_value = df.iloc[row - 1, pr_index]  # Get PR value
                        if pr_value <= 50:
                            cell.set_facecolor("#FF0000")  # Sharp red for top 50
                        elif pr_value <= 200:
                            cell.set_facecolor("#FFA500")  # Orange for 51-200
                        elif pr_value <= 500:
                            cell.set_facecolor("#FFFF00")  # Yellow for 200-500
                        elif pr_value <= 1000:
                            cell.set_facecolor("#ADD8E6")  # Light blue for 500-1000
                        elif pr_value <= 2000:
                            cell.set_facecolor("#800080")  # Purple for 1001-2000
                            
                    cell.set_height(0.1)  # Adjust the row height (experiment with values for desired size)

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


    @commands.command()
    async def scoutclubtext(self, ctx, club_name:str):
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                # Fetch player details for the club
                cursor.execute(
                    """
                    SELECT Name, Nerf, PR, team_name
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return
                
                player_details = "\n".join(
                f"**Name**: {player[0]}, **Nerf**: {player[1]}, **PR**: {player[2]}, **Team**: {player[3]}"
                for player in players
            )

            # Create the response message
            message = f"**Players in {club_name}:**\n{player_details}"

            # Send the message
            await ctx.send(message)

                
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command
    async def addtoclub(self, ctx, club_name: str, *, args: str = ""):
        player_commands_cog = self.bot.get_cog("PlayerCommands")
        try:
            with self.connection.cursor() as cursor:
                # Check if the club exists
                cursor.execute(
                    """
                    SELECT club_name
                    FROM Club
                    WHERE club_name = %s
                    """,
                    (club_name,),
                )
                club = cursor.fetchone()

                if not club:
                    # If club doesn't exist, add it
                    self.addclub(club_name)
                    await ctx.send(f"Club **{club_name}** has been added to the database.")

                # Process player names from `args`
                if args:
                    parsed_args = shlex.split(args)  # Split the player names

                    for player_name in parsed_args:
                        # Check if the player exists
                        cursor.execute(
                            """
                            SELECT player_name
                            FROM Player
                            WHERE player_name = %s
                            """,
                            (player_name,),
                        )
                        player = cursor.fetchone()

                        if player:
                            if player_commands_cog:
                                await player_commands_cog.updateclub(ctx, player_name, club_name)
                                await ctx.send(f"Updated **{player_name}** to club **{club_name}**.")
                            else:
                                await ctx.send("Error: `PlayerCommands` cog is not loaded.")
                                return
                        else:
                            if player_commands_cog:
                                await player_commands_cog.addplayer(ctx, player_name, club=club_name)
                                await ctx.send(f"Added player **{player_name}** to club **{club_name}**.")
                            else:
                                await ctx.send("Error: `PlayerCommands` cog is not loaded.")
                                return

                    self.connection.commit()
                else:
                    await ctx.send("No player names were provided.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")




async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(ClubCommands(bot, connection))