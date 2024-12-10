from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord

def setup_commands(bot, connection):
    """Register all commands for the bot."""

    #club commands

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_club(ctx, club_name: str):
        """Fetch all players belonging to a specific club and display their details using scout_player."""
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT Name FROM Player WHERE Club_Name = %s", (club_name,))
            players = cursor.fetchall()
            cursor.close()

            if players:
                for player in players:
                    # Call scout_player for each player in the club
                    player_name = player[0]
                    await scout_player(ctx, player_name)  # Call scout_player with ctx and player_name
            else:
                await ctx.send(f"No players found for the club '{club_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_cupcake(ctx, club_name: str):
        """
        Fetch and display selected details (Name, Nerf, PR, Last Updated, Nerf Last Updated)
        of all players belonging to a specific club.
        """
        try:
            with connection.cursor() as cursor:
                # Fetch the desired details for all players in the club
                cursor.execute(
                    """
                    SELECT Name, Nerf, PR, last_updated, nerf_updated, team_name
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if players:
                    # Format details for each player
                    details_list = [
                        (
                            f"**Name**: {player[0]}\n"
                            f"**Nerf**: {player[1]}\n"
                            f"**PR**: {player[2]}\n"
                            f"**Last Updated**: {player[3]}\n"
                            f"**Nerf Last Updated**: {player[4]}\n"
                            f"**Team Name**: {player[5]}"
                        )
                        for player in players
                    ]
                    # Send details as separate messages
                    for details in details_list:
                        await ctx.send(details)
                else:
                    await ctx.send(f"No players found for the club '{club_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def add_club(ctx, club_name: str):
        """Add a new club to the database."""
        try:
            cursor = connection.cursor()

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
                connection.commit()
                await ctx.send(f"Added new club '{club_name}' to the database.")

            cursor.close()
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def rename_club(ctx, old_name: str, new_name: str):
        """Rename an existing club in the database."""
        try:
            with connection.cursor() as cursor:
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

                connection.commit()
                await ctx.send(f"Renamed club '{old_name}' to '{new_name}' and updated all associated players.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def delete_club(ctx, club_name: str):
        """Delete a club from the database if it has no players."""
        try:
            with connection.cursor() as cursor:
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
                connection.commit()
                await ctx.send(f"Club '{club_name}' has been successfully deleted.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def list_clubs(ctx):
        """List all clubs in the database."""
        try:
            with connection.cursor() as cursor:
                # Fetch all clubs from the database
                cursor.execute("SELECT Club_Name FROM Club")
                clubs = cursor.fetchall()

                if clubs:
                    club_list = "\n".join([club[0] for club in clubs])  # Extract club names into a formatted string
                    await ctx.send(f"**Clubs in the Database:**\n{club_list}")
                else:
                    await ctx.send("No clubs found in the database.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_club_image(ctx, club_name: str):
        """
        Fetch player details for a specific club and return them as a table image.
        """
        try:
            with connection.cursor() as cursor:
                # Fetch player details for the club
                cursor.execute(
                    """
                    SELECT Name, sp1_name, sp1_skills, sp2_name, sp2_skills, sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name,
                    sp5_skills, Nerf, PR, Most_Common_Batting_Skill, last_updated, nerf_updated, team_name
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
                columns = ["Name", "SP1 Name", "SP1 Skills", "SP2 Name", "SP2 Skills", "SP3 Name", "SP3 Skills", "SP4 Name", 
                           "SP4 Skills", "SP5 Name", "SP5 Skills", "Nerf", "PR", "Batting Skill", "Last Updated", "Nerf Updated",
                           "Team Deck"]
                df = pd.DataFrame(players, columns=columns)

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

                # Save the table as an image in memory
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="club_table.png")
                await ctx.send(file=file)
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    

    








    #player commands

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_player(ctx, player_name: str):
        """Fetch all details of a specific player."""
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT Name, Club_Name, SP1_Name, SP1_Skills, SP2_Name, SP2_Skills, 
                       SP3_Name, SP3_Skills, SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                       Nerf, Most_Common_Batting_Skill, PR, last_updated, nerf_updated, team_name
                FROM Player
                WHERE Name = %s
                """,
                (player_name,),
            )
            player = cursor.fetchone()
            cursor.close()

            if player:
                (
                    name, club, sp1_name, sp1_skills, sp2_name, sp2_skills,
                    sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                    nerf, batting_skill, pr, last_updated, nerf_updated, team_name
                ) = player

                details = (
                    f"**Player Details**\n"
                    f"**Name**: {name}\n"
                    f"**Club**: {club}\n"
                    f"**SP1**: {sp1_name} ({sp1_skills})\n"
                    f"**SP2**: {sp2_name} ({sp2_skills})\n"
                    f"**SP3**: {sp3_name} ({sp3_skills})\n"
                    f"**SP4**: {sp4_name} ({sp4_skills})\n"
                    f"**SP5**: {sp5_name} ({sp5_skills})\n"
                    f"**Nerf**: {nerf}\n"
                    f"**Most Common Batting Skill**: {batting_skill}\n"
                    f"**PR**: {pr}\n"
                    f"**Last Updated**: {last_updated}\n"
                    f"**Nerf Last Updated**: {nerf_updated}\n"
                    f"**Team Deck**: {team_name}\n"
                )

                await ctx.send(details)
            else:
                await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_player_image(ctx, name: str):
        """
        Fetch player details for a specific player and return them as a table image.
        """
        try:
            with connection.cursor() as cursor:
                # Fetch player details for the specified name
                cursor.execute(
                    """
                    SELECT Name, Club_name, sp1_name, sp1_skills, sp2_name, sp2_skills, sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name,
                    sp5_skills, Nerf, PR, Most_Common_Batting_Skill, last_updated, nerf_updated, team_name
                    FROM Player
                    WHERE Name = %s
                    """,
                    (name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found.")
                    return

                # Create a DataFrame from the fetched data
                columns = ["Name", "Club Name", "SP1 Name", "SP1 Skills", "SP2 Name", "SP2 Skills", "SP3 Name", "SP3 Skills", "SP4 Name", 
                        "SP4 Skills", "SP5 Name", "SP5 Skills", "Nerf", "PR", "Batting Skill", "Last Updated", "Nerf Updated",
                        "Team Deck"]
                df = pd.DataFrame(players, columns=columns)

                # Plot the table using matplotlib
                fig, ax = plt.subplots(figsize=(50, len(df) * 2 + 3))  # Increased width and height
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
                table.set_fontsize(24)  # Increased font size
                table.auto_set_column_width(col=list(range(len(df.columns))))

                # Save the table as an image in memory
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight", dpi=200)  # Higher DPI for better quality
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="player_table.png")
                await ctx.send(file=file)
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")







    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def add_player(
        ctx,
        name: str,
        club_name: str,
        sp1_name: str,
        sp1_skills: str,
        sp2_name: str,
        sp2_skills: str,
        sp3_name: str,
        sp3_skills: str,
        sp4_name: str,
        sp4_skills: str,
        sp5_name: str,
        sp5_skills: str,
        nerf: str,
        batting_skill: str,
        pr: int,
        team_name: str,
    ):
        """Add a new player to the database. Fails if the player already exists."""
        try:
            cursor = connection.cursor()

            # Check if the player already exists
            cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
            existing_player = cursor.fetchone()

            if existing_player:
                await ctx.send(f"The player '{name}' already exists in the database. No changes made.")
            else:
                # Insert a new player and set Last_Updated to the current date
                cursor.execute(
                    """
                    INSERT INTO Player (
                        Name, Club_Name, SP1_Name, SP1_Skills,
                        SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                        SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                        Nerf, Most_Common_Batting_Skill, PR, last_updated, nerf_updated, team_name
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s)
                    """,
                    (
                        name,
                        club_name,
                        sp1_name,
                        sp1_skills,
                        sp2_name,
                        sp2_skills,
                        sp3_name,
                        sp3_skills,
                        sp4_name,
                        sp4_skills,
                        sp5_name,
                        sp5_skills,
                        nerf,
                        batting_skill,
                        pr,
                        team_name
                    ),
                )
                connection.commit()
                await ctx.send(f"Added new player '{name}' to the database.")

            cursor.close()
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def update_nerf(ctx, player_name: str, new_nerf: str):
        """Update the nerf value for a player and set the nerf last updated date."""
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if player:
                    # Update the nerf value and nerf_updated date
                    cursor.execute(
                        """
                        UPDATE Player
                        SET Nerf = %s, nerf_updated = CURRENT_DATE
                        WHERE Name = %s
                        """,
                        (new_nerf, player_name),
                    )
                    connection.commit()
                    await ctx.send(f"Updated nerf for '{player_name}' to '{new_nerf}' and updated the last nerf change date.")
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def delete_player(ctx, player_name: str):
        """Delete a player from the database."""
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if player:
                    # Delete the player
                    cursor.execute("DELETE FROM Player WHERE Name = %s", (player_name,))
                    connection.commit()
                    await ctx.send(f"Player '{player_name}' has been deleted from the database.")
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def edit_sp(ctx, player_name: str, sp_number: int, sp_name: str, sp_skills: str):
        """

        Args:
            player_name: The name of the player whose SP to edit.
            sp_number: The SP number (1 to 5) to edit.
            sp_name: The new name for the SP.
            sp_skills: The new skills for the SP.
        """
        try:
            # Validate SP number
            if sp_number < 1 or sp_number > 5:
                await ctx.send("Invalid SP number. Please specify a number from 1 to 5.")
                return

            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                # Determine the column names for the specified SP
                sp_name_column = f"SP{sp_number}_Name"
                sp_skills_column = f"SP{sp_number}_Skills"

                # Update the SP details for the player
                cursor.execute(
                    f"""
                    UPDATE Player
                    SET {sp_name_column} = %s, {sp_skills_column} = %s
                    WHERE Name = %s
                    """,
                    (sp_name, sp_skills, player_name),
                )
                connection.commit()
                await ctx.send(f"Updated SP{sp_number} for player '{player_name}' to '{sp_name}' ({sp_skills}).")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def update_pr(ctx, player_name: str, new_pr: int):
        """
        Update a player's PR (Power Rating).
        Args:
            player_name: The name of the player whose PR to update.
            new_pr: The new PR value.
        """
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                # Update the PR value for the player
                cursor.execute(
                    """
                    UPDATE Player
                    SET PR = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_pr, player_name),
                )
                connection.commit()
                await ctx.send(f"Updated PR for '{player_name}' to {new_pr}.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_club(ctx, player_name: str, new_club: str):
        """Change a player's club and update both Player and Club tables."""
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                # Get the current club of the player
                current_club = player[1]  # Assuming Club_Name is the second column in the Player table

                # Check if the new club exists, create it if not
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (new_club,))
                new_club_entry = cursor.fetchone()

                if not new_club_entry:
                    cursor.execute("INSERT INTO Club (Club_Name) VALUES (%s)", (new_club,))

                # Update the player's club
                cursor.execute(
                    "UPDATE Player SET Club_Name = %s WHERE Name = %s",
                    (new_club, player_name),
                )

                # Check if the old club is now empty
                cursor.execute("SELECT COUNT(*) FROM Player WHERE Club_Name = %s", (current_club,))
                old_club_player_count = cursor.fetchone()[0]

                # Delete the old club if it is empty
                if old_club_player_count == 0:
                    cursor.execute("DELETE FROM Club WHERE Club_Name = %s", (current_club,))

                connection.commit()
                await ctx.send(f"Player '{player_name}' has been moved to club '{new_club}'. Old club '{current_club}' has been deleted (if empty).")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_bat(ctx, player_name: str, new_batting_skill: str):
        """
        Update the most common batting skill for a player.
        Args:
            player_name: The name of the player whose batting skill to update.
            new_batting_skill: The new most common batting skill.
        """
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                # Update the batting skill for the player
                cursor.execute(
                    """
                    UPDATE Player
                    SET Most_Common_Batting_Skill = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_batting_skill, player_name),
                )
                connection.commit()
                await ctx.send(f"Updated batting skill for '{player_name}' to '{new_batting_skill}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_team_deck(ctx, player_name: str, new_team_name: str):
        """
        Change the team name of a player.
        Args:
            player_name: The name of the player whose team name to update.
            new_team_name: The new team name.
        """
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                # Update the team name for the player
                cursor.execute(
                    """
                    UPDATE Player
                    SET team_name = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_team_name, player_name),
                )
                connection.commit()
                await ctx.send(f"Updated team deck for '{player_name}' to '{new_team_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    @bot.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def rename_player(ctx, old_name: str, new_name: str):
        """
        Rename a player in the database.
        Args:
            old_name: The current name of the player to rename.
            new_name: The new name for the player.
        """
        try:
            with connection.cursor() as cursor:
                # Check if the player with the old name exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (old_name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{old_name}'.")
                    return

                # Check if the new name already exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (new_name,))
                new_name_player = cursor.fetchone()

                if new_name_player:
                    await ctx.send(f"The name '{new_name}' is already taken by another player.")
                    return

                # Update the player's name
                cursor.execute(
                    """
                    UPDATE Player
                    SET Name = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_name, old_name),
                )
                connection.commit()
                await ctx.send(f"Player '{old_name}' has been successfully renamed to '{new_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")








