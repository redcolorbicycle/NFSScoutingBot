from discord.ext import commands
import discord
import os

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
            await ctx.send("You're fucked, that's out of reach.")
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
                      )      
            await ctx.send(answer)  
    
    @commands.command()
    async def fivetoolcalculator(self, ctx, totalcon:int, totalpow:int, totaleye:int, totalspd:int,
                                 totalfld:int, target:int, supreme:str):
        """
        Calculates how many points are needed to hit a threshold and how many points leftover
        """
        supreme = supreme.lower()
        trainingtotal = 57
        totalstats = totalcon + totalpow + totaleye + totalspd + totalfld
        if supreme == "yes":
            trainingtotal = 87
        if target*5 - (totalstats + trainingtotal) > 0:
            await ctx.send("You're fucked, that's out of reach.")
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
                      )      
            await ctx.send(answer)  


async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
