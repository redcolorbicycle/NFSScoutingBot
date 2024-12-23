import discord
from discord.ext import commands
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt

class RankedBatStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.initial_state = set()  # Cache for initial state (rows as tuples)
        self.final_state = set()    # Cache for final state (rows as tuples)
        self.api_key = 'OCRSPACE_API'  # Replace with your OCR.Space API key

    def parse_image(self, image_data):
        """
        Extracts tabular data from an image using the OCR.Space API.
        """
        print("trying")
        try:
            # Send the image to OCR.Space API
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'image': image_data},
                data={'apikey': self.api_key, 'language': 'eng'}
            )

            # Parse the API response

            print("HTTP Status Code:", response.status_code)
            print("Response Text:", response)

            # Extract the recognized text
            return response
        except Exception as e:
            print(f"Error using OCR.Space API: {e}")
            return ""

    @commands.command()
    async def collect(self, ctx):
        """
        Collect images for initial and final states, process them.
        Attach exactly 4 images to the command.
        """
        print("ok")
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
                print("ok")

                player_names = groups[0].split("\n")
                ab = groups[1].split("\n")
                h = groups[2].split("\n")
                bb = groups[3].split("\n")
                slg = processfloats(groups[4])
                bbk = processfloats(groups[5])
                hr = groups[6].split("\n")
                sb = groups[7].split("\n")
                sbpct = groups[8].split("\n")

                print("ok2")

                # Make all lists the same length
                max_rows = max(len(player_names), len(ab), len(h), len(bb), len(slg), len(bbk), len(hr), len(doubles), len(rbi))
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
                                    DISCORDID, PLAYERNAME, AB, H, BB, SLG, BBK, HR, DOUBLES, RBI, TIMING 
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

    @commands.command()
    async def checktables(self, ctx):
        """
        Display two tables: one for entries with timing "before" and one for timing "after".
        """
        discord_id = ctx.author.id
        try:
            with self.connection.cursor() as cursor:
                # Query for "before" timing
                cursor.execute("SELECT * FROM rankedbatstats WHERE TIMING = 'before' AND DISCORDID = %s;", (discord_id,))
                before_rows = cursor.fetchall()
                before_columns = [desc[0] for desc in cursor.description]

                # Query for "after" timing
                cursor.execute("SELECT * FROM rankedbatstats WHERE TIMING = 'after' AND DISCORDID = %s;", (discord_id,))
                after_rows = cursor.fetchall()
                after_columns = [desc[0] for desc in cursor.description]

            # Convert to pandas DataFrame for better visualization
            before_df = pd.DataFrame(before_rows, columns=before_columns)
            after_df = pd.DataFrame(after_rows, columns=after_columns)

            # Plot the "before" table
            fig, ax = plt.subplots(figsize=(24, len(before_df) * 0.5 + 1))
            ax.axis("tight")
            ax.axis("off")
            table = ax.table(
                cellText=before_df.values,
                colLabels=before_df.columns,
                cellLoc="center",
                loc="center",
            )

            # Save the "before" table as an image
            buffer_before = BytesIO()
            plt.savefig(buffer_before, format="png", bbox_inches="tight")
            buffer_before.seek(0)
            plt.close(fig)

            # Plot the "after" table
            fig, ax = plt.subplots(figsize=(24, len(after_df) * 0.5 + 1))
            ax.axis("tight")
            ax.axis("off")
            table = ax.table(
                cellText=after_df.values,
                colLabels=after_df.columns,
                cellLoc="center",
                loc="center",
            )

            # Save the "after" table as an image
            buffer_after = BytesIO()
            plt.savefig(buffer_after, format="png", bbox_inches="tight")
            buffer_after.seek(0)
            plt.close(fig)

            # Send the tables to Discord
            before_file = discord.File(fp=buffer_before, filename="before_table.png")
            after_file = discord.File(fp=buffer_after, filename="after_table.png")

            await ctx.send("**Before Table:**", file=before_file)
            await ctx.send("**After Table:**", file=after_file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedBatStats(bot, connection))
