import discord
from discord.ext import commands

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None  # To track the message ID for reactions

    # Map emojis to roles
    ROLE_REACTIONS = {
        "👍": "GoldyIsNFS",  # Replace with your role names
        "🎉": "TooDankFast",
        "😎": "Burnouts",
    }

    @commands.command()
    async def send_roles(self, ctx):
        """Send a message for role assignment."""
        message = await ctx.send(
            "React to this message to get a role:\n"
            "👍 for \n"
            "🎉 for \n"
            "😎 for "
        )

        # Add the reactions to the message
        for emoji in self.ROLE_REACTIONS.keys():
            await message.add_reaction(emoji)

        # Save the message ID for tracking reactions
        self.role_message_id = message.id
        await ctx.send("Role assignment message sent and reactions added.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Assign a role when a user reacts."""
        if payload.user_id == self.bot.user.id:  # Ignore bot reactions
            return

        # Ensure the reaction is on the correct message
        if payload.message_id != self.role_message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Get the role name from the emoji
        role_name = self.ROLE_REACTIONS.get(emoji)
        if role_name:
            # Get the role object
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
                try:
                    await member.send(f"You have been assigned the role: {role_name}")
                except discord.Forbidden:
                    pass  # Handle cases where the user has DMs disabled

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Remove a role when a user removes their reaction."""
        if payload.user_id == self.bot.user.id:  # Ignore bot reactions
            return

        # Ensure the reaction is on the correct message
        if payload.message_id != self.role_message_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Get the role name from the emoji
        role_name = self.ROLE_REACTIONS.get(emoji)
        if role_name:
            # Get the role object
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)
                try:
                    await member.send(f"The role {role_name} has been removed from you.")
                except discord.Forbidden:
                    pass  # Handle cases where the user has DMs disabled


async def setup(bot):
    await bot.add_cog(ServerCommands(bot))
