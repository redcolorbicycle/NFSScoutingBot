from discord.ext import commands

def setup_commands(bot, connection):
    """Register all commands for the bot."""

    #club commands

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
            connection.rollback()
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
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    async def rename_club(ctx, old_name: str, new_name: str):
        """Rename an existing club in the database."""
        try:
            with connection.cursor() as cursor:
                # Check if the club with the old name exists
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (old_name,))
                existing_club = cursor.fetchone()

                if not existing_club:
                    await ctx.send(f"No club found with the name '{old_name}'.")
                    return

                # Check if the new name already exists
                cursor.execute("SELECT * FROM Club WHERE Club_Name = %s", (new_name,))
                new_name_club = cursor.fetchone()

                if new_name_club:
                    await ctx.send(f"The name '{new_name}' is already taken by another club.")
                    return

                # Rename the club
                cursor.execute(
                    "UPDATE Club SET Club_Name = %s WHERE Club_Name = %s",
                    (new_name, old_name),
                )

                connection.commit()
                await ctx.send(f"Renamed club '{old_name}' to '{new_name}' and updated all associated players.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")







    #player commands

    @bot.command()
    async def scout_player(ctx, player_name: str):
        """Fetch all details of a specific player."""
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT Name, Club_Name, SP1_Name, SP1_Skills, SP2_Name, SP2_Skills, 
                       SP3_Name, SP3_Skills, SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                       Nerf, Most_Common_Batting_Skill, PR, last_updated, nerf_updated
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
                    nerf, batting_skill, pr, last_updated, nerf_updated
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
                    f"**Nerf Last Updated**: {nerf_updated}\n"
                )

                await ctx.send(details)
            else:
                await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
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
        """Add a new player to the database. Fails if the player already exists."""
        try:
            cursor = connection.cursor()

            # Check if the player already exists
            cursor.execute("SELECT * FROM Player WHERE Name = %s", (name,))
            existing_player = cursor.fetchone()

            if existing_player:
                await ctx.send(f"The player '{name}' already exists in the database. No changes made.")
            else:
                # Insert a new player and set Last_Updated to the current date
                cursor.execute(
                    """
                    INSERT INTO Player (
                        Name, Club_Name, SP1_Name, SP1_Skills,
                        SP2_Name, SP2_Skills, SP3_Name, SP3_Skills,
                        SP4_Name, SP4_Skills, SP5_Name, SP5_Skills,
                        Nerf, Most_Common_Batting_Skill, PR, last_updated, nerf_updated
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE)
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
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


    @bot.command()
    async def update_nerf(ctx, player_name: str, new_nerf: str):
        """Update the nerf value for a player and set the nerf last updated date."""
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if player:
                    # Update the nerf value and nerf_updated date
                    cursor.execute(
                        """
                        UPDATE Player
                        SET Nerf = %s, nerf_updated = CURRENT_DATE
                        WHERE Name = %s
                        """,
                        (new_nerf, player_name),
                    )
                    connection.commit()
                    await ctx.send(f"Updated nerf for '{player_name}' to '{new_nerf}' and updated the last nerf change date.")
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")

    @bot.command()
    async def delete_player(ctx, player_name: str):
        """Delete a player from the database."""
        try:
            with connection.cursor() as cursor:
                # Check if the player exists
                cursor.execute("SELECT * FROM Player WHERE Name = %s", (player_name,))
                player = cursor.fetchone()

                if player:
                    # Delete the player
                    cursor.execute("DELETE FROM Player WHERE Name = %s", (player_name,))
                    connection.commit()
                    await ctx.send(f"Player '{player_name}' has been deleted from the database.")
                else:
                    await ctx.send(f"No player found with the name '{player_name}'.")
        except Exception as e:
            connection.rollback()
            await ctx.send(f"An error occurred: {e}")


