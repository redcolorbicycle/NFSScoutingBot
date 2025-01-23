import discord
from discord.ext import commands
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib import rcParams
import shlex
import numpy as np
from io import BytesIO

class RankedBatStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Initialize PaddleOCR for English

    
        
    @commands.command()
    async def testocr(self, ctx):
        attachments = ctx.message.attachments
        for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                data = self.parse_image(image_data)
                await ctx.send(data)

    @commands.command()
    async def batters(self, ctx):
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images: first 2 for the initial state, last 2 for the final state.")
            return

        try:
            discord_id = ctx.author.id
            await ctx.send("Please wait...")

            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM rankedbatstats WHERE DISCORDID = %s;",
                    (discord_id,)
                )

            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                data = self.parse_image(image_data)
                try:
                    timing = "before" if i <= 1 else "after"
                    self.process_insert(data, discord_id, timing)
                except Exception as e:
                    self.connection.rollback()
                    await ctx.send(f"An error occurred: {e}")

            await ctx.send("Data has been updated!")
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")







   
    

    def process_insert(self, raw_data, discord_id, timing):
        try:
            data = []
            newrow = []
            print(raw_data)
            for i in range(len(raw_data)):
                if raw_data[i][0].isupper() or (raw_data[i][0:2] == "0." and raw_data[i][2].isalpha()):
                    newrow = [raw_data[i]]
                    continue
                elif len(newrow) in [1, 2, 3, 4, 5, 6, 7]:
                    newrow.append(raw_data[i])
                if len(newrow) == 8:
                    if newrow[-1] == "0":
                        newrow.append("0")
                    else:
                        newrow.append(raw_data[i + 1])
                    data.append(newrow)
                    newrow = []
            print(data)

                


            # Insert rows into the database
            with self.connection.cursor() as cursor:
                for row in data:
                    cursor.execute(
                        """
                        INSERT INTO rankedbatstats (
                            DISCORDID, PLAYERNAME, AB, H, BB, SLG, K, HR, SB, SBPCT, TIMING
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (DISCORDID, PLAYERNAME, TIMING) DO NOTHING;
                        """,
                        (discord_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], timing)
                    )
                self.connection.commit()
            print(f"Inserted {len(data)} rows into the database.")


        except Exception as e:
            self.connection.rollback()
            print(f"Error processing and inserting data: {e}")
            

    @commands.command()
    async def rankedbat(self, ctx):
        """
        Compares 'before' and 'after' stats for each player and returns a table image with the differences.
        """
        discord_id = ctx.author.id
        try:
            with self.connection.cursor() as cursor:
                # Execute the SQL query to fetch and calculate differences
                cursor.execute(
                    """
                    SELECT a.PLAYERNAME,
                        b.AB - a.AB AS diff_AB,
                        b.H - a.H AS diff_H,
                        b.HR - a.HR AS diff_HR,
                        b.BB - a.BB AS diff_BB,
                        b.SLG * b.AB - a.SLG * a.AB AS diff_BASES,
                        b.SB - a.SB AS diff_SB,
                        CASE 
                            WHEN b.SBPCT > 0 AND a.SBPCT > 0 THEN 
                                ROUND((CAST(b.SB AS FLOAT) / CAST(b.SBPCT AS FLOAT)) * 100) - 
                                ROUND((CAST(a.SB AS FLOAT) / CAST(a.SBPCT AS FLOAT)) * 100)
                            ELSE 0
                        END AS diff_SBA,
                        b.K - a.K AS diff_K
                    FROM rankedbatstats a
                    JOIN rankedbatstats b
                    ON a.PLAYERNAME = b.PLAYERNAME
                    WHERE a.DISCORDID = %s
                    AND b.DISCORDID = %s
                    AND a.TIMING = 'before'
                    AND b.TIMING = 'after';

                    """,
                    (discord_id, discord_id)
                )



                # Fetch results
                results = cursor.fetchall()

                if not results:
                    await ctx.send("No matching records found for comparison.")
                    return

                # Process data into a DataFrame
                data = []
                for row in results:
                    player_name = row[0]
                    diff_AB = row[1]
                    diff_H = row[2]
                    diff_HR = row[3]
                    diff_BB = row[4]
                    diff_BASES = row[5]
                    diff_SB = row[6]
                    diff_SBA = row[7]
                    diff_K = row[8]


                    # Calculate metrics
                    avg = round(diff_H / diff_AB, 3) if diff_AB > 0 else 0
                    walkrate = round(diff_BB / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) > 0 else 0
                    walkrate *= 100
                    walkrate = round(walkrate, 1)
                    obp = round((diff_H + diff_BB) / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) > 0 else 0
                    hrrate = round(diff_HR / diff_AB, 3) if diff_AB > 0 else 0
                    hrrate *= 100
                    hrrate = round(hrrate, 1)
                    slg = round(diff_BASES / diff_AB, 3) if diff_AB > 0 else 0
                    ops = round(obp + slg, 3)
                    sbrate = round(diff_SB / diff_SBA, 3) if (diff_SBA > 0 and diff_SB > 0) else 0
                    sbrate *= 100
                    sbrate = round(sbrate, 1)
                    krate = round(diff_K/diff_AB, 3) if diff_AB > 0 else 0
                    krate *= 100
                    krate = round(krate, 1)

                    # Append the row
                    data.append([
                        player_name, diff_AB, avg, diff_BB, walkrate, diff_K, krate, obp,
                        diff_HR, hrrate, slg, ops, diff_SB, sbrate
                    ])

                # Define column headers
                columns = [
                    "Player Name", "AB", "Avg", "BB", "BB%", "K", "K%", "OBP",
                    "HR", "HR%", "SLG", "OPS", "SB", "SB%"
                ]

                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)

                # Sort DataFrame by OPS (optional)
                df = df.sort_values(by="OPS", ascending=False)

                # Plot the table using matplotlib
                fig, ax = plt.subplots(figsize=(24, len(df) * 0.5 + 1))  # Adjust size dynamically
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
                for (row, col), cell in cell_dict.items():
                    if row == 0 or col == 0:
                        cell.set_text_props(weight="bold")

                row_height = 1 / len(df)  # Divide the figure height by the number of rows
                for (row, col), cell in cell_dict.items():
                    cell.set_height(row_height)  # Set height dynamically

                # Save the table as an image in memory
                buffer = BytesIO()
                plt.savefig(buffer, format="png", bbox_inches="tight")
                buffer.seek(0)
                plt.close(fig)

                # Send the image to Discord
                file = discord.File(fp=buffer, filename="stats_comparison.png")
                await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"Error comparing stats: {e}")


            

    def fetch(self, discord_id):
        """
        Retrieves all rows where the same PLAYERNAME appears in both TIMING = 'before' and TIMING = 'after'.
        """
        try:
            with self.connection.cursor() as cursor:
                # Execute the SELECT query
                cursor.execute(
                    """
                    SELECT a.*, 
                    FROM rankedbatstats a
                    JOIN rankedbatstats b
                    ON a.PLAYERNAME = b.PLAYERNAME
                    WHERE a.DISCORDID = %s
                    AND b.DISCORDID = %s
                    AND a.TIMING = 'before'
                    AND b.TIMING = 'after';

                    """,
                    (discord_id, discord_id)
                )
                # Fetch all matching rows
                rowsbefore = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT b.*, 
                    FROM rankedbatstats a
                    JOIN rankedbatstats b
                    ON a.PLAYERNAME = b.PLAYERNAME
                    WHERE a.DISCORDID = %s
                    AND b.DISCORDID = %s
                    AND a.TIMING = 'before'
                    AND b.TIMING = 'after';

                    """,
                    (discord_id, discord_id)
                )
                # Fetch all matching rows
                rowsafter = cursor.fetchall()
                return (rowsbefore, rowsafter)
            
        except Exception as e:
            print(f"Error retrieving common players: {e}")
            return []


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedBatStats(bot, connection))
