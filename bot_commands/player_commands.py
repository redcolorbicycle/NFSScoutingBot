from discord.ext import commands
import pandas as pd
from io import BytesIO
import shlex
import discord

from bot_commands.constants import LEADERSHIP_ROLES, UPLOAD_TEMPLATE


class PlayerCommands(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    async def cog_check(self, ctx):
        """Restrict commands to users with specific roles."""
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in LEADERSHIP_ROLES for role in user_roles)


    @commands.command()
    async def excel(self, ctx):
        """Send the upload template Excel file."""
        try:
            await ctx.send(file=discord.File(UPLOAD_TEMPLATE, filename=UPLOAD_TEMPLATE))
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
                       Nerf, PR, last_updated, nerf_updated, team_name, charbats, toolbats, source
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
                    nerf, pr, last_updated, nerf_updated, team_name, charbats, toolbats, source
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
                    f"**Source**: {source}\n"
                )
                await ctx.send(details)
            else:
                await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def addplayer(self, ctx, name: str, *, args: str = ""):
        """Add a new player to the database."""
        name = name.lower()
        if "$" in name:
            await ctx.send("Please replace $ with S. If the player already exists, replace it with @.")
            return
        args = args.replace("\u201c", '"').replace("\u201d", '"')

        try:
            defaults = {
                "club": "no club",
                "sp1name": "", "sp1skills": "",
                "sp2name": "", "sp2skills": "",
                "sp3name": "", "sp3skills": "",
                "sp4name": "", "sp4skills": "",
                "sp5name": "", "sp5skills": "",
                "nerf": "",
                "pr": 9999,
                "teamdeck": "",
                "charbats": 0,
                "toolbats": 0,
                "source": "",
            }

            if args:
                for arg in shlex.split(args):
                    key, value = map(str.strip, arg.split("=", 1))
                    defaults[key.lower()] = value.lower()

            defaults["pr"] = int(defaults["pr"])
            defaults["charbats"] = int(defaults["charbats"])
            defaults["toolbats"] = int(defaults["toolbats"])

            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
            existing_player = cursor.fetchone()

            if existing_player:
                await ctx.send(f"The player '{name}' already exists in the database. No changes made.")
            else:
                cursor.execute(
                    """
                    INSERT INTO Player (
                        Name, Club_Name, SP1_Name, SP1_Skills,
                        SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                        SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                        Nerf, PR, last_updated, nerf_updated, team_name, charbats, toolbats, source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            CURRENT_DATE, CURRENT_DATE, %s, %s, %s, %s)
                    """,
                    (
                        name,
                        defaults["club"],
                        defaults["sp1name"], defaults["sp1skills"],
                        defaults["sp2name"], defaults["sp2skills"],
                        defaults["sp3name"], defaults["sp3skills"],
                        defaults["sp4name"], defaults["sp4skills"],
                        defaults["sp5name"], defaults["sp5skills"],
                        defaults["nerf"],
                        defaults["pr"],
                        defaults["teamdeck"],
                        defaults["charbats"],
                        defaults["toolbats"],
                        defaults["source"],
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
        """Update the nerf value for a player."""
        player_name = player_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET Nerf = %s, nerf_updated = CURRENT_DATE WHERE Name = %s",
                    (new_nerf, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
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
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute("DELETE FROM Player WHERE Name = %s", (player_name,))
                self.connection.commit()
                await ctx.send(f"Player '{player_name}' has been deleted from the database.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatesp(self, ctx, player_name: str, sp_number: int, sp_name: str, sp_skills: str):
        """Update a player's special player skill slot."""
        player_name = player_name.lower()
        try:
            if sp_number < 1 or sp_number > 5:
                await ctx.send("Invalid SP number. Please specify a number from 1 to 5.")
                return

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                sp_name_col = f"SP{sp_number}_Name"
                sp_skills_col = f"SP{sp_number}_Skills"

                cursor.execute(
                    f"UPDATE Player SET {sp_name_col} = %s, {sp_skills_col} = %s WHERE Name = %s",
                    (sp_name, sp_skills, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatepr(self, ctx, player_name: str, new_pr: int):
        """Update a player's PR (Power Rating)."""
        player_name = player_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET PR = %s, last_updated = CURRENT_DATE WHERE Name = %s",
                    (new_pr, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updateprs(self, ctx, *, args: str = ""):
        """Update PRs for multiple players. Args must be pairs: player_name PR_value ..."""
        try:
            parsed_args = shlex.split(args)

            if len(parsed_args) % 2 != 0:
                await ctx.send("Error: Arguments must be in pairs: player_name PR_value.")
                return

            updates = []
            for i in range(0, len(parsed_args), 2):
                player_name = parsed_args[i].lower()
                try:
                    pr_value = int(parsed_args[i + 1])
                except ValueError:
                    await ctx.send(f"Error: '{parsed_args[i + 1]}' is not a valid integer for PR value.")
                    return
                updates.append((player_name, pr_value))

            with self.connection.cursor() as cursor:
                for player_name, pr_value in updates:
                    cursor.execute("SELECT Name FROM Player WHERE Name = %s", (player_name,))
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE Player SET PR = %s WHERE Name = %s",
                            (pr_value, player_name),
                        )
                        await ctx.send(f"Updated PR for **{player_name}** to **{pr_value}**.")
                    else:
                        await self.addplayer(ctx, player_name, args=f"pr={pr_value}")
                        await ctx.send(f"Player **{player_name}** does not exist in the database.")

                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatechar(self, ctx, player_name: str, new_char: int):
        """Update a player's charisma bats count."""
        player_name = player_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET charbats = %s, last_updated = CURRENT_DATE WHERE Name = %s",
                    (new_char, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updatetool(self, ctx, player_name: str, new_tool: int):
        """Update a player's five-tool bats count."""
        player_name = player_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET toolbats = %s, last_updated = CURRENT_DATE WHERE Name = %s",
                    (new_tool, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def updateclub(self, ctx, player_name: str, new_club: str):
        """Change a player's club."""
        player_name = player_name.lower()
        new_club = new_club.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (new_club,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO Club (Club_Name) VALUES (%s)", (new_club,))

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
        """Change the team deck assignment of a player."""
        player_name = player_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{player_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET team_name = %s, last_updated = CURRENT_DATE WHERE Name = %s",
                    (new_team_name, player_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, player_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def renameplayer(self, ctx, old_name: str, new_name: str):
        """Rename a player in the database."""
        old_name = old_name.lower()
        new_name = new_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (old_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{old_name}'.")
                    return

                cursor.execute("SELECT * FROM Player WHERE Name = %s", (new_name,))
                if cursor.fetchone():
                    await ctx.send(f"The name '{new_name}' is already taken by another player.")
                    return

                cursor.execute(
                    "UPDATE Player SET Name = %s, last_updated = CURRENT_DATE WHERE Name = %s",
                    (new_name, old_name),
                )
                self.connection.commit()
                await self.scoutplayer(ctx, new_name)
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def listplayers(self, ctx):
        """List the 10 most recently added players and the total count."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM Player")
                total_players = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT Name
                    FROM Player
                    OFFSET GREATEST((SELECT COUNT(*) FROM Player) - 10, 0)
                    """
                )
                players = cursor.fetchall()

                if players:
                    playerlist = "\n".join([p[0] for p in players])
                    await ctx.send(
                        f"**Total Players in the Database:** {total_players}\n\n"
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
        Example: !updateplayer John club=NewClub nerf=yes pr=9000
        """
        name = name.lower()
        args = args.replace("\u201c", '"').replace("\u201d", '"')
        try:
            column_mapping = {
                "club": "club_name",
                "nerf": "nerf",
                "pr": "pr",
                "teamdeck": "team_name",
                "sp1n": "sp1_name", "sp1s": "sp1_skills",
                "sp2n": "sp2_name", "sp2s": "sp2_skills",
                "sp3n": "sp3_name", "sp3s": "sp3_skills",
                "sp4n": "sp4_name", "sp4s": "sp4_skills",
                "sp5n": "sp5_name", "sp5s": "sp5_skills",
                "char": "charbats",
                "tool": "toolbats",
                "source": "source",
            }

            updates = {}
            if args:
                for arg in shlex.split(args):
                    key, value = map(str.strip, arg.split("=", 1))
                    key = key.lower()
                    if key in column_mapping:
                        updates[column_mapping[key]] = value.lower()

            update_query_parts = []
            update_values = []
            for column, value in updates.items():
                if column == "pr":
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

            update_values.append(name)

            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
                if not cursor.fetchone():
                    await ctx.send(f"No player found with the name '{name}'.")
                    return

                update_query = ", ".join(update_query_parts)
                cursor.execute(
                    f"UPDATE Player SET {update_query}, last_updated = CURRENT_DATE WHERE Name = %s",
                    update_values,
                )
                self.connection.commit()
                await ctx.send(f"Updated player '{name}' with the following changes: {updates}")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    def _normalize_player_df(self, df):
        """Normalize column types and fill defaults for a player upload DataFrame."""
        df["Name"] = df["Name"].astype(str).str.lower().str.replace(" ", "").str.replace("$", "s")
        df["Club_Name"] = df["Club_Name"].fillna("no club").astype(str).str.lower()
        df.loc[df["Club_Name"] != "no club", "Club_Name"] = (
            df["Club_Name"].str.replace(" ", "", regex=False)
        )
        df.fillna({
            "SP1_name": "", "SP1_skills": "",
            "SP2_name": "", "SP2_skills": "",
            "SP3_name": "", "SP3_skills": "",
            "SP4_name": "", "SP4_skills": "",
            "SP5_name": "", "SP5_skills": "",
            "Team_Name": "",
            "Nerf": "",
            "PR": 9999,
            "charbats": 10,
            "toolbats": 10,
            "source": "",
        }, inplace=True)
        df["charbats"] = df["charbats"].astype(int)
        df["toolbats"] = df["toolbats"].astype(int)
        return df

    def _ensure_club_exists(self, cursor, club_name):
        """Insert the club if it doesn't already exist."""
        cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Club (Club_Name) VALUES (%s)", (club_name,))

    def _upsert_player_row(self, cursor, row):
        """Insert or update a single player row."""
        cursor.execute(
            """
            INSERT INTO Player (
                Name, Club_Name,
                SP1_name, SP1_skills, SP2_name, SP2_skills,
                SP3_name, SP3_skills, SP4_name, SP4_skills,
                SP5_name, SP5_skills, Nerf, PR, team_name,
                charbats, toolbats, source, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            ON CONFLICT (Name) DO UPDATE SET
                Club_Name = EXCLUDED.Club_Name,
                SP1_name  = CASE WHEN EXCLUDED.SP1_name  IS NOT NULL THEN EXCLUDED.SP1_name  ELSE Player.SP1_name  END,
                SP1_skills= CASE WHEN EXCLUDED.SP1_skills IS NOT NULL THEN EXCLUDED.SP1_skills ELSE Player.SP1_skills END,
                SP2_name  = CASE WHEN EXCLUDED.SP2_name  IS NOT NULL THEN EXCLUDED.SP2_name  ELSE Player.SP2_name  END,
                SP2_skills= CASE WHEN EXCLUDED.SP2_skills IS NOT NULL THEN EXCLUDED.SP2_skills ELSE Player.SP2_skills END,
                SP3_name  = CASE WHEN EXCLUDED.SP3_name  IS NOT NULL THEN EXCLUDED.SP3_name  ELSE Player.SP3_name  END,
                SP3_skills= CASE WHEN EXCLUDED.SP3_skills IS NOT NULL THEN EXCLUDED.SP3_skills ELSE Player.SP3_skills END,
                SP4_name  = CASE WHEN EXCLUDED.SP4_name  IS NOT NULL THEN EXCLUDED.SP4_name  ELSE Player.SP4_name  END,
                SP4_skills= CASE WHEN EXCLUDED.SP4_skills IS NOT NULL THEN EXCLUDED.SP4_skills ELSE Player.SP4_skills END,
                SP5_name  = CASE WHEN EXCLUDED.SP5_name  IS NOT NULL THEN EXCLUDED.SP5_name  ELSE Player.SP5_name  END,
                SP5_skills= CASE WHEN EXCLUDED.SP5_skills IS NOT NULL THEN EXCLUDED.SP5_skills ELSE Player.SP5_skills END,
                Nerf      = CASE WHEN EXCLUDED.Nerf      IS NOT NULL THEN EXCLUDED.Nerf      ELSE Player.Nerf      END,
                PR        = CASE WHEN EXCLUDED.PR <> 9999            THEN EXCLUDED.PR        ELSE Player.PR        END,
                team_name = CASE WHEN EXCLUDED.team_name IS NOT NULL THEN EXCLUDED.team_name ELSE Player.team_name END,
                charbats  = CASE WHEN EXCLUDED.charbats  <> 10       THEN EXCLUDED.charbats  ELSE Player.charbats  END,
                toolbats  = CASE WHEN EXCLUDED.toolbats  <> 10       THEN EXCLUDED.toolbats  ELSE Player.toolbats  END,
                source    = CASE WHEN EXCLUDED.source    IS NOT NULL THEN EXCLUDED.source    ELSE Player.source    END,
                last_updated = CURRENT_DATE
            """,
            (
                row["Name"], row["Club_Name"],
                row.get("SP1_name", ""), row.get("SP1_skills", ""),
                row.get("SP2_name", ""), row.get("SP2_skills", ""),
                row.get("SP3_name", ""), row.get("SP3_skills", ""),
                row.get("SP4_name", ""), row.get("SP4_skills", ""),
                row.get("SP5_name", ""), row.get("SP5_skills", ""),
                row["Nerf"], row["PR"], row.get("Team_Name", ""),
                row["charbats"], row["toolbats"], row.get("source", ""),
            )
        )

    async def upload_to_database(self, file_stream):
        """Parse an Excel file and upsert all player rows into the database."""
        df = pd.read_excel(file_stream, engine="openpyxl")
        df = self._normalize_player_df(df)

        cursor = self.connection.cursor()
        try:
            for _, row in df.iterrows():
                try:
                    self._ensure_club_exists(cursor, row["Club_Name"])
                    self._upsert_player_row(cursor, row)
                except Exception as row_error:
                    print(f"Error processing row: {row.to_dict()} - {row_error}")
            self.connection.commit()
        except Exception as db_error:
            self.connection.rollback()
            raise db_error
        finally:
            cursor.close()


    @commands.command()
    async def upload(self, ctx):
        """Upload player data from an attached Excel file."""
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please attach an Excel file with the command!")
            return

        message = await ctx.send("Data is uploading. Please do not interrupt.")
        attachment = ctx.message.attachments[0]
        file_stream = BytesIO()
        await attachment.save(file_stream)
        file_stream.seek(0)

        try:
            await self.upload_to_database(file_stream)
            await message.edit(content="Data successfully uploaded to the database! You can scout now.")
        except Exception as e:
            await message.edit(content=f"Error: {e}")


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(PlayerCommands(bot, connection))
