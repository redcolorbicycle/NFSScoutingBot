from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import shlex
import discord
import pandas as pd
import psycopg2
from urllib.parse import urlparse
import os
import asyncio


class PlayerCommands(commands.Cog):
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
            "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad", "M16 Recruit"
        ]
        
        # Check if the user has at least one of the allowed roles
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in allowed_roles for role in user_roles)
    

    @commands.command()
    async def excel(self, ctx):
        # Path to your preformatted Excel file
        file_path = "uploadtemplate.xlsx"
        
        # Send the file to the user
        try:
            await ctx.send(file=discord.File(file_path, filename="uploadtemplate.xlsx"))
        except Exception as e:
            await ctx.send(f"Error: Could not send the file. {e}")


    @commands.command()
    async def scoutplayer(self, ctx, player_name: str):
        """Fetch all details of a specific player."""
        player_name = player_name.lower()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT Name, Club_Name, SP1_Name, SP1_Skills, SP2_Name, SP2_Skills, 
                       SP3_Name, SP3_Skills, SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                       Nerf, PR, last_updated, nerf_updated, team_name, charbats, toolbats
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
                    nerf, pr, last_updated, nerf_updated, team_name, charbats, toolbats
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
                    f"**Last Updated**: {last_updated}\n"
                    f"**Nerf Last Updated**: {nerf_updated}\n"
                    f"**Charisma Bats**: {charbats}\n"
                    f"**5 Tool Bats**: {toolbats}\n"
                )

                await ctx.send(details)
            else:
                await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def addplayer(self, ctx, name: str, *, args: str = ""):
        """
        Add a new player to the database using the first argument as the name and optional keyword arguments.
        """
        name = name.lower()
        args = args.replace("“", '"').replace("”", '"')

        try:
            # Default values
            defaults = {
                "club": "no club",
                "sp1name": "",
                "sp1skills": "",
                "sp2name": "",
                "sp2skills": "",
                "sp3name": "",
                "sp3skills": "",
                "sp4name": "",
                "sp4skills": "",
                "sp5name": "",
                "sp5skills": "",
                "nerf": "",
                "pr": 9999,
                "teamdeck": "",
                "charbats": 0,
                "toolbats": 0,
            }

            # Parse arguments with shlex
            provided_args = {}
            if args:
                parsed_args = shlex.split(args)
                for arg in parsed_args:
                    key, value = map(str.strip, arg.split("=", 1))
                    provided_args[key.lower()] = value.lower()

            # Merge with defaults
            for key in defaults.keys():
                if key in provided_args:
                    defaults[key] = provided_args[key]

            # Validate PR
            defaults["pr"] = int(defaults["pr"])
            defaults["charbats"] = int(defaults["charbats"])
            defaults["toolbats"] = int(defaults["toolbats"])
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
                        Nerf, PR, last_updated, nerf_updated, team_name, charbats, toolbats
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE, %s, %s, %s)
                    """,
                    (
                        name,
                        defaults["club"],
                        defaults["sp1name"],
                        defaults["sp1skills"],
                        defaults["sp2name"],
                        defaults["sp2skills"],
                        defaults["sp3name"],
                        defaults["sp3skills"],
                        defaults["sp4name"],
                        defaults["sp4skills"],
                        defaults["sp5name"],
                        defaults["sp5skills"],
                        defaults["nerf"],
                        defaults["pr"],
                        defaults["teamdeck"],
                        defaults["charbats"],
                        defaults["toolbats"],
                    ),
                )
                self.connection.commit()
                await ctx.send(f"Added new player '{name}' to the database.")

            cursor.close()
            await self.scoutplayer(ctx, name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatenerf(self, ctx, player_name: str, new_nerf: str):
        """Update the nerf value for a player and set the nerf last updated date."""
        player_name = player_name.lower()
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
                    await self.scoutplayer(ctx, player_name)
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    @commands.has_role("M16Speed Spy Daddies")
    async def deleteplayer(self, ctx, player_name: str):
        """Delete a player from the database."""
        player_name = player_name.lower()
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
    async def updatesp(self, ctx, player_name: str, sp_number: int, sp_name: str, sp_skills: str):
        """

        Args:
            player_name: The name of the player whose SP to edit.
            sp_number: The SP number (1 to 5) to edit.
            sp_name: The new name for the SP.
            sp_skills: The new skills for the SP.
        """
        player_name = player_name.lower()
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
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatepr(self, ctx, player_name: str, new_pr: int):
        """
        Update a player's PR (Power Rating).
        Args:
            player_name: The name of the player whose PR to update.
            new_pr: The new PR value.
        """
        player_name = player_name.lower()
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
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def updatechar(self, ctx, player_name: str, new_char: int):
        """
        Update a player's char bats.
        Args:
            player_name: The name of the player whose PR to update.
            new_char: The new number of char bats
        """
        player_name = player_name.lower()
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
                    SET charbats = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_char, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatetool(self, ctx, player_name: str, new_tool: int):
        """
        Update a player's tool bats.
        Args:
            player_name: The name of the player whose PR to update.
            new_tool: The new number of tool bats
        """
        player_name = player_name.lower()
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
                    SET toolbats = %s, last_updated = CURRENT_DATE
                    WHERE Name = %s
                    """,
                    (new_tool, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")
    
    

    @commands.command()
    async def updateclub(self, ctx, player_name: str, new_club: str):
        """Change a player's club and update both Player and Club tables."""
        player_name = player_name.lower()
        new_club = new_club.lower()
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
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updateteamdeck(self, ctx, player_name: str, new_team_name: str):
        """
        Change the team name of a player.
        Args:
            player_name: The name of the player whose team name to update.
            new_team_name: The new team name.
        """
        player_name = player_name.lower()
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
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def renameplayer(self, ctx, old_name: str, new_name: str):
        """
        Rename a player in the database.
        Args:
            old_name: The current name of the player to rename.
            new_name: The new name for the player.
        """
        old_name = old_name.lower()
        new_name = new_name.lower()
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
                await self.scoutplayer(ctx, new_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def listplayers(self, ctx):
        """List the bottom 10 most recently added players and the total number of players in the database."""
        try:
            with self.connection.cursor() as cursor:
                # Fetch the total number of clubs
                cursor.execute("SELECT COUNT(*) FROM Player")
                total_clubs = cursor.fetchone()[0]

                # Fetch the bottom 10 most recently added clubs
                cursor.execute(
                    """
                    SELECT Name
                    FROM Player
                    OFFSET GREATEST((SELECT COUNT(*) FROM Player) - 10, 0)
                    """
                )
                players = cursor.fetchall()

                if players:
                    # Format the recent clubs list
                    playerlist = "\n".join([club[0] for club in players])
                    await ctx.send(
                        f"**Total Players in the Database:** {total_clubs}\n\n"
                        f"**10 Most Recently Added Players:**\n{playerlist}"
                    )
                else:
                    await ctx.send("No players found in the database.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updateplayer(self, ctx, name: str, *, args: str = ""):
        """
        Update multiple attributes of a player in a single command.
        Example usage:
        !updateplayer John club=NewClubName nerf=NewNerfValue pr=9000 bat=NewBatSkill teamdeck=NewTeamDeck
        """
        name = name.lower()
        args = args.replace("“", '"').replace("”", '"')  # Replace smart quotes
        try:
            # Define a mapping from user-friendly keys to SQL column names
            column_mapping = {
                "club": "club_name",
                "nerf": "nerf",
                "pr": "pr",
                "teamdeck": "team_name",
                "sp1n": "sp1_name",
                "sp1s": "sp1_skills",
                "sp2n": "sp2_name",
                "sp2s": "sp2_skills",
                "sp3n": "sp3_name",
                "sp3s": "sp3_skills",
                "sp4n": "sp4_name",
                "sp4s": "sp4_skills",
                "sp5n": "sp5_name",
                "sp5s": "sp5_skills",
                "char": "charbats",
                "tool": "toolbats",
            }

            # Parse the key-value arguments using shlex.split
            updates = {}
            if args:
                for arg in shlex.split(args):
                    key, value = map(str.strip, arg.split("=", 1))
                    key = key.lower()
                    if key in column_mapping:
                        updates[column_mapping[key]] = value.lower()

            # Validate and construct the SQL query
            update_query_parts = []
            update_values = []
            for column, value in updates.items():
                if column == "pr":  # Convert PR to integer
                    try:
                        value = int(value)
                    except ValueError:
                        await ctx.send(f"Invalid value for PR: {value}. It must be an integer.")
                        return
                update_query_parts.append(f"{column} = %s")
                update_values.append(value)

            if not update_query_parts:
                await ctx.send("No valid updates provided.")
                return

            # Add the player's name to the query
            update_query = ", ".join(update_query_parts)
            update_values.append(name)

            # Execute the update query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
                player = cursor.fetchone()

                if not player:
                    await ctx.send(f"No player found with the name '{name}'.")
                    return

                cursor.execute(
                    f"UPDATE Player SET {update_query}, last_updated = CURRENT_DATE WHERE Name = %s",
                    update_values,
                )
                self.connection.commit()
                await ctx.send(f"Updated player '{name}' with the following changes: {updates}")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")



    def upload_to_database(self, file_stream):
        # Read the Excel file
        df = pd.read_excel(file_stream, engine="openpyxl")

        # Format the names properly
        df["Name"] = df["Name"].astype(str)
        df["Name"] = df["Name"].str.lower().str.replace(" ", "")
        df["Club_Name"] = df["Club_Name"].str.lower()

        # Fill empty values
        df["Club_Name"].fillna("no club", inplace=True)
        df["Nerf"].fillna("", inplace=True)
        df["PR"].fillna(9999, inplace=True)
        df["charbats"].fillna(0, inplace=True)
        df["toolbats"].fillna(0, inplace=True)
        df.fillna({
            "SP1_name": "",
            "SP1_skills": "",
            "SP2_name": "",
            "SP2_skills": "",
            "SP3_name": "",
            "SP3_skills": "",
            "SP4_name": "",
            "SP4_skills": "",
            "SP5_name": "",
            "SP5_skills": "",
            "Team_Name": "",
        }, inplace=True)

        df["charbats"] = df["charbats"].astype(int)
        df["toolbats"] = df["toolbats"].astype(int)

        DATABASE_URL = os.getenv("DATABASE_URL")
        result = urlparse(DATABASE_URL)
        connection = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
        )

        try:
            with connection.cursor() as cursor:
                # Process clubs first to avoid duplication
                clubs = df["Club_Name"].unique()
                for club_name in clubs:
                    cursor.execute(
                        "INSERT INTO Club (Club_Name) VALUES (%s) ON CONFLICT (Club_Name) DO NOTHING",
                        (club_name,)
                    )

                # Prepare batch insert for players
                player_data = [
                    (
                        row["Name"], row["Club_Name"], row["SP1_name"], row["SP1_skills"],
                        row["SP2_name"], row["SP2_skills"], row["SP3_name"], row["SP3_skills"],
                        row["SP4_name"], row["SP4_skills"], row["SP5_name"], row["SP5_skills"],
                        row["Nerf"], row["PR"], row["Team_Name"], row["charbats"], row["toolbats"]
                    )
                    for _, row in df.iterrows()
                ]

                # Batch insert players
                execute_batch(
                    cursor,
                    """
                    INSERT INTO Player (
                        Name, Club_Name, SP1_Name, SP1_Skills,
                        SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                        SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                        Nerf, PR, team_name, charbats, toolbats, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
                    ON CONFLICT (Name) DO NOTHING
                    """,
                    player_data
                )

            connection.commit()  # Commit after processing all rows
        except Exception as e:
            connection.rollback()  # Rollback on any database error
            raise e
        finally:
            connection.close()  # Ensure proper cleanup


    @commands.command()
    async def upload(self, ctx):
        # Check if a file is attached
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please attach an Excel file with the command!")
            return

        # Get the attached file
        attachment = ctx.message.attachments[0]
        
        # Download the file into a BytesIO object
        file_stream = BytesIO()
        await attachment.save(file_stream)
        file_stream.seek(0)

        try:
            # Pass the file stream to the upload_to_database function
            await asyncio.to_thread(self.upload_to_database, file_stream)
            await ctx.send("Data successfully uploaded to the database!")
        except Exception as e:
            await ctx.send(f"Error: {e}")



async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(PlayerCommands(bot, connection))