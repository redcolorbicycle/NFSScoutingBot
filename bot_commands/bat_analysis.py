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
                        print(extracted_text)

                        return "\n".join(extracted_text)

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
            def processfloats(lst):
                lst = lst.split("\n")
                for i in range(len(lst)):
                    try:
                        f = float(lst[i])
                        if f >= 2:
                            lst[i] = f / 1000
                    except ValueError:
                        pass
                return lst

            counter = 0

            # Process each image
            for i, attachment in enumerate(attachments):
                counter += 1
                image_data = await attachment.read()
                data = self.parse_image(image_data)

                # Insert into the database
                discord_id = ctx.author.id  # Get the Discord ID of the user
                try:
                    if i <= 1:
                        timing = "before"
                    else:
                        timing = "after"
                    self.process_insert(data, discord_id, timing)
                except Exception as e:
                    self.connection.rollback()
                    await ctx.send(f"An error occurred: {e}")
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")

    def process_insert(self, raw_data, discord_id, timing):
        try:
            rows = []  # To store processed rows
            current_row = []  # Current player's data

            for i, value in enumerate(raw_data):
                if len(current_row) == 0:  # Start of a new player
                    if value[0].isupper() or "'" in value:
                        current_row.append(value)  # Add player name
                elif len(current_row) < 8:  # Add non-sb attributes for the current player
                    try:
                        current_row.append(float(value) if '.' in value else int(value))
                    except ValueError:
                        current_row.append(value)  # Handle invalid values gracefully
                if len(current_row) == 8:  # Check if player data is complete
                    # Handle SB = 0 and next value logic
                    if current_row[7] == 0:  # SB = 0
                        if raw_data[i+1] == "-":
                            i += 1
                        current_row.append(0)  # SBPCT = 0

                    if len(current_row) == 9:  # Ensure SBPCT is added
                        current_row.append(timing)  # Add timing
                        print(current_row)
                        print(rows)
                        rows.append([discord_id] + current_row)
                        print(current_row)
                        print(rows)
                        current_row = []  # Reset for the next player

            # Insert rows into the database
            with self.connection.cursor() as cursor:
                for row in rows:
                    cursor.execute(
                        """
                        INSERT INTO rankedbatstats (
                            DISCORDID, PLAYERNAME, AB, H, BB, SLG, BBK, HR, SB, SBPCT, TIMING
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        row,
                    )
                self.connection.commit()
            print(f"Inserted {len(rows)} rows into the database.")


        except Exception as e:
            print(f"Error processing and inserting data: {e}")
            self.connection.rollback()


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedBatStats(bot, connection))
