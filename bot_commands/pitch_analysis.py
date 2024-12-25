import discord
from discord.ext import commands
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import os
from matplotlib import rcParams
import shlex

class RankedPitchStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.initial_state = set()  # Cache for initial state (rows as tuples)
        self.final_state = set()    # Cache for final state (rows as tuples)
        self.api_key = os.getenv('AZURE_API_KEY')  # Replace with your Azure API key
        self.endpoint = os.getenv('AZURE_ENDPOINT') + '/vision/v3.2/read/analyze'


    def parse_image(self, image_data):
        """
        Extracts tabular data from an image using Azure Computer Vision API.
        """
        try:
            # Correct headers and endpoint
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/octet-stream'
            }

            # Perform the API call
            response = requests.post(self.endpoint, headers=headers, data=image_data)


            # Check for 202 response
            if response.status_code == 202:
                # Extract the Operation-Location header
                operation_location = response.headers["Operation-Location"]

                # Poll for the result
                import time
                while True:
                    result_response = requests.get(operation_location, headers=headers)
                    if result_response.status_code != 200:
                        print(f"Polling failed: {result_response.status_code}, {result_response.text}")
                        return ""

                    result = result_response.json()

                    # Check if the operation is complete
                    if result.get("status") == "succeeded":
                        # Extract text from the result
                        extracted_text = []
                        for read_result in result["analyzeResult"]["readResults"]:
                            for line in read_result["lines"]:
                                extracted_text.append(line["text"])
                        return extracted_text

                    elif result.get("status") == "failed":
                        print("Text extraction failed.")
                        return ""

                    # Wait before polling again
                    time.sleep(1)
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return ""

        except Exception as e:
            print(f"Error using Azure OCR API: {e}")
            return ""


    @commands.command()
    async def pitchers(self, ctx):
        """
        Collect images for initial and final states, process them.
        Attach exactly 4 images to the command.
        """
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images: first 2 for the initial state, last 2 for the final state.")
            return

        try:
            discord_id = ctx.author.id
            await ctx.send(discord_id)
            with self.connection.cursor() as cursor:
                # Execute the DELETE query
                cursor.execute(
                    "DELETE FROM rankedpitchstats WHERE DISCORDID = %s;",
                    (discord_id,)
                )

            # Process each image
            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                data = self.parse_image(image_data)

                # Insert into the database
                try:
                    if i <= 1:
                        timing = "before"
                    else:
                        timing = "after"
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
            
            for i in range(len(raw_data)):
                if raw_data[i][0].isupper(): #for 1
                    newrow = [raw_data[i]]
                    continue
                elif len(newrow) == 1:
                    if "." in raw_data[i]:
                        integer_part, decimal_part = raw_data[i].split(".")
                        if decimal_part == "1":
                            newrow.append(f"{integer_part}.33")
                        elif decimal_part == "2":
                            newrow.append(f"{integer_part}.66")
                        else:
                            newrow.append(raw_data[i])
                else:
                    newrow.append(raw_data[i])
                    data.append(newrow)
                    print(newrow)
            
            # Insert rows into the database
            with self.connection.cursor() as cursor:
                for row in data:
                    cursor.execute(
                        """
                        INSERT INTO rankedpitchstats (
                            DISCORDID, PLAYERNAME, IP, ERA, H, BB, SLG, HR, SO, TIMING, AVG
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (DISCORDID, PLAYERNAME, TIMING) DO NOTHING;
                        """,
                        (discord_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], timing, row[8])
                    )
                self.connection.commit()
            print(f"Inserted {len(data)} rows into the database.")


        except Exception as e:
            self.connection.rollback()
            print(f"Error processing and inserting data: {e}")
            

    @commands.command()
    async def rankedpitch(self, ctx):
        """
        Compares 'before' and 'after' stats for each player and returns a table image with the differences.
        """
        discord_id = ctx.author.id
        try:
            with self.connection.cursor() as cursor:
                # Execute the SQL query to fetch and calculate differences
                cursor.execute(
                    """
                    SELECT 
                        a.PLAYERNAME,
                        innings_converted(b.ip - a.ip) AS diff_IP,
                        CASE 
                            WHEN b.ip - a.ip != 0 THEN 
                                (b.era / 9 * b.ip - a.era / 9 * a.ip) / (b.ip - a.ip) * 9
                            ELSE 0
                        END AS diff_ERA,
                        b.h - a.h AS diff_H,
                        b.bb - a.bb AS diff_BB,
                        CASE 
                            WHEN b.h / b.avg - a.h / a.avg != 0 THEN 
                                (b.slg * b.h / b.avg - a.slg * a.h / a.avg) / (b.h / b.avg - a.h / a.avg)
                            ELSE 0
                        END AS diff_SLG,
                        b.HR - a.HR AS diff_HR,
                        b.SO - a.SO AS diff_SO,
                        CASE 
                            WHEN b.h / b.avg - a.h / a.avg != 0 THEN 
                                (b.h - a.h) / (b.h / b.avg - a.h / a.avg)
                            ELSE 0
                        END AS diff_AVG,
                        CASE 
                            WHEN b.h / b.avg + b.bb - a.h / a.avg - a.bb != 0 THEN 
                                (b.h + b.bb - a.h - a.bb) / (b.h / b.avg + b.bb - a.h / a.avg - a.bb)
                            ELSE 0
                        END AS diff_OBP,
                        b.ip - a.ip AS actualinningdiff
                    FROM rankedpitchstats a
                    JOIN rankedpitchstats b
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
                    diff_IP = row[1]
                    diff_ERA = round(row[2], 2)
                    diff_H = row[3]
                    diff_BB = row[4]
                    diff_SLG = round(row[5], 3)
                    diff_HR = row[6]
                    diff_SO = row[7]
                    diff_AVG = round(row[8], 3)
                    diff_OBP = round(row[9], 8)


                    # Calculate metrics
                    diff_AVG = float(diff_AVG)  # Convert if coming from SQL as a string
                    diff_IP = float(diff_IP)
                    diff_SO = float(diff_SO)
                    diff_AB = float(diff_AB)

                    diff_AB = diff_H / diff_AVG
                    ip = diff_IP 
                    era = diff_ERA
                    avg = diff_AVG if diff_IP > 0 else 0
                    walkrate = round(diff_BB / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) > 0 else 0
                    walkrate *= 100
                    walkrate = round(walkrate, 1)
                    obp = round((diff_H + diff_BB) / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) > 0 else 0
                    hrrate = round(diff_HR / diff_AB, 3) if diff_AB > 0 else 0
                    hrrate *= 100
                    hrrate = round(hrrate, 1)
                    slg = diff_SLG if diff_AB > 0 else 0
                    ops = round(obp + slg, 3)
                    krate = diff_SO / diff_AB
                    krate *= 100
                    krate = round(krate, 1)
                    obp2 = diff_OBP

                    # Append the row
                    data.append([
                        player_name, ip, era, avg, obp, obp2, slg, ops, diff_BB, walkrate, diff_HR, hrrate, diff_SO, krate
                    ])

                # Define column headers
                columns = [
                    "Player Name", "IP", "ERA", "AVG", "OBP", "OBP2", "SLG", "OPS", "BB", "BB%", "HR", "HR%", "K",
                    "K%"
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
                    FROM rankedpitchstats a
                    JOIN rankedpitchstats b
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
                    FROM rankedpitchstats a
                    JOIN rankedpitchstats b
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
    await bot.add_cog(RankedPitchStats(bot, connection))
