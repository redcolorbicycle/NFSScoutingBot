import discord
from discord.ext import commands
import psycopg2
import os
from urllib.parse import urlparse

# Parse database URL
DATABASE_URL = "postgres://u4kqn7e60puiu1:p4a4ecc6673558b8a08d820c48a4456038a4752c358a0f1de9396f15fd58c6945@cd27da2sn4hj7h.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d6p7k4of1m96ql"
result = urlparse(DATABASE_URL)
connection = psycopg2.connect(
    database=result.path[1:],
    user=result.username,
    password=result.password,
    host=result.hostname,
    port=result.port
)

# Define intents
intents = discord.Intents.default()  # Default intents include basic events
intents.message_content = True       # Allows the bot to read message content

# Initialize the bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Command: Scout Club
@bot.command()
async def scout_club(ctx, club_name: str):
    """Fetch all players belonging to a specific club."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT Name FROM Player WHERE Club_Name = %s", (club_name,))
        players = cursor.fetchall()
        cursor.close()

        if players:
            player_list = "\n".join([player[0] for player in players])
            await ctx.send(f"Players in {club_name}:\n{player_list}")
        else:
            await ctx.send(f"No players found for the club '{club_name}'.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
async def scout_player(ctx, player_name: str):
    """Fetch all details of a specific player."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT Name, Club_Name, SP1_Name, SP1_Skills, SP2_Name, SP2_Skills, 
                   SP3_Name, SP3_Skills, SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                   Nerf, Most_Common_Batting_Skill, PR
            FROM Player
            WHERE Name = %s
            """,
            (player_name,),
        )
        player = cursor.fetchone()
        cursor.close()

        if player:
            (
                name, club, sp1_name, sp1_skills, sp2_name, sp2_skills,
                sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                nerf, batting_skill, pr, last_updated
            ) = player

            details = (
                f"**Player Details**\n"
                f"**Name**: {name}\n"
                f"**Club**: {club}\n"
                f"**SP1**: {sp1_name} ({sp1_skills})\n"
                f"**SP2**: {sp2_name} ({sp2_skills})\n"
                f"**SP3**: {sp3_name} ({sp3_skills})\n"
                f"**SP4**: {sp4_name} ({sp4_skills})\n"
                f"**SP5**: {sp5_name} ({sp5_skills})\n"
                f"**Nerf**: {nerf}\n"
                f"**Most Common Batting Skill**: {batting_skill}\n"
                f"**PR**: {pr}\n"
                f"**Last Updated**: {last_updated}\n"
            )
            await ctx.send(details)
        else:
            await ctx.send(f"No player found with the name '{player_name}'.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")





@bot.command()
async def add_club(ctx, club_name: str):
    """Add a new club to the database."""
    try:
        cursor = connection.cursor()

        # Check if the club already exists
        cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (club_name,))
        existing_club = cursor.fetchone()

        if existing_club:
            await ctx.send(f"The club '{club_name}' already exists in the database.")
        else:
            # Insert a new club
            cursor.execute(
                """
                INSERT INTO Club (Club_Name)
                VALUES (%s)
                """,
                (club_name,),
            )
            connection.commit()
            await ctx.send(f"Added new club '{club_name}' to the database.")

        cursor.close()
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


@bot.command()
async def add_player(
    ctx,
    name: str,
    club_name: str,
    sp1_name: str,
    sp1_skills: str,
    sp2_name: str,
    sp2_skills: str,
    sp3_name: str,
    sp3_skills: str,
    sp4_name: str,
    sp4_skills: str,
    sp5_name: str,
    sp5_skills: str,
    nerf: str,
    batting_skill: str,
    pr: int,
):
    """Add or update a player in the database."""
    try:
        cursor = connection.cursor()

        # Check if the player already exists
        cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
        existing_player = cursor.fetchone()

        if existing_player:
            # Update the player's details
            cursor.execute(
                """
                UPDATE Player
                SET Club_Name = %s, SP1_Name = %s, SP1_Skills = %s,
                    SP2_Name = %s, SP2_Skills = %s, SP3_Name = %s, SP3_Skills = %s,
                    SP4_Name = %s, SP4_Skills = %s, SP5_Name = %s, SP5_Skills = %s,
                    Nerf = %s, Most_Common_Batting_Skill = %s, PR = %s
                WHERE Name = %s
                """,
                (
                    club_name,
                    sp1_name,
                    sp1_skills,
                    sp2_name,
                    sp2_skills,
                    sp3_name,
                    sp3_skills,
                    sp4_name,
                    sp4_skills,
                    sp5_name,
                    sp5_skills,
                    nerf,
                    batting_skill,
                    pr,
                    name,
                ),
            )
            connection.commit()
            await ctx.send(f"Updated player '{name}' in the database.")
        else:
            # Insert a new player
            cursor.execute(
                """
                INSERT INTO Player (
                    Name, Club_Name, SP1_Name, SP1_Skills,
                    SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                    SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                    Nerf, Most_Common_Batting_Skill, PR
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    club_name,
                    sp1_name,
                    sp1_skills,
                    sp2_name,
                    sp2_skills,
                    sp3_name,
                    sp3_skills,
                    sp4_name,
                    sp4_skills,
                    sp5_name,
                    sp5_skills,
                    nerf,
                    batting_skill,
                    pr,
                ),
            )
            connection.commit()
            await ctx.send(f"Added new player '{name}' to the database.")

        cursor.close()
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")


# Run the bot
bot.run("MTMxMTc0MjYzNjE1OTQwMjA1Nw.GMFFat.ejWIUJ18tiTh6sjndAt8qnSpYnygwBTqh9-CD4")
