import discord
from discord.ext import commands

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_message_ids = []  # List of all role assignment message IDs

        # Define emoji-role mappings
        self.ROLE_REACTIONS = {
            "🟨": "GoldyIsNFS",           
            "🏎️": "TokyoDrift",          
            "🔥": "Burnouts",            
            "♠️": "Dugout Party",        
            "🚀": "The Kerchosen",       
            "🚦": "Rush Hour",           
            "🚗": "Speed Bumpers",       
            "😎": "ImOnSpeed Member",    
            "🌠": "NFS_NoLimits Member", 
            "🟧": "M&Ms",
        }

        self.STRAT_PASS_ROLE = "NFS Strat Pass"  # Role automatically assigned to all reactors

    @commands.command()
    async def send_roles(self, ctx):
        """Send a message for role assignment."""
        # Create a message describing the role assignment options
        role_message = "\n".join(
            [f"{emoji} for {role}" for emoji, role in self.ROLE_REACTIONS.items()]
        )
        message = await ctx.send(
            f"React to this message to get a role:\n{role_message}\n\n"
            
        )

        # Add the reactions to the message
        for emoji in self.ROLE_REACTIONS.keys():
            await message.add_reaction(emoji)

        # Save the message ID for tracking reactions
        self.role_message_ids.append(message.id)
        await ctx.send("I'm not actually Bieber by the way")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Assign a role when a user reacts."""
        if payload.user_id == self.bot.user.id:  # Ignore bot reactions
            return

        # Ensure the reaction is on any tracked role message
        if payload.message_id not in self.role_message_ids:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Assign the NFS Strat Pass role to all reactors
        strat_pass_role = discord.utils.get(guild.roles, name=self.STRAT_PASS_ROLE)
        if strat_pass_role and member:
            await member.add_roles(strat_pass_role)

        # Assign the role based on the emoji
        role_name = self.ROLE_REACTIONS.get(emoji)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
                

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Remove a role when a user removes their reaction."""
        if payload.user_id == self.bot.user.id:  # Ignore bot reactions
            return

        # Ensure the reaction is on any tracked role message
        if payload.message_id not in self.role_message_ids:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Remove the specific role based on the emoji
        role_name = self.ROLE_REACTIONS.get(emoji)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role and member:
                await member.remove_roles(role)
                

    @commands.command()
    async def clean_roles(self, ctx):
        """Remove old role messages from tracking and delete the messages."""
        for message_id in self.role_message_ids:
            try:
                message = await ctx.channel.fetch_message(message_id)  # Fetch the message by ID
                await message.delete()  # Delete the message
            except discord.NotFound:
                await ctx.send(f"Message with ID {message_id} was not found and might already be deleted.")
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to delete the message with ID {message_id}.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete message with ID {message_id}: {e}")

        # Clear the tracked IDs
        self.role_message_ids = []
        await ctx.send("All tracked role messages cleared and deleted.")


async def setup(bot):
    await bot.add_cog(ServerCommands(bot))
