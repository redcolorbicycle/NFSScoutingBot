from discord.ext import commands
import pandas as pd
from io import BytesIO
import discord
import shlex

from bot_commands.utils import render_table_image, send_paginated_table
from bot_commands.constants import LEADERSHIP_ROLES, ROWS_PER_PAGE


class ClubCommands(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.banned_user_ids = {965282028943736893}  # Add more IDs as needed

    async def cog_check(self, ctx):
        user_roles = [role.name for role in ctx.author.roles]

        if ctx.author.id in self.banned_user_ids:
            return False

        return any(role in LEADERSHIP_ROLES for role in user_roles)


    @commands.command()
    async def addclub(self, ctx, club_name: str):
        """Add a new club to the database."""
        try:
            cursor = self.connection.cursor()
            club_name = club_name.lower()

            cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
            existing_club = cursor.fetchone()

            if existing_club:
                await ctx.send(f"The club '{club_name}' already exists in the database.")
            else:
                cursor.execute(
                    "INSERT INTO Club (Club_Name) VALUES (%s)",
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
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (old_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No club found with the name '{old_name}'.")
                    return

                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (new_name,))
                if cursor.fetchone():
                    await ctx.send(f"The name '{new_name}' is already taken by another club.")
                    return

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
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No club found with the name '{club_name}'.")
                    return

                cursor.execute("SELECT COUNT(*) FROM Player WHERE Club_Name = %s", (club_name,))
                player_count = cursor.fetchone()[0]

                if player_count > 0:
                    await ctx.send(f"The club '{club_name}' cannot be deleted because it has {player_count} players.")
                    return

                cursor.execute("DELETE FROM Club WHERE Club_Name = %s", (club_name,))
                self.connection.commit()
                await ctx.send(f"Club '{club_name}' has been successfully deleted.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def listclubs(self, ctx):
        """List the 10 most recently added clubs and the total count."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM Club")
                total_clubs = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT Club_Name
                    FROM Club
                    OFFSET GREATEST((SELECT COUNT(*) FROM Club) - 10, 0)
                    """
                )
                recent_clubs = cursor.fetchall()

                if recent_clubs:
                    club_list = "\n".join([club[0] for club in recent_clubs])
                    await ctx.send(
                        f"**Total Clubs in the Database:** {total_clubs}\n\n"
                        f"**10 Most Recently Added Clubs:**\n{club_list}"
                    )
                else:
                    await ctx.send("No clubs found in the database.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def scoutclub(self, ctx, club_name: str):
        """Fetch player details for a club and return as a table image."""
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT Name, sp1_name, sp1_skills, sp2_name, sp2_skills, sp3_name, sp3_skills,
                           sp4_name, sp4_skills, sp5_name, sp5_skills, Nerf, PR,
                           last_updated, charbats, toolbats, source
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return

                processed_players = [
                    (
                        player[0],
                        f"{player[1]} ({player[2]})",   # SP1
                        f"{player[3]} ({player[4]})",   # SP2
                        f"{player[5]} ({player[6]})",   # SP3
                        f"{player[7]} ({player[8]})",   # SP4
                        f"{player[9]} ({player[10]})",  # SP5
                        player[11],  # Nerf
                        player[12],  # PR
                        player[14],  # Char
                        player[15],  # Tool
                        player[16],  # Source
                        player[13],  # Last Updated
                    )
                    for player in players
                ]

                columns = ["Name", "SP1 Info", "SP2 Info", "SP3 Info", "SP4 Info", "SP5 Info",
                           "Nerf", "PR", "Char", "Tool", "Source", "Last Updated"]
                df = pd.DataFrame(processed_players, columns=columns)
                df = df.sort_values(by="PR")

                buffer = render_table_image(df, pr_col_index=columns.index("PR"))
                await ctx.send("Applebee's 🍎")
                await ctx.send(file=discord.File(fp=buffer, filename="club_table.png"))
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def scoutclubez(self, ctx, club_name: str):
        """Fetch simplified player details for a club as a table image."""
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT Name, Nerf, PR, charbats, toolbats, last_updated, nerf_updated, team_name
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return

                columns = ["Name", "Nerf", "PR", "Char", "Tool", "Last Updated", "Nerf Updated", "Team Deck"]
                df = pd.DataFrame(players, columns=columns)
                df = df.sort_values(by="PR")

                buffer = render_table_image(
                    df, figwidth=5, figheight_per_row=2, fontsize=20, dpi=200,
                    pr_col_index=columns.index("PR"),
                )
                await ctx.send(file=discord.File(fp=buffer, filename="club_table.png"))
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def scoutclubtext(self, ctx, club_name: str):
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT Name, Nerf, PR, team_name
                    FROM Player
                    WHERE Club_Name = %s
                    ORDER BY PR ASC;
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
            await ctx.send(f"**Players in {club_name}:**\n{player_details}")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def addtoclub(self, ctx, club_name: str, *, args: str = ""):
        player_commands_cog = self.bot.get_cog("PlayerCommands")
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                if args:
                    parsed_args = shlex.split(args)

                    for player_name in parsed_args:
                        player_name = player_name.lower()
                        cursor.execute(
                            "SELECT Name FROM Player WHERE Name = %s",
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
                                await player_commands_cog.addplayer(ctx, player_name, args=f"club={club_name}")
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


    @commands.command()
    async def clearclub(self, ctx, club_name: str):
        """Remove all players from the specified club by setting their Club_Name to 'no club'."""
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
                if not cursor.fetchone():
                    await ctx.send(f"No club found with the name '{club_name}'.")
                    return

                cursor.execute("SELECT COUNT(*) FROM Player WHERE Club_Name = %s", (club_name,))
                player_count = cursor.fetchone()[0]

                if player_count == 0:
                    await ctx.send(f"No players are currently in the club '{club_name}'.")
                    return

                cursor.execute(
                    "UPDATE Player SET Club_Name = 'no club' WHERE Club_Name = %s",
                    (club_name,),
                )
                self.connection.commit()
                await ctx.send(f"✅ Cleared {player_count} players from '{club_name}' and set them to 'no club'.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def scoutclubtrial(self, ctx, club_name: str):
        """Fetch player details for a club as a paginated table image."""
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT Name, sp1_name, sp1_skills, sp2_name, sp2_skills, sp3_name, sp3_skills,
                           sp4_name, sp4_skills, sp5_name, sp5_skills, Nerf, PR,
                           Most_Common_Batting_Skill, last_updated
                    FROM Player
                    WHERE Club_Name = %s
                    """,
                    (club_name,),
                )
                players = cursor.fetchall()

                if not players:
                    await ctx.send(f"No players found for the club '{club_name}'.")
                    return

                processed_players = [
                    (
                        player[0],
                        f"{player[1]} ({player[2]})",   # SP1
                        f"{player[3]} ({player[4]})",   # SP2
                        f"{player[5]} ({player[6]})",   # SP3
                        f"{player[7]} ({player[8]})",   # SP4
                        f"{player[9]} ({player[10]})",  # SP5
                        player[11],  # Nerf
                        player[12],  # PR
                        player[13],  # Batting Skill
                        player[14],  # Last Updated
                    )
                    for player in players
                ]

                columns = ["Name", "SP1 Info", "SP2 Info", "SP3 Info", "SP4 Info", "SP5 Info",
                           "Nerf", "PR", "Batting Skill", "Last Updated"]
                df = pd.DataFrame(processed_players, columns=columns)
                df = df.sort_values(by="PR")

                await send_paginated_table(
                    ctx, df, rows_per_page=ROWS_PER_PAGE,
                    pr_col_index=columns.index("PR"),
                )
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def uploadbattles(self, ctx):
        """
        Upload battle records from an Excel file to the GoldyBattles table.
        Expected columns: Player Name or Name, PR, Attacking Club, Defending Club, Date, Wins, Non Wins
        """
        if not ctx.message.attachments:
            await ctx.send("Please attach an Excel file (.xlsx) to upload battle data.")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".xlsx"):
            await ctx.send("Only Excel (.xlsx) files are supported.")
            return

        try:
            file_bytes = await attachment.read()
            df = pd.read_excel(BytesIO(file_bytes))

            df.columns = [col.strip().lower() for col in df.columns]

            if "player name" in df.columns:
                df.rename(columns={"player name": "player_name"}, inplace=True)
            elif "name" in df.columns:
                df.rename(columns={"name": "player_name"}, inplace=True)

            rename_map = {
                "pr": "pr",
                "attacking club": "home_club",
                "defending club": "opponent_club",
                "date": "battle_date",
                "wins": "wins",
                "non wins": "nonwins"
            }
            df.rename(columns=rename_map, inplace=True)

            required_cols = ["player_name", "pr", "home_club", "opponent_club", "battle_date", "wins", "nonwins"]
            for col in required_cols:
                if col not in df.columns:
                    await ctx.send(f"Missing column: `{col}`")
                    return

            df.dropna(subset=["player_name", "battle_date"], inplace=True)
            df["battle_date"] = pd.to_datetime(df["battle_date"], dayfirst=True).dt.date

            insert_query = """
                INSERT INTO GoldyBattles (
                    player_name, pr, home_club, opponent_club, battle_date, wins, nonwins
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name, battle_date)
                DO UPDATE SET
                    pr = EXCLUDED.pr,
                    home_club = EXCLUDED.home_club,
                    opponent_club = EXCLUDED.opponent_club,
                    wins = EXCLUDED.wins,
                    nonwins = EXCLUDED.nonwins;
            """

            inserted = 0
            with self.connection.cursor() as cursor:
                for _, row in df.iterrows():
                    cursor.execute(
                        insert_query,
                        (
                            row["player_name"].strip().lower(),
                            int(row["pr"]) if not pd.isna(row["pr"]) else None,
                            row["home_club"],
                            row["opponent_club"],
                            row["battle_date"],
                            int(row["wins"]) if not pd.isna(row["wins"]) else 0,
                            int(row["nonwins"]) if not pd.isna(row["nonwins"]) else 0,
                        )
                    )
                    inserted += 1
                self.connection.commit()

            await ctx.send(f"✅ Uploaded {inserted} battle records to `GoldyBattles`.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"❌ Upload failed: {e}")


    @commands.command()
    async def scoutwinrate(self, ctx, *, opponent_club: str):
        """
        Show daily win rate against a given defending club.
        Usage: !scoutwinrate <club name>
        """
        opponent_club = opponent_club.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT battle_date,
                        SUM(wins) AS total_wins,
                        SUM(nonwins) AS total_nonwins
                    FROM GoldyBattles
                    WHERE LOWER(opponent_club) = %s
                    GROUP BY battle_date
                    ORDER BY battle_date;
                    """,
                    (opponent_club,)
                )
                rows = cursor.fetchall()

                if not rows:
                    await ctx.send(f"No battle records found against '{opponent_club}'.")
                    return

                lines = []
                for date, wins, nonwins in rows:
                    total = wins + nonwins
                    winrate = wins / total if total > 0 else 0
                    lines.append(f"📅 {date}: **{winrate:.2%}** ({wins}W / {nonwins}L)")

                await ctx.send(f"🎯 **Win Rate vs `{opponent_club}` by Date:**\n" + "\n".join(lines))
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"❌ Error fetching win rate: {e}")


    @commands.command()
    async def deletebattles(self, ctx, battle_date: str, home_club: str):
        """
        Delete all GoldyBattles for a given date and home club.
        Usage: !deletebattles <dd/mm/yy> <home club>
        """
        home_club = home_club.lower()
        try:
            parsed_date = pd.to_datetime(battle_date, dayfirst=True).date()

            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM GoldyBattles
                    WHERE battle_date = %s AND LOWER(home_club) = %s
                    """,
                    (parsed_date, home_club)
                )
                deleted_count = cursor.rowcount
                self.connection.commit()

            await ctx.send(f"🗑️ Deleted {deleted_count} records for `{home_club}` on `{parsed_date}`.")
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"❌ Error deleting battles: {e}")


    @commands.command()
    async def scoutmatchup(self, ctx, opponent_club: str, battle_date: str):
        """
        Show all player matchups and team summary vs a defending club on a specific date.
        Usage: !scoutmatchup <defending club> <dd/mm/yyyy>
        """
        opponent_club = opponent_club.lower()
        try:
            parsed_date = pd.to_datetime(battle_date, dayfirst=True).date()

            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT player_name, home_club, wins, nonwins
                    FROM GoldyBattles
                    WHERE LOWER(opponent_club) = %s AND battle_date = %s
                    ORDER BY home_club, wins DESC
                    """,
                    (opponent_club, parsed_date)
                )
                matchups = cursor.fetchall()

                if not matchups:
                    await ctx.send(f"No matchups found against `{opponent_club}` on `{parsed_date}`.")
                    return

                lines = []
                team_totals = {}
                for player_name, home_club, wins, nonwins in matchups:
                    total = wins + nonwins
                    winrate = wins / total if total > 0 else 0
                    lines.append(
                        f"🏅 **{player_name}** ({home_club}) — {wins}W / {nonwins}NW → **{winrate:.0%}**"
                    )
                    if home_club not in team_totals:
                        team_totals[home_club] = [0, 0]
                    team_totals[home_club][0] += wins
                    team_totals[home_club][1] += nonwins

                summary_lines = []
                for team, (w, nw) in sorted(team_totals.items(), key=lambda x: -x[1][0]):
                    total = w + nw
                    wr = w / total if total > 0 else 0
                    summary_lines.append(f"🏟️ `{team}` — {w}W / {nw}NW → **{wr:.0%}**")

                await ctx.send(f"📋 Matchups vs `{opponent_club}` on {parsed_date}:")
                await ctx.send("\n".join(lines))
                await ctx.send("\n📊 **Team Summary:**")
                await ctx.send("\n".join(summary_lines))
        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"❌ Error retrieving matchup: {e}")


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(ClubCommands(bot, connection))
