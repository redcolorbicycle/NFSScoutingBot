from discord.ext import commands

def setup_commands(bot, connection):
    """Register all commands for the bot."""

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
                       Nerf, Most_Common_Batting_Skill, PR, last_updated
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
    async def add_player(ctx, name, club_name, sp1_name, sp1_skills, sp2_name, sp2_skills,
                        sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                        nerf, batting_skill, pr):
        """Add a new player to the database."""
        try:
            cursor = connection.cursor()
            
            # Insert the player without explicitly setting nerf_updated (uses DEFAULT CURRENT_DATE)
            cursor.execute("""
                INSERT INTO Player (Name, Club_Name, SP1_Name, SP1_Skills, SP2_Name, SP2_Skills,
                                    SP3_Name, SP3_Skills, SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                                    Nerf, Batting_Skill, PR)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, club_name, sp1_name, sp1_skills, sp2_name, sp2_skills,
                sp3_name, sp3_skills, sp4_name, sp4_skills, sp5_name, sp5_skills,
                nerf, batting_skill, pr))
            
            connection.commit()
            await ctx.send(f"Added new player '{name}' to the database.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")