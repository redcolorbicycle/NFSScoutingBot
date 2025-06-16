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
    async def identify(self, ctx):
        try:
            discord_id = ctx.author.id
            await ctx.send(discord_id)
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")

    @commands.command()
    async def cmboost(self, ctx):
        """
        Send the Contact Master image
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
    async def trainers(self, ctx):
        """
        Send the Trainers image
        """
        try:
            # Fixed path to the image
            image_path = "assets/trainers.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="trainers.jpg")
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
        bonuses = [110, 108, 105, 103, 100, 98, 95, 93, 90, 88]
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
            maxpossible = (totalstats + trainingtotal)//5
            final = 110
            for i in bonuses:
                if i <=maxpossible:
                    final = i
                    break

            answer = (f"Train {contrain} {powtrain} {eyetrain} {spdtrain} {fldtrain}.\n"
                      f"You will have {trainingtotal - contrain - powtrain - eyetrain - spdtrain - fldtrain} training points left over.\n"
                      f"Your max possible 5 tool level is {maxpossible}.\n"
                      f"Your max possible 5 tool level where the boost hits a new threshold is {final}."
                      )      
            await ctx.send(answer)  


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
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def wtf(self, ctx):
        """
        wtf
        """
        try:
            

            image_path = "assets/wtf.jpg"  # Adjust this path as needed
            file = discord.File(image_path, filename="wtf.jpg")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def respondtostevie2(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/stare.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="stare.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def hehe(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/run.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="run.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def sunbro(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/sunbro.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="sunbro.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def dankbrewski(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/dankbrewski.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="dankbrewski.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def stevie(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/stevielose.jpg"  # Adjust this path as needed
            file = discord.File(image_path, filename="stevielose.jpg")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def ohno(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/shock.jpg"  # Adjust this path as needed
            file = discord.File(image_path, filename="shock.jpg")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def boom(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/boom.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="boom.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    commands.command()
    async def fu(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/gnome.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="gnome.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def miltown(self, ctx):
        """
        Respond to stevie
        """
        try:
            

            image_path = "assets/miltown.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="miltown.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen for messages and respond to specific ones.
        """

        if message.content == "yabbadabbadobadee":
            try:
                ctx = await self.bot.get_context(message)
                if ctx.command is None:
                    await self.respondtostevie(ctx)
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")


    @commands.command()
    async def pcoboost(self, ctx):
        """
        Send the Pitching Coordinator image
        """
        try:
            # Fixed path to the image
            image_path = "assets/PCO.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="PCO.jpg")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def mrpboost(self, ctx):
        """
        Send the Mr Perfect image
        """
        try:
            # Fixed path to the image
            image_path = "assets/MrPerfect.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="MRP.jpg")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def toolswebpage(self, ctx):
        """
        Send Murph's webpage
        """
        try:
            await ctx.send("https://9inningstools.app/")
            return
        except Exception as e:
            await ctx.send(f"An error occured: {e}")





    
    


async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
