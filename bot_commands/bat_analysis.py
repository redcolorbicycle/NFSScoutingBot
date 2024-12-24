import discord
from discord.ext import commands
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import os

class RankedBatStats(commands.Cog):
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
    async def collect(self, ctx):
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
            with self.connection.cursor() as cursor:
                # Execute the DELETE query
                cursor.execute(
                    "DELETE FROM rankedbatstats WHERE DISCORDID = %s;",
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
                    await ctx.send("Data reset!")
                except Exception as e:
                    self.connection.rollback()
                    await ctx.send(f"An error occurred: {e}")
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")


    def process_insert(self, raw_data, discord_id, timing):
        try:
            data = [raw_data[i:i + 9] for i in range(0, len(raw_data), 9)]
            print(data)
            # Insert rows into the database
            with self.connection.cursor() as cursor:
                for row in data:
                    cursor.execute(
                        """
                        INSERT INTO rankedbatstats (
                            DISCORDID, PLAYERNAME, AB, H, BB, SLG, BBK, HR, DOUBLES, RBI, TIMING
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (DISCORDID, PLAYERNAME, TIMING) DO NOTHING;
                        """,
                        (discord_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], timing)
                    )
                    print(row)
                    print("done!")
                self.connection.commit()
            print(f"Inserted {len(data)} rows into the database.")


        except Exception as e:
            self.connection.rollback()
            print(f"Error processing and inserting data: {e}")
            

    @commands.command()
    async def compare_stats(self, ctx):
        """
        Compares 'before' and 'after' stats for each player and prints the differences.
        """
        discord_id = ctx.author.id
        try:
            with self.connection.cursor() as cursor:
                # Execute the SQL query to fetch and calculate differences
                message = ""
                cursor.execute(
                    """
                    SELECT a.PLAYERNAME,
                        b.AB - a.AB AS diff_AB,
                        b.H - a.H AS diff_H,
                        b.HR - a.HR AS diff_HR,
                        b.BB - a.BB AS diff_BB,
                        b.SLG * b.AB - a.SLG * a.AB AS diff_bases,
                        b.DOUBLES - a.DOUBLES AS diff_DOUBLES,
                        b.RBI - a.RBI AS diff_RBI
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

                # Print differences
                for row in results:
                    player_name = row[0]
                    diff_AB = row[1]
                    diff_H = row[2]
                    diff_HR = row[3]
                    diff_BB = row[4]
                    diff_BASES = row[5]
                    diff_DOUBLES = row[6]
                    diff_RBI = row[7]
                    message += f"{player_name} hit an average of {diff_H/diff_AB}, with a walk rate of {diff_BB/(diff_AB + diff_BB)} and an OBP of {(diff_H + diff_BB)/(diff_AB + diff_BB)}.\n"
                    message += f"{player_name} hit {diff_HR} HRs for a HR rate of {diff_HR/diff_AB}, slugging {diff_BASES/diff_AB} and hitting {diff_DOUBLES} doubles({diff_DOUBLES/diff_AB}%, {diff_DOUBLES/diff_H}% of his hits).\n"
                    message += f"{player_name} hit {diff_RBI} in {diff_H} hits and {diff_BB} walks."
            await ctx.send(message)
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
