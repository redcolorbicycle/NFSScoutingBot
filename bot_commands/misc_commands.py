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
        Respond to stevie with a random boom gif
        """
        try:
            gif_choices = ["assets/boom.gif", "assets/boom2.gif", "assets/boom3.gif"]
            image_path = random.choice(gif_choices)

            if not os.path.isfile(image_path):
                await ctx.send("The selected image file was not found.")
                return

            file = discord.File(image_path, filename=os.path.basename(image_path))
            await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def sweep(self, ctx):
        """
        Respond to stevie with a random boom gif
        """
        try:
            gif_choices = ["assets/sweep1.gif", "assets/sweep2.gif", "assets/sweep3.gif"]
            image_path = random.choice(gif_choices)

            if not os.path.isfile(image_path):
                await ctx.send("The selected image file was not found.")
                return

            file = discord.File(image_path, filename=os.path.basename(image_path))
            await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def cupcake(self, ctx):
        """
        Respond to stevie with a random boom gif
        """
        try:
            gif_choices = ["assets/cupcake1.gif", "assets/cupcake2.gif"]
            image_path = random.choice(gif_choices)

            if not os.path.isfile(image_path):
                await ctx.send("The selected image file was not found.")
                return

            file = discord.File(image_path, filename=os.path.basename(image_path))
            await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def fuckyou(self, ctx):
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
    async def commands(self, ctx):
        """
        Lists all available command names (no descriptions).
        """
        try:
            command_names = [command.name for command in self.bot.commands if not command.hidden]
            command_names.sort()
            command_list = "\n".join(f"!{name}" for name in command_names)
            await ctx.send(f"**Available Commands:**\n{command_list}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def rekt(self, ctx, *, opponent: str):
        """
        Celebrate a grand slam with bold text and a custom sweep message.
        Usage: !five [opponent]
        """
        try:
            siren = "🚨"
            username = ctx.author.display_name.upper()
            magnified_name = ''.join(username.upper())
            opponent_clean = opponent.strip().upper()

            message = (
                f"{siren} {siren} {siren} {siren} {siren} {siren}\n"
                f"**GRAND SLAM!! FIVE WINS FOR {magnified_name}!! AND HE SWEEPS {opponent_clean} RIGHT OUT OF THE PLAYOFFS!**\n"
                f"{siren} {siren} {siren} {siren} {siren} {siren}"
            )
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def swept(self, ctx, *, opponent: str):
        """
        Celebrate a grand slam with bold text and a custom sweep message.
        Usage: !five [opponent]
        """
        try:
            siren = "🚨"
            username = ctx.author.display_name.upper()
            magnified_name = ''.join(username.upper())
            opponent_clean = opponent.strip().upper()

            message = (
                f"{siren} {siren} \n"
                f"**{magnified_name} has swept {opponent_clean} !**\n"
                f"{siren} {siren}"
            )
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def shame(self, ctx, *, opponent: discord.Member):
        """
        SHAME
        Usage: !shame @opponent
        """
        try:
            siren = "🚨"
            image_path = "assets/shame.gif"

            await ctx.send(file=discord.File(image_path, filename="shame.gif"))

            message = (
                f"{siren} {siren} \n"
                f"**SHAME ON {opponent.mention}!**\n"
                f"**SHAME ON {opponent.mention}!**\n"
                f"**Go sit in the corner. Daddy MK is very disappointed.**\n"
                f"{siren} {siren}"
            )
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")



    @commands.command()
    async def five(self, ctx):
        try:
            

            image_path = "assets/five.gif"  # Adjust this path as needed
            file = discord.File(image_path, filename="five.gif")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    @commands.command()
    async def jfc(self, ctx):
        try:
            

            image_path = "assets/jfc.jpg"  # Adjust this path as needed
            file = discord.File(image_path, filename="jfc.jpg")
            await ctx.send(file=file)
            #await ctx.send(file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


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
    async def flag(self, ctx):
        """
        Send the Pitching Coordinator image
        """
        try:
            # Fixed path to the image
            image_path = "assets/flag.jpg"  # Adjust this path as needed

            # Check if the image exists
            if not os.path.isfile(image_path):
                await ctx.send("The fixed image file was not found.")
                return

            # Send the image
            file = discord.File(image_path, filename="flag.jpg")
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


    
    


async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
