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
            print("CALLED!")
            print(response)

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

                if not data.strip():
                    await ctx.send("Error: Unable to extract data from one of the images.")
                    return

                groups = data.strip().split("\n\n")
                if len(groups) < 9:  # Ensure there are at least 9 groups
                    await ctx.send("Error: Insufficient data provided.")
                    return

                player_names = groups[0].split("\n")
                ab = groups[1].split("\n")
                h = groups[2].split("\n")
                bb = groups[3].split("\n")
                slg = processfloats(groups[4])
                bbk = processfloats(groups[5])
                hr = groups[6].split("\n")
                sb = groups[7].split("\n")
                sbpct = groups[8].split("\n")

                # Make all lists the same length
                max_rows = max(len(player_names), len(ab), len(h), len(bb), len(slg), len(bbk), len(hr), len(sb), len(sbpct))
                player_names += [""] * (max_rows - len(player_names))
                ab += ["0"] * (max_rows - len(ab))
                h += ["0"] * (max_rows - len(h))
                bb += ["0"] * (max_rows - len(bb))
                slg += ["0"] * (max_rows - len(slg))
                bbk += ["0"] * (max_rows - len(bbk))
                hr += ["0"] * (max_rows - len(hr))
                sb += ["0"] * (max_rows - len(sb))
                sbpct += ["0"] * (max_rows - len(sbpct))

                def safe_float(value):
                    try:
                        return float(value)
                    except ValueError:
                        return 0.0

                # Insert into the database
                discord_id = ctx.author.id  # Get the Discord ID of the user
                try:
                    with self.connection.cursor() as cursor:
                        for i in range(max_rows):
                            timing = "before" if counter <= 2 else "after"
                            cursor.execute(
                                """
                                INSERT INTO rankedbatstats (
                                    DISCORDID, PLAYERNAME, AB, H, BB, SLG, BBK, HR, SB, SBPCT, TIMING 
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    discord_id,
                                    player_names[i].strip(),
                                    int(ab[i]) if ab[i].isdigit() else 0,
                                    int(h[i]) if h[i].isdigit() else 0,
                                    int(bb[i]) if bb[i].isdigit() else 0,
                                    safe_float(slg[i]),
                                    safe_float(bbk[i]),
                                    int(hr[i]) if hr[i].isdigit() else 0,
                                    int(sb[i]) if sb[i].isdigit() else 0,
                                    int(sbpct[i]) if sbpct[i].isdigit() else 0,
                                    timing
                                ),
                            )
                        self.connection.commit()
                    await ctx.send(f"Data successfully inserted for Discord ID {discord_id}.")
                except Exception as e:
                    self.connection.rollback()
                    await ctx.send(f"An error occurred: {e}")
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")

    # Rest of the class remains unchanged
    # (checktables, etc.)

async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedBatStats(bot, connection))
