import discord
from discord.ext import commands
import asyncio
import pandas as pd
import os

from bot_commands.utils import render_table_image, parse_image, looks_like_row_start
from bot_commands.constants import ALLOWED_ANALYST_IDS


class RankedPitchStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.api_key = os.getenv('AZURE_API_KEY')
        self.endpoint = os.getenv('AZURE_ENDPOINT') + '/vision/v3.2/read/analyze'

    async def cog_check(self, ctx):
        return ctx.author.id in ALLOWED_ANALYST_IDS

    def delete_user_data(self, discord_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM rankedpitchstats WHERE DISCORDID = %s;", (discord_id,))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Delete Error: {e}")

    def process_insert(self, raw_data, discord_id, timing):
        try:
            ocr_rows, current_row = [], []

            for i in range(len(raw_data)):
                if raw_data[i] == "...":
                    continue
                if looks_like_row_start(raw_data[i]):
                    current_row = [raw_data[i]]
                    continue
                elif len(current_row) == 1:
                    if "." in raw_data[i]:
                        integer_part, decimal_part = raw_data[i].split(".")
                        integer_part = int(integer_part)
                        if decimal_part == "1":
                            current_row.append(integer_part * 3 + 1)
                        elif decimal_part == "2":
                            current_row.append(integer_part * 3 + 2)
                        else:
                            current_row.append(integer_part * 3)
                else:
                    current_row.append(raw_data[i])
                    ocr_rows.append(current_row)

            with self.connection.cursor() as cursor:
                for row in ocr_rows:
                    cursor.execute("""
                        INSERT INTO rankedpitchstats (
                            DISCORDID, PLAYERNAME, OUTS, R, H, BB, SLG, HR, SO, TIMING, G
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (DISCORDID, PLAYERNAME, TIMING) DO NOTHING;
                    """, (discord_id, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], timing, row[8]))
                self.connection.commit()
            print(f"Inserted {len(ocr_rows)} rows into the database.")
        except Exception as e:
            self.connection.rollback()
            print(f"Insert Error: {e}")

    @commands.command()
    async def pitchers(self, ctx):
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images: first 2 for the initial state, last 2 for the final state.")
            return

        discord_id = ctx.author.id
        await ctx.send("Please wait...")

        try:
            await asyncio.to_thread(self.delete_user_data, discord_id)

            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                extracted_data = await asyncio.to_thread(parse_image, image_data, self.api_key, self.endpoint)
                timing = "before" if i <= 1 else "after"
                await asyncio.to_thread(self.process_insert, extracted_data, discord_id, timing)

            await ctx.send(f"Data has been updated for {discord_id}!")
        except Exception as e:
            await ctx.send(f"Error occurred: {e}")

    @commands.command()
    async def rankedpitch(self, ctx):
        discord_id = ctx.author.id
        try:
            results = await asyncio.to_thread(self.fetch_comparison_data, discord_id)

            if not results:
                await ctx.send("No matching records found for comparison.")
                return

            data = []
            for row in results:
                player_name, diff_OUTS, diff_R, diff_H, diff_BB, diff_SLG, diff_HR, diff_SO, diff_G = row
                diff_SLG = round(diff_SLG, 3)
                diff_AB = diff_H + diff_OUTS

                ip = diff_OUTS // 3 + (diff_OUTS % 3) / 10
                era = round(diff_R / diff_OUTS * 27, 2) if diff_R > 0 else 0
                avg = round(diff_H / diff_AB, 3) if diff_H > 0 else 0
                walkrate = round((diff_BB / (diff_AB + diff_BB)) * 100, 1) if (diff_AB + diff_BB) > 0 else 0
                obp = round((diff_H + diff_BB) / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) > 0 else 0
                hrrate = round((diff_HR / diff_AB) * 100, 1) if diff_AB > 0 else 0
                slg = diff_SLG if diff_AB > 0 else 0
                ops = round(obp + slg, 3)
                krate = round((diff_SO / diff_AB) * 100, 1) if diff_AB > 0 else 0
                whip = round((diff_BB + diff_H) / diff_OUTS * 3, 3) if diff_OUTS > 0 else 0
                ipg = round(float(ip / diff_G), 3) if diff_G > 0 else 0

                data.append([
                    player_name, diff_G, ip, ipg, era, avg, obp, slg, ops,
                    walkrate, hrrate, krate, whip
                ])

            columns = [
                "Player Name", "G", "IP", "AVG IP/G", "ERA", "AVG", "OBP", "SLG", "OPS",
                "BB%", "HR%", "K%", "WHIP"
            ]
            df = pd.DataFrame(data, columns=columns)
            df = df.sort_values(by="ERA")
            buffer = render_table_image(df)
            await ctx.send(file=discord.File(fp=buffer, filename="stats_comparison.png"))
        except Exception as e:
            await ctx.send(f"Error comparing stats: {e}")

    def fetch_comparison_data(self, discord_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        a.PLAYERNAME,
                        b.outs - a.outs,
                        b.r - a.r,
                        b.h - a.h,
                        b.bb - a.bb,
                        CASE
                            WHEN (b.h + b.outs) - (a.h + a.outs) != 0 THEN
                                (b.slg * (b.h + b.outs) - a.slg * (a.h + a.outs)) / ((b.h + b.outs) - (a.h + a.outs))
                            ELSE 0
                        END,
                        b.HR - a.HR,
                        b.SO - a.SO,
                        b.G - a.G
                    FROM rankedpitchstats a
                    JOIN rankedpitchstats b
                        ON a.PLAYERNAME = b.PLAYERNAME
                    WHERE a.DISCORDID = %s AND b.DISCORDID = %s
                      AND a.TIMING = 'before' AND b.TIMING = 'after';
                """, (discord_id, discord_id))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return []


async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedPitchStats(bot, connection))
