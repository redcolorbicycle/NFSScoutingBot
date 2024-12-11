from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import discord

class PlayerCommands(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def scout_player(self, ctx, player_name: str):
        """Fetch all details of a specific player."""
        try:
            cursor = self.connection.cursor()
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
                    f"{name}, PR {pr} from {club} ({team_name})\n"
                    f"**SP1**: {sp1_name} ({sp1_skills})\n"
                    f"**SP2**: {sp2_name} ({sp2_skills})\n"
                    f"**SP3**: {sp3_name} ({sp3_skills})\n"
                    f"**SP4**: {sp4_name} ({sp4_skills})\n"
                    f"**SP5**: {sp5_name} ({sp5_skills})\n"
                    f"**Nerf**: {nerf}\n"
                    f"**Most Common Batting Skill**: {batting_skill}\n"
                    f"**Last Updated**: {last_updated}\n"
                    f"**Nerf Last Updated**: {nerf_updated}\n"
                )

                await ctx.send(details)
            else:
                await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def add_player(self, ctx, name: str, *, args: str = ""):
        """
        Add a new player to the database using the first argument as the name and optional keyword arguments.
        Example usage:
        !add_player John club=tokyodrift pr=9000 sp1_name=Skill1
        Unspecified arguments will take their default values:
        - Club_Name: "NO CLUB"
        - PR: 9999
        - Other SP fields, Nerf, Batting_Skill, and Team_Name: Empty strings
        """
        try:
            # Default values
            defaults = {
                "Club_Name": "NO CLUB",
                "SP1_Name": "",
                "SP1_Skills": "",
                "SP2_Name": "",
                "SP2_Skills": "",
                "SP3_Name": "",
                "SP3_Skills": "",
                "SP4_Name": "",
                "SP4_Skills": "",
                "SP5_Name": "",
                "SP5_Skills": "",
                "Nerf": "",
                "Batting_Skill": "",
                "PR": 9999,
                "Team_Name": "",
            }

            # Parse the keyword arguments
            provided_args = {}
            if args:
                for arg in args.split():
                    key, value = map(str.strip, arg.split("=", 1))
                    provided_args[key] = value

            # Merge provided arguments with defaults
            for key in defaults.keys():
                if key in provided_args:
                    defaults[key] = provided_args[key]

            # Validate PR as an integer
            try:
                defaults["PR"] = int(defaults["PR"])
            except ValueError:
                await ctx.send("Error: 'PR' must be an integer.")
                return

            cursor = self.connection.cursor()

            # Check if the player already exists
            cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
            existing_player = cursor.fetchone()

            if existing_player:
                await ctx.send(f"The player '{name}' already exists in the database. No changes made.")
            else:
                # Insert the player with all arguments
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
                        defaults["Club_Name"],
                        defaults["SP1_Name"],
                        defaults["SP1_Skills"],
                        defaults["SP2_Name"],
                        defaults["SP2_Skills"],
                        defaults["SP3_Name"],
                        defaults["SP3_Skills"],
                        defaults["SP4_Name"],
                        defaults["SP4_Skills"],
                        defaults["SP5_Name"],
                        defaults["SP5_Skills"],
                        defaults["Nerf"],
                        defaults["Batting_Skill"],
                        defaults["PR"],
                        defaults["Team_Name"],
                    ),
                )
                self.connection.commit()
                await ctx.send(f"Added new player '{name}' to the database.")

            cursor.close()
            await self.scout_player(ctx, name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")




    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def update_nerf(self, ctx, player_name: str, new_nerf: str):
        """Update the nerf value for a player and set the nerf last updated date."""
        try:
            with self.connection.cursor() as cursor:
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
                    self.connection.commit()
                    await self.scout_player(ctx, player_name)
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def delete_player(self, ctx, player_name: str):
        """Delete a player from the database."""
        try:
            with self.connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if player:
                    # Delete the player
                    cursor.execute("DELETE FROM Player WHERE Name = %s", (player_name,))
                    self.connection.commit()
                    await ctx.send(f"Player '{player_name}' has been deleted from the database.")
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def edit_sp(self, ctx, player_name: str, sp_number: int, sp_name: str, sp_skills: str):
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

            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def update_pr(self, ctx, player_name: str, new_pr: int):
        """
        Update a player's PR (Power Rating).
        Args:
            player_name: The name of the player whose PR to update.
            new_pr: The new PR value.
        """
        try:
            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_club(self, ctx, player_name: str, new_club: str):
        """Change a player's club and update both Player and Club tables."""
        try:
            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_bat(self, ctx, player_name: str, new_batting_skill: str):
        """
        Update the most common batting skill for a player.
        Args:
            player_name: The name of the player whose batting skill to update.
            new_batting_skill: The new most common batting skill.
        """
        try:
            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def change_team_deck(self, ctx, player_name: str, new_team_name: str):
        """
        Change the team name of a player.
        Args:
            player_name: The name of the player whose team name to update.
            new_team_name: The new team name.
        """
        try:
            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def rename_player(self, ctx, old_name: str, new_name: str):
        """
        Rename a player in the database.
        Args:
            old_name: The current name of the player to rename.
            new_name: The new name for the player.
        """
        try:
            with self.connection.cursor() as cursor:
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
                self.connection.commit()
                await self.scout_player(ctx, old_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")



async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(PlayerCommands(bot, connection))