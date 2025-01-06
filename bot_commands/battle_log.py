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

class BattleLog(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    async def cog_check(self, ctx):
        """
        Restrict commands to users with specific roles.
        """
        allowed_roles = [
            "TooDank Leaders", "Vice", "TokyoDrift Leaders", "NFS Ops", "NFS OG Leaders", 
            "NeedForSpeed Leaders", "M16Speed Spy Daddies", "GoldyLeads", "Burnout Leaders", 
            "Dugout Leads", "Kerchoo Leaders", "Rush Hour Leaders", "Speed Bump Leaders", 
            "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad"
        ]
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in allowed_roles for role in user_roles)


    @commands.command()
    async def logsheet(self, ctx):
        # Path to your preformatted Excel file
        file_path = "battlelogs.xlsx"
        
        # Send the file to the user
        try:
            await ctx.send(file=discord.File(file_path, filename="battlelogs.xlsx"))
        except Exception as e:
            await ctx.send(f"Error: Could not send the file. {e}")



    async def upload_log_to_database(self, file_stream):
        # Read the Excel file
        df = pd.read_excel(file_stream, engine="openpyxl")

        # Format the names properly
        df["Home Club"] = df["Home Club"].astype(str)
        df["Home Club"] = df["Home Club"].str.lower().str.replace(" ", "")
        df["Opponent Club"] = df["Opponent Club"].astype(str)
        df["Opponent Club"] = df["Opponent Club"].str.lower().str.replace(" ", "")
        df["Player Name"] = df["Player Name"].astype(str)
        df["Player Name"] = df["Player Name"].str.lower().str.replace(" ", "")
        df["Opponent Name"] = df["Opponent Name"].astype(str)
        df["Opponent Name"] = df["Opponent Name"].str.lower().str.replace(" ", "")
        df["Player Nerf"] = df["Player Nerf"].str.lower().str.replace(" ", "")
        df["Result"] = df["Result"].str.lower().str.replace(" ", "")
        df["Player SP Number"] = df["Player SP Number"].astype(int)
        df["Opponent SP Number"] = df["Opponent SP Number"].astype(int)
        df["Battle Date"] = df["Battle Date"].dt.strftime("%d-%m-%Y")

        try:
            cursor = self.connection.cursor()

            for _, row in df.iterrows():
                try:
                    # Check if the record already exists
                    cursor.execute(
                        """
                        SELECT 1 FROM club_records
                        WHERE battle_date = %s
                        AND player_name = %s
                        AND opponent_name = %s
                        AND player_sp_number = %s
                        AND opponent_sp_number = %s
                        """,
                        (
                            row["Battle Date"],
                            row["Player Name"],
                            row["Opponent Name"],
                            row["Player SP Number"],
                            row["Opponent SP Number"],
                        ),
                    )
                    record_exists = cursor.fetchone()

                    if record_exists:
                        # Skip if record already exists
                        continue

                    # Insert the row into the database
                    cursor.execute(
                        """
                        INSERT INTO club_records (
                            battle_date, player_name, opponent_name, result, opponent_club,
                            player_club, player_sp_number, opponent_sp_number, nerf
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        
            self.connection.commit()  # Commit after processing all rows
        except Exception as db_error:
            self.connection.rollback()  # Rollback on any database error
            raise db_error  # Rethrow for higher-level handling
        finally:
            cursor.close()


    @commands.command()
    async def log(self, ctx):
        # Check if a file is attached
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please attach an Excel file with the command!")
            return

        # Notify that the upload is starting
        message = await ctx.send("Data is uploading. Please do not interrupt.")

        # Get the attached file
        attachment = ctx.message.attachments[0]
        file_stream = BytesIO()
        await attachment.save(file_stream)
        file_stream.seek(0)

        try:
            # Pass the file stream to the upload_to_database function
            await self.upload_log_to_database(file_stream)

            # Notify completion
            await message.edit(content="Data successfully uploaded to the database!")
        except Exception as e:
            await message.edit(content=f"Error: {e}")

    @commands.command()
    async def analyse(self, ctx, club_name: str):
        """
        Analyse and display the win, loss, and draw records against a specified opponent club.
        """
        club_name = club_name.lower()
        rows_per_page = 30  # Number of rows per page
        try:
            with self.connection.cursor() as cursor:
                # Query to fetch date, home club, and total wins, losses, and draws against the specified opponent club
                cursor.execute(
                    """
                    SELECT 
                        battle_date,
                        player_club AS home_club,
                        COUNT(CASE WHEN result = 'w' THEN 1 END) AS total_wins,
                        COUNT(CASE WHEN result = 'l' THEN 1 END) AS total_losses,
                        COUNT(CASE WHEN result = 'd' THEN 1 END) AS total_draws,
                        CASE 
                            WHEN COUNT(CASE WHEN result = 'w' THEN 1 END) + 
                                COUNT(CASE WHEN result = 'l' THEN 1 END) + 
                                COUNT(CASE WHEN result = 'd' THEN 1 END) > 0 
                            THEN ROUND(
                                COUNT(CASE WHEN result = 'w' THEN 1 END)::decimal / 
                                (COUNT(CASE WHEN result = 'w' THEN 1 END) + 
                                COUNT(CASE WHEN result = 'l' THEN 1 END) + 
                                COUNT(CASE WHEN result = 'd' THEN 1 END)), 
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
                # Fetch results
                results = cursor.fetchall()

                # If no records found
                if not results:
                    await ctx.send(f"No records found against the opponent club **{club_name}**.")
                    return

                # Process the data into a DataFrame
                columns = ["Date", "Home Club", "Total Wins", "Total Losses", "Total Draws", "Win Percentage"]
                df = pd.DataFrame(results, columns=columns)

                # Paginate the table
                total_pages = (len(df) + rows_per_page - 1) // rows_per_page
                for page in range(total_pages):
                    start = page * rows_per_page
                    end = start + rows_per_page
                    df_page = df.iloc[start:end]

                    # Plot the table using matplotlib
                    fig, ax = plt.subplots(figsize=(24, len(df_page) * 0.5 + 1))  # Dynamic height based on rows
                    ax.axis("tight")
                    ax.axis("off")
                    table = ax.table(
                        cellText=df_page.values,
                        colLabels=df_page.columns,
                        cellLoc="center",
                        loc="center",
                    )

                    # Adjust table style
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.auto_set_column_width(col=list(range(len(df_page.columns))))

                    # Bold the headers and the first column
                    cell_dict = table.get_celld()
                    for (row, col), cell in cell_dict.items():
                        if row == 0 or col == 0:
                            cell.set_text_props(weight="bold")

                        # Adjust the row height dynamically
                        row_height = 1 / len(df_page)
                        cell.set_height(row_height)

                    # Save the table as an image in memory
                    buffer = BytesIO()
                    plt.savefig(buffer, format="png", bbox_inches="tight")
                    buffer.seek(0)
                    plt.close(fig)

                    # Send the image to Discord
                    file = discord.File(fp=buffer, filename=f"club_table_page_{page + 1}.png")
                    await ctx.send(f"**Page {page + 1} of {total_pages}:**", file=file)

                    buffer.close()
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")



async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(BattleLog(bot, connection))
