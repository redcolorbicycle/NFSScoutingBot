import discord
from discord.ext import commands
from PIL import Image
import pytesseract
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from paddleocr import PaddleOCR

class RankedBatStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.initial_state = set()  # Cache for initial state (rows as tuples)
        self.final_state = set()    # Cache for final state (rows as tuples)
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")  # Initialize PaddleOCR

    def parse_image(self, image_data):
        """
        Extracts tabular data from an image using PaddleOCR.
        """
        try:
            # Load image from bytes
            image = Image.open(BytesIO(image_data)).convert("RGB")

            # Convert image to a format PaddleOCR can process
            result = self.ocr.ocr(image, det=True, rec=True)

            # Extract the recognized text
            extracted_text = "\n".join([line[1][0] for line in result[0]])
            return extracted_text
        except Exception as e:
            print(f"Error using PaddleOCR: {e}")
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
            for attachment in attachments:
                image_data = await attachment.read()
                data = self.parse_image(image_data)
                # Process the extracted text into structured data
                print("OCR Output:", data)
                # Proceed with database and table logic...
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
