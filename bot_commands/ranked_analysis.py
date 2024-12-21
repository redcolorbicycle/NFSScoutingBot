import discord
from discord.ext import commands
from PIL import Image
import pytesseract
from io import BytesIO
import re
import os

class TableAnalyser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initial_state = set()  # Cache for initial state (rows as tuples)
        self.final_state = set()    # Cache for final state (rows as tuples)

    def parse_image(self, image_data):
        """
        Extracts tabular data from an image using OCR
        """
        try:
            print("TESSDATA_PREFIX:", os.getenv("TESSDATA_PREFIX"))

            image = Image.open(BytesIO(image_data))
            extracted_text = pytesseract.image_to_string(image, lang="eng")

            return extracted_text
        except Exception as e:
            print(f"Error parsing image: {e}")
            return []

    @commands.command()
    async def analyse(self, ctx):
        """
        Analyse images for initial and final states, process them, and calculate results.
        Attach exactly 4 images to the command.
        """
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images: first 2 for the initial state, last 2 for the final state.")
            return

        try:
            # Process each image
            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                parsed_rows = self.parse_image(image_data)

                await ctx.send(parsed_rows)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(TableAnalyser(bot))
