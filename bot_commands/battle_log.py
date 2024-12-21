from discord.ext import commands

class BattleLog(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection

    async def cog_check(self, ctx):
        """
        Restrict commands to users with specific roles.
        """
        allowed_roles = [
            "TooDank Leaders", "Vice", "TokyoDrift Leaders", "NFS Ops", "NFS OG Leaders", 
            "NeedForSpeed Leaders", "M16Speed Spy Daddies", "GoldyLeads", "Burnout Leaders", 
            "Dugout Leads", "Kerchoo Leaders", "Rush Hour Leaders", "Speed Bump Leaders", 
            "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad"
        ]
        user_roles = [role.name for role in ctx.author.roles]
        return any(role in allowed_roles for role in user_roles)

    @commands.command()
    async def log(self, ctx, hometeam: str, opponentteam: str, *args):
        """
        Log battles into the club_records table.
        Usage: !log <hometeam> <opponentteam> <player_number> <opponent_number> <result> ...
        """
        hometeam = hometeam.lower()
        opponentteam = opponentteam.lower()
        if len(args) % 3 != 0:
            await ctx.send("Error: Arguments must be in groups of 3 (player_number opponent_number result).")
            return

        try:
            with self.connection.cursor() as cursor:
                response_messages = []
                battle_date = None

                # Retrieve the locked battle_date
                cursor.execute("SELECT locked_date FROM battle_date WHERE id = 1")
                battle_date_row = cursor.fetchone()
                if not battle_date_row:
                    await ctx.send("Error: Battle date is not set. Please start a battle first with !startbattle hometeam opponent.")
                    return

                battle_date = battle_date_row[0]

                for i in range(0, len(args), 3):
                    try:
                        # Parse arguments
                        player_number = int(args[i])
                        opponent_number = int(args[i + 1])
                        result = args[i + 2].upper()

                        if result not in ("W", "L", "D"):
                            raise ValueError(f"Invalid result: {result}")

                        # Fetch player and opponent details
                        cursor.execute(
                            """
                            SELECT player, homeclub, sp
                            FROM hometeam
                            WHERE designated_number = %s AND homeclub = %s
                            """,
                            (player_number, hometeam)
                        )
                        player_row = cursor.fetchone()

                        cursor.execute(
                            """
                            SELECT opponent, opponentclub, sp
                            FROM opponents
                            WHERE designated_number = %s AND opponentclub = %s
                            """,
                            (opponent_number, opponentteam)
                        )
                        opponent_row = cursor.fetchone()

                        if not player_row or not opponent_row:
                            raise ValueError(f"Invalid player ({player_number}) or opponent ({opponent_number}) number.")

                        player_name, player_club, player_sp = player_row
                        opponent_name, opponent_club, opponent_sp = opponent_row

                        # Insert into club_records
                        cursor.execute(
                            """
                            INSERT INTO club_records (
                                battle_date, player_name, opponent_name, result,
                                opponent_club, player_club, player_sp_number, opponent_sp_number
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                battle_date,
                                player_name, opponent_name, result,
                                opponent_club, player_club,
                                player_sp, opponent_sp,
                            ),
                        )

                        # Update SP numbers
                        next_player_sp = 1 if player_sp == 5 else player_sp + 1
                        next_opponent_sp = 1 if opponent_sp == 5 else opponent_sp + 1

                        cursor.execute(
                            """
                            UPDATE hometeam
                            SET sp = %s
                            WHERE designated_number = %s AND homeclub = %s
                            """,
                            (next_player_sp, player_number, hometeam),
                        )

                        cursor.execute(
                            """
                            UPDATE opponents
                            SET sp = %s
                            WHERE designated_number = %s AND opponentclub = %s
                            """,
                            (next_opponent_sp, opponent_number, opponentteam),
                        )

                        self.connection.commit()
                        response_messages.append(f"Logged: Player {player_number} vs Opponent {opponent_number} ({result}).")
                    except Exception as sub_error:
                        response_messages.append(f"Error processing {args[i:i+3]}: {sub_error}")

                await ctx.send("\n".join(response_messages))

        except Exception as e:
            self.connection.rollback()
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(BattleLog(bot, connection))
