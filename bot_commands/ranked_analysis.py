import discord
from discord.ext import commands
from PIL import Image
import pytesseract
from io import BytesIO
import re

class TableAnalyser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initial_state = set()  # Cache for initial state (rows as tuples)
        self.final_state = set()    # Cache for final state (rows as tuples)

    def parse_image(self, image_data):
        """
        Extracts tabular data from an image using OCR.
        """
        try:
            image = Image.open(BytesIO(image_data))
            extracted_text = pytesseract.image_to_string(image)

            rows = []
            for line in extracted_text.split("\n"):
                # Split rows into columns based on multiple spaces
                columns = re.split(r"\s{2,}", line.strip())
                if len(columns) >= 4:  # Ensure it has at least 4 columns
                    rows.append(tuple(columns[:4]))  # Take the first 4 columns
            return rows
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

                # Add rows to the appropriate cache
                if i < 2:  # Initial state (first two images)
                    self.initial_state.update(parsed_rows)
                else:  # Final state (last two images)
                    self.final_state.update(parsed_rows)

            # Convert sets to lists for processing
            initial_rows = list(self.initial_state)
            final_rows = list(self.final_state)

            # Perform calculations (example: compare row counts)
            initial_count = len(initial_rows)
            final_count = len(final_rows)
            added_rows = len(self.final_state - self.initial_state)
            removed_rows = len(self.initial_state - self.final_state)

            # Send results back to Discord
            await ctx.send(
                f"**Results:**\n"
                f"- Initial State Rows: {initial_count}\n"
                f"- Final State Rows: {final_count}\n"
                f"- Rows Added: {added_rows}\n"
                f"- Rows Removed: {removed_rows}"
            )

            # Optionally: print or send the exact rows added or removed
            added_rows_details = "\n".join(map(str, self.final_state - self.initial_state))
            removed_rows_details = "\n".join(map(str, self.initial_state - self.final_state))
            await ctx.send(f"**Added Rows:**\n{added_rows_details}")
            await ctx.send(f"**Removed Rows:**\n{removed_rows_details}")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(TableAnalyser(bot))
