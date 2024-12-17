import discord
import os
from discord.ext import commands

class ServerCommands(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
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
            "🌪": "NeedForSpeed Squad",
            "🚂": "TooDankFast",
        }
        self.STRAT_PASS_ROLE = "NFS Strat Pass"

        # Load previously saved message IDs from the database
        self.role_message_ids = self.load_message_ids()

    def load_message_ids(self):
        """Load message IDs from the database."""
        with self.connection.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS role_messages (id BIGINT PRIMARY KEY);")
            cursor.execute("SELECT id FROM role_messages;")
            return [row[0] for row in cursor.fetchall()]

    def save_message_ids(self, message_id):
        """Save message ID to the database."""
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO role_messages (id) VALUES (%s) ON CONFLICT DO NOTHING;", (message_id,))
            self.connection.commit()

    @commands.command()
    async def send_roles(self, ctx):
        """Send a message for role assignment."""
        # Send the role assignment message
        role_message = "\n".join(
            [f"{emoji} for {role}" for emoji, role in self.ROLE_REACTIONS.items()]
        )
        message = await ctx.send(
            f"React to this message to get a role (multiple times for multiple clubs):\n{role_message}."
        )

        # Add reactions to the message
        for emoji in self.ROLE_REACTIONS.keys():
            await message.add_reaction(emoji)

        # Save the message ID for tracking
        self.save_message_ids(message.id)
        self.role_message_ids.append(message.id)  # Update in-memory list

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Assign a role when a user reacts."""
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id not in self.role_message_ids:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Assign "NFS Strat Pass" role
        strat_pass_role = discord.utils.get(guild.roles, name=self.STRAT_PASS_ROLE)
        if strat_pass_role and member:
            await member.add_roles(strat_pass_role)

        # Assign specific role based on emoji
        role_name = self.ROLE_REACTIONS.get(emoji)
        if role_name:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Remove a role when a user removes their reaction."""
        if payload.user_id == self.bot.user.id:
            return

        if payload.message_id not in self.role_message_ids:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji = str(payload.emoji)

        # Remove specific role based on emoji
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
                message = await ctx.channel.fetch_message(message_id)
                await message.delete()
            except discord.NotFound:
                await ctx.send(f"Message with ID {message_id} was not found and might already be deleted.")
            except discord.Forbidden:
                await ctx.send(f"I don't have permission to delete the message with ID {message_id}.")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to delete message with ID {message_id}: {e}")

        # Clear the tracked IDs in memory and the database
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM role_messages;")
            self.connection.commit()

        self.role_message_ids = []
        await ctx.send("All tracked role messages cleared and deleted.")

async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(ServerCommands(bot, connection))
