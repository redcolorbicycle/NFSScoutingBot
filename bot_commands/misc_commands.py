import random
from io import BytesIO
from PIL import Image
import discord
import os
from discord.ext import commands

class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cmboost(self, ctx):
        """
        Send the Control Master image
        """
        try:
            # Fixed path to the image
            image_path = "assets/cmtable.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="cmtable.jpg")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def fivetoolboost(self, ctx):
        """
        Send the 5 Tool Player image
        """
        try:
            # Fixed path to the image
            image_path = "assets/fivetooltable.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="fivetooltable.jpg")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def fivetoolcalculator(self, ctx, conbase:int, congi:int, powbase:int, powgi: int, eyebase:int, eyegi:int, spdbase:int,
                                 spdgi:int, fldbase:int, fldgi:int, target:int, supreme:str):
        """
        Calculates how many points are needed to hit a threshold and how many points leftover
        """
        supreme = supreme.lower()
        trainingtotal = 57
        totalcon = conbase + congi
        totalpow = powbase + powgi
        totaleye = eyebase + eyegi
        totalspd = spdbase + spdgi
        totalfld = fldbase + fldgi
        totalstats = totalcon + totalpow + totaleye + totalspd + totalfld
        if supreme == "yes":
            trainingtotal = 87
        if target*5 - (totalstats + trainingtotal) > 0:
            await ctx.send(f"You're fucked, that's out of reach. Try {(totalstats + trainingtotal)//5}.")
        else:
            contrain = max(target - totalcon,0)
            powtrain = max(target - totalpow,0)
            eyetrain = max(target - totaleye,0)
            spdtrain = max(target - totalspd,0)
            fldtrain = max(target - totalfld,0)

            answer = (f"You need {contrain} points to Contact.\n"
                      f"You need {powtrain} points to Power.\n"
                      f"You need {eyetrain} points to Eye.\n"
                      f"You need {spdtrain} points to Speed.\n"
                      f"You need {fldtrain} points to Fielding.\n"
                      f"You will have {trainingtotal - contrain - powtrain - eyetrain - spdtrain - fldtrain} training points left over.\n"
                      f"Your max possible 5 tool level is {(totalstats + trainingtotal)//5}."
                      )      
            await ctx.send(answer)  


    @commands.command()
    async def randomcolor(self, ctx):
        """
        Generate a random color and return an image of that color.
        """
        try:
            # Generate a random color
            random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            rgb_color = tuple(int(random_color[i:i+2], 16) for i in (1, 3, 5))  # Convert HEX to RGB

            # Create an image with the random color
            img = Image.new('RGB', (256, 256), rgb_color)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            # Send the image with the HEX code
            file = discord.File(fp=buffer, filename="random_color.png")
            await ctx.send(f"Here is your random color: {random_color}", file=file)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def delete_bot_messages(self, ctx, limit: int = 10):
        """Delete recent messages sent by the bot in the 'lounge' channel."""
        lounge_channel = discord.utils.get(ctx.guild.channels, name="bot-functions")  # Find the "lounge" channel
        if not lounge_channel:
            await ctx.send("The 'lounge' channel does not exist.")
            return

        try:
            deleted_count = 0
            async for message in lounge_channel.history(limit=limit):
                if message.author == self.bot.user:  # Check if the message was sent by the bot
                    await message.delete()
                    deleted_count += 1
            await ctx.send(f"Deleted {deleted_count} recent messages sent by the bot in 'lounge'.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages in the 'lounge' channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to delete messages: {e}")

    @commands.command()
    async def list_channels(self, ctx):
        """Lists all text channels the bot can access in all servers."""
        print("Available channels the bot can see:")
        for guild in self.bot.guilds:
            print(f"Server: {guild.name} (ID: {guild.id})")
            for channel in guild.text_channels:
                print(f"- Channel: {channel.name} (ID: {channel.id})")
            print("\n")
        await ctx.send("Channel list has been printed to the console.")


    @commands.command()
    async def respondtostevie(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/steviegif.mp4"  # Adjust this path as needed
            file = discord.File(image_path, filename="steviegif.mp4")
            await ctx.send(file=file)
            await ctx.send("Boy shut yo ass")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")



    
    


async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
