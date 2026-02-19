from discord.ext import commands
import pandas as pd
from io import BytesIO
import discord

from bot_commands.utils import send_paginated_table
from bot_commands.constants import BATTLE_LOG_ROLES, ROWS_PER_PAGE, BATTLE_LOG_TEMPLATE


class BattleLog(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    async def cog_check(self, ctx):
        """Restrict commands to users with specific roles."""
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in BATTLE_LOG_ROLES for role in user_roles)


    @commands.command()
    async def logsheet(self, ctx):
        """Send the battle log template Excel file."""
        try:
            await ctx.send(file=discord.File(BATTLE_LOG_TEMPLATE, filename=BATTLE_LOG_TEMPLATE))
        except Exception as e:
            await ctx.send(f"Error: Could not send the file. {e}")


    @commands.command()
    async def analyse(self, ctx, club_name: str):
        """Display win, loss, and draw records against a specified opponent club."""
        club_name = club_name.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        battle_date,
                        player_club AS home_club,
                        COUNT(CASE WHEN result = 'w' THEN 1 END) AS total_wins,
                        COUNT(CASE WHEN result = 'l' THEN 1 END) AS total_losses,
                        COUNT(CASE WHEN result = 'd' THEN 1 END) AS total_draws,
                        CASE
                            WHEN COUNT(CASE WHEN result IN ('w','l','d') THEN 1 END) > 0
                            THEN ROUND(
                                COUNT(CASE WHEN result = 'w' THEN 1 END)::decimal * 100 /
                                COUNT(CASE WHEN result IN ('w','l','d') THEN 1 END),
                                2
                            )
                            ELSE 0
                        END AS win_rate
                    FROM club_records
                    WHERE opponent_club = %s
                    GROUP BY battle_date, player_club
                    ORDER BY battle_date;
                    """,
                    (club_name,)
                )
                results = cursor.fetchall()

                if not results:
                    await ctx.send(f"No records found against the opponent club **{club_name}**.")
                    return

                columns = ["Date", "Home Club", "Total Wins", "Total Losses", "Total Draws", "Win Percentage"]
                df = pd.DataFrame(results, columns=columns)
                await send_paginated_table(ctx, df, rows_per_page=ROWS_PER_PAGE)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    def _normalize_battle_df(self, df):
        """Normalize column values for a battle log DataFrame."""
        str_cols = ["Home Club", "Opponent Club", "Player Name", "Opponent Name", "Player Nerf", "Result"]
        for col in str_cols:
            df[col] = df[col].astype(str).str.lower().str.replace(" ", "")
        df["Player SP Number"] = df["Player SP Number"].astype(int)
        df["Opponent SP Number"] = df["Opponent SP Number"].astype(int)
        df["Battle Date"] = df["Battle Date"].astype(str)
        return df

    async def replace_log_to_database(self, file_stream):
        """Parse an Excel file and upsert all battle log rows into the database."""
        df = pd.read_excel(file_stream, engine="openpyxl")
        df = self._normalize_battle_df(df)

        cursor = self.connection.cursor()
        try:
            for _, row in df.iterrows():
                try:
                    cursor.execute(
                        """
                        INSERT INTO club_records (
                            battle_date, player_name, opponent_name, result, opponent_club,
                            player_club, player_sp_number, opponent_sp_number, nerf
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (battle_date, player_name, opponent_name, player_sp_number, opponent_sp_number)
                        DO UPDATE SET
                            result = EXCLUDED.result,
                            opponent_club = EXCLUDED.opponent_club,
                            player_club = EXCLUDED.player_club,
                            nerf = EXCLUDED.nerf
                        """,
                        (
                            row["Battle Date"],
                            row["Player Name"],
                            row["Opponent Name"],
                            row["Result"],
                            row["Opponent Club"],
                            row["Home Club"],
                            row["Player SP Number"],
                            row["Opponent SP Number"],
                            row["Player Nerf"],
                        ),
                    )
                except Exception as row_error:
                    print(f"Error processing row: {row.to_dict()} - {row_error}")

            self.connection.commit()
        except Exception as db_error:
            self.connection.rollback()
            raise db_error
        finally:
            cursor.close()


    @commands.command()
    async def log(self, ctx):
        """Upload battle records from an attached Excel file."""
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please attach an Excel file with the command!")
            return

        message = await ctx.send("Data is uploading. Please do not interrupt.")
        attachment = ctx.message.attachments[0]
        file_stream = BytesIO()
        await attachment.save(file_stream)
        file_stream.seek(0)

        try:
            await self.replace_log_to_database(file_stream)
            await message.edit(content="Data successfully logged!")
        except Exception as e:
            await message.edit(content=f"Error: {e}")


    @commands.command()
    async def analyse_date(self, ctx, battle_date: str, home_club: str, opponent_club: str):
        """Analyse win percentages and SP-specific stats for a specific matchup date."""
        home_club = home_club.lower()
        opponent_club = opponent_club.lower()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        opponent_name,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN result IN ('w','l','d') THEN 1 END), 0),
                            2
                        ) AS overall_win_rate,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' AND opponent_sp_number = 1 THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN opponent_sp_number = 1 THEN 1 END), 0), 2
                        ) AS sp1_win_rate,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' AND opponent_sp_number = 2 THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN opponent_sp_number = 2 THEN 1 END), 0), 2
                        ) AS sp2_win_rate,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' AND opponent_sp_number = 3 THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN opponent_sp_number = 3 THEN 1 END), 0), 2
                        ) AS sp3_win_rate,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' AND opponent_sp_number = 4 THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN opponent_sp_number = 4 THEN 1 END), 0), 2
                        ) AS sp4_win_rate,
                        ROUND(
                            COUNT(CASE WHEN result = 'w' AND opponent_sp_number = 5 THEN 1 END)::decimal * 100 /
                            NULLIF(COUNT(CASE WHEN opponent_sp_number = 5 THEN 1 END), 0), 2
                        ) AS sp5_win_rate,
                        ROUND(AVG(player_sp_number::decimal), 2) AS average_home_sp
                    FROM club_records
                    WHERE
                        battle_date = %s AND
                        LOWER(player_club) = %s AND
                        LOWER(opponent_club) = %s
                    GROUP BY opponent_name
                    ORDER BY overall_win_rate ASC;
                    """,
                    (battle_date, home_club, opponent_club)
                )
                results = cursor.fetchall()

                if not results:
                    await ctx.send(
                        f"No records found for **{home_club}** against **{opponent_club}** on **{battle_date}**."
                    )
                    return

                columns = [
                    "Opponent Name", "Overall Win %", "SP1 Win %", "SP2 Win %",
                    "SP3 Win %", "SP4 Win %", "SP5 Win %", "Average Home SP"
                ]
                df = pd.DataFrame(results, columns=columns)
                await send_paginated_table(ctx, df, rows_per_page=20)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(BattleLog(bot, connection))
