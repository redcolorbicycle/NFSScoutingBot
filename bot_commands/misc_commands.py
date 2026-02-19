import discord
from discord.ext import commands

from bot_commands.utils import send_asset
from bot_commands.constants import FIVETOOL_BONUSES, FIVETOOL_TRAINING_NORMAL, FIVETOOL_TRAINING_SUPREME


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def identify(self, ctx):
        try:
            await ctx.send(ctx.author.id)
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")

    @commands.command()
    async def cmboost(self, ctx):
        await send_asset(ctx, "cmboost")

    @commands.command()
    async def trainers(self, ctx):
        await send_asset(ctx, "trainers")

    @commands.command()
    async def fivetoolboost(self, ctx):
        await send_asset(ctx, "fivetoolboost")

    @commands.command()
    async def fivetoolcalculator(self, ctx, conbase: int, congi: int, powbase: int, powgi: int,
                                 eyebase: int, eyegi: int, spdbase: int, spdgi: int,
                                 fldbase: int, fldgi: int, target: int, supreme: str):
        """Calculate training points needed to hit a five-tool threshold."""
        supreme = supreme.lower()
        trainingtotal = FIVETOOL_TRAINING_SUPREME if supreme == "yes" else FIVETOOL_TRAINING_NORMAL
        totalcon = conbase + congi
        totalpow = powbase + powgi
        totaleye = eyebase + eyegi
        totalspd = spdbase + spdgi
        totalfld = fldbase + fldgi
        totalstats = totalcon + totalpow + totaleye + totalspd + totalfld

        if target * 5 - (totalstats + trainingtotal) > 0:
            await ctx.send(f"That target is out of reach. Try {(totalstats + trainingtotal) // 5}.")
        else:
            contrain = max(target - totalcon, 0)
            powtrain = max(target - totalpow, 0)
            eyetrain = max(target - totaleye, 0)
            spdtrain = max(target - totalspd, 0)
            fldtrain = max(target - totalfld, 0)
            maxpossible = (totalstats + trainingtotal) // 5
            final = 110
            for i in FIVETOOL_BONUSES:
                if i <= maxpossible:
                    final = i
                    break
            leftover = trainingtotal - contrain - powtrain - eyetrain - spdtrain - fldtrain
            await ctx.send(
                f"Train {contrain} {powtrain} {eyetrain} {spdtrain} {fldtrain}.\n"
                f"You will have {leftover} training points left over.\n"
                f"Your max possible 5 tool level is {maxpossible}.\n"
                f"Your max possible 5 tool level where the boost hits a new threshold is {final}."
            )

    @commands.command()
    async def list_channels(self, ctx):
        """List all text channels the bot can access."""
        print("Available channels the bot can see:")
        for guild in self.bot.guilds:
            print(f"Server: {guild.name} (ID: {guild.id})")
            for channel in guild.text_channels:
                print(f"- Channel: {channel.name} (ID: {channel.id})")
            print("\n")
        await ctx.send("Channel list has been printed to the console.")

    @commands.command()
    async def respondtostevie(self, ctx):
        await send_asset(ctx, "respondtostevie")

    @commands.command()
    async def wtf(self, ctx):
        await send_asset(ctx, "wtf")

    @commands.command()
    async def respondtostevie2(self, ctx):
        await send_asset(ctx, "respondtostevie2")

    @commands.command()
    async def hehe(self, ctx):
        await send_asset(ctx, "hehe")

    @commands.command()
    async def stevie(self, ctx):
        await send_asset(ctx, "stevie")

    @commands.command()
    async def ohno(self, ctx):
        await send_asset(ctx, "ohno")

    @commands.command()
    async def boom(self, ctx):
        await send_asset(ctx, "boom")

    @commands.command()
    async def cyclopssweep(self, ctx):
        await send_asset(ctx, "cyclopssweep")

    @commands.command()
    async def sweep(self, ctx):
        await send_asset(ctx, "sweep")

    @commands.command()
    async def click(self, ctx):
        await send_asset(ctx, "click")

    @commands.command()
    async def kiss(self, ctx):
        await send_asset(ctx, "kiss")

    @commands.command()
    async def cupcake(self, ctx):
        await send_asset(ctx, "cupcake")

    @commands.command()
    async def fuckyou(self, ctx):
        await send_asset(ctx, "fuckyou")

    @commands.command()
    async def cursed(self, ctx):
        await send_asset(ctx, "cursed")

    @commands.command()
    async def goldskilltrainers(self, ctx):
        await send_asset(ctx, "goldskilltrainers")

    @commands.command()
    async def listcommands(self, ctx):
        """List all available command names."""
        try:
            command_names = sorted(cmd.name for cmd in self.bot.commands if not cmd.hidden)
            await ctx.send("**Available Commands:**\n" + "\n".join(f"!{name}" for name in command_names))
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def filtered(self, ctx):
        """List selected boost commands."""
        selected_commands = [
            "!cmboost", "!fivetoolboost", "!fivetoolcalculator",
            "!mrpboost", "!pcoboost", "!goldskilltrainers", "!trainers",
        ]
        await ctx.send("**Available Commands:**\n" + "\n".join(selected_commands))

    @commands.command()
    async def rekt(self, ctx, *, opponent: str):
        """Announce a grand slam sweep victory."""
        siren = "🚨"
        username = ctx.author.display_name.upper()
        opponent_clean = opponent.strip().upper()
        await ctx.send(
            f"{siren} {siren} {siren} {siren} {siren} {siren}\n"
            f"**GRAND SLAM!! FIVE WINS FOR {username}!! AND HE SWEEPS {opponent_clean} RIGHT OUT OF THE PLAYOFFS!**\n"
            f"{siren} {siren} {siren} {siren} {siren} {siren}"
        )

    @commands.command()
    async def swept(self, ctx, *, opponent: str):
        """Announce a sweep."""
        siren = "🚨"
        username = ctx.author.display_name.upper()
        opponent_clean = opponent.strip().upper()
        await ctx.send(
            f"{siren} {siren} \n"
            f"**{username} has swept {opponent_clean} !**\n"
            f"{siren} {siren}"
        )

    @commands.command()
    async def shame(self, ctx, *, opponent: discord.Member):
        """Shame a user."""
        siren = "🚨"
        try:
            await ctx.send(file=discord.File("assets/shame.gif", filename="shame.gif"))
            await ctx.send(
                f"{siren} {siren} \n"
                f"**SHAME ON {opponent.mention}!**\n"
                f"**SHAME ON {opponent.mention}!**\n"
                f"**Go sit in the corner. Daddy MK is very disappointed.**\n"
                f"{siren} {siren}"
            )
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def five(self, ctx):
        await send_asset(ctx, "five")

    @commands.command()
    async def jfc(self, ctx):
        await send_asset(ctx, "jfc")

    @commands.command()
    async def pcoboost(self, ctx):
        await send_asset(ctx, "pcoboost")

    @commands.command()
    async def flag(self, ctx):
        await send_asset(ctx, "flag")

    @commands.command()
    async def mrpboost(self, ctx):
        await send_asset(ctx, "mrpboost")


async def setup(bot):
    await bot.add_cog(MiscCommands(bot))
