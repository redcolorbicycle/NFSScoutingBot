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

    async def stevie2(self, ctx):
        """
        Impersonate Stevie too
        """
        try:
            await ctx.send("So my Boston team is coming along.. blues n greens away from having my rotation complete.. worst set wld be a cm 331 on erod .. 2 legends with fb sets .. Pedro 333 cm price 332 fb ace")
            await ctx.send("Xander sig to replace Ozzie (to bench wit chem)")
            await ctx.send("Have 2 legends and two primes in lineup who need BD..")
            await ctx.send("My bullpen is a huge question mark but over last cpl days I hit Okajima sig and kimbrel prime")
            await ctx.send("So that wld give me Lowe Okajima kimbrel in SU1-2 and closer")
            await ctx.send("All in all . Once I BD some guys and get a cpl GIs .. I'ma be cookin")
            await ctx.send("I've decided to put more effort into it")
            await ctx.send("I think I now have enuff pieces to patchwork together a solid top 1k ish squad")
            await ctx.send("My Mets team is seriously so far back it's insane.. I don even know where to start")
            await ctx.send("Yes it got 8 sigs 3 legends but it ain't got but one solid skills set")
            await ctx.send("And cespedes sig has batterss chem.. 682s on ppl 683s n shit.. bds are ass backwards")
            await ctx.send("He does have 332 cm in backups")
            await ctx.send("It jus needs Alot of work . I can prob get it right in a year or so")
            await ctx.send("But I'ma focus more on boston")
            await ctx.send("It's much closer to competing")
            await ctx.sned("Mets team is literally going 0-5 for moonshots everyday lmao")
            await ctx.send("Surprised they ain't kick me out")
            await ctx.send("Yet")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


async def setup(bot):
    await bot.add_cog(StevieCommands(bot))
