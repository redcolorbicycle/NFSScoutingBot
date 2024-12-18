import random
from io import BytesIO
from PIL import Image
import discord
import os
from discord.ext import commands

class StevieCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def stevie(self, ctx):
        """
        Impersonate Stevie
        """
        try:
            # Fixed path to the image
            image_path = "assets/steviestart.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="cmtable.jpg")
            await ctx.send(file=file)
            await ctx.send("My hitting seems better after blues for sure but my pitching has taken a hit with the two aces")
            await ctx.send("Gonna need to blue off an ace sp asap. Went from Anibal being close to dominant and fried being 3+ era to both of them being 2.4-2.8 era.")
            await ctx.send("Need one of them to be a bonafide 2")
            await ctx.send("Hopefully once I blue off Anibal or get him a new set fried can be that guy with 578 FB fin ace")
            await ctx.send("I'm not liking wat I'm seeing with two aces")
            image_path = "assets/steviegif.mp4"  # Adjust this path as needed
            file = discord.File(image_path, filename="steviegif.mp4")
            await ctx.send(file=file)
            await ctx.send("Oh shit that's me")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(StevieCommands(bot))
