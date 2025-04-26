import discord
from discord.ext import commands
import asyncio
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import os

class RankedPitchStats(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.api_key = os.getenv('AZURE_API_KEY')
        self.endpoint = os.getenv('AZURE_ENDPOINT') + '/vision/v3.2/read/analyze'

    async def cog_check(self, ctx):
        allowed_user_ids = [
            355004588186796035, 327567846567575554, 249243533246988292,
            1209287557121318974, 635463073712570385, 237066640448159746,
            460950294893690880, 1231605248041156653, 698184128478314566,
            958512461500276736, 629122681261785118, 143909682237538304,
            1145543271330881599, 1091901514848678061, 536258698461577236,
            1042374780550135868, 200767106453733386, 617029165597720592,
            308760445160783882, 788709027570778123, 789922571834884107
        ]
        return ctx.author.id in allowed_user_ids

    def parse_image(self, image_data):
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/octet-stream'
            }
            response = requests.post(self.endpoint, headers=headers, data=image_data)
            if response.status_code == 202:
                operation_location = response.headers["Operation-Location"]
                import time
                while True:
                    result_response = requests.get(operation_location, headers=headers)
                    if result_response.status_code != 200:
                        return ""
                    result = result_response.json()
                    if result.get("status") == "succeeded":
                        return [line["text"] for read_result in result["analyzeResult"]["readResults"] for line in read_result["lines"]]
                    elif result.get("status") == "failed":
                        return ""
                    time.sleep(1)
            else:
                return ""
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

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
            data, newrow = [], []
            for i in range(len(raw_data)):
                if raw_data[i] == "...":
                    continue
                if raw_data[i][0].isupper() or (raw_data[i][0:2] == "0." and raw_data[i][2].isalpha()):
                    newrow = [raw_data[i]]
                    continue
                elif len(newrow) == 1:
                    if "." in raw_data[i]:
                        integer_part, decimal_part = raw_data[i].split(".")
                        integer_part = int(integer_part)
                        if decimal_part == "1":
                            newrow.append(integer_part * 3 + 1)
                        elif decimal_part == "2":
                            newrow.append(integer_part * 3 + 2)
                        else:
                            newrow.append(integer_part * 3)
                else:
                    newrow.append(raw_data[i])
                    data.append(newrow)

            with self.connection.cursor() as cursor:
                for row in data:
                    cursor.execute("""
                        INSERT INTO rankedpitchstats (
                            DISCORDID, PLAYERNAME, OUTS, R, H, BB, SLG, HR, SO, TIMING, G
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (DISCORDID, PLAYERNAME, TIMING) DO NOTHING;
                    """, (discord_id, *row, timing))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Insert Error: {e}")

    def fetch_comparison_data(self, discord_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT a.PLAYERNAME,
                        b.outs - a.outs, b.r - a.r, b.h - a.h, b.bb - a.bb,
                        CASE WHEN (b.h + b.outs) - (a.h + a.outs) != 0 THEN (b.slg * (b.h + b.outs) - a.slg * (a.h + a.outs))/((b.h + b.outs) - (a.h + a.outs)) ELSE 0 END,
                        b.HR - a.HR, b.SO - a.SO, b.G - a.G
                    FROM rankedpitchstats a
                    JOIN rankedpitchstats b ON a.PLAYERNAME = b.PLAYERNAME
                    WHERE a.DISCORDID = %s AND b.DISCORDID = %s
                    AND a.TIMING = 'before' AND b.TIMING = 'after';
                """, (discord_id, discord_id))
                return cursor.fetchall()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return []

    def create_pitching_plot(self, results):
        data = []
        for row in results:
            player_name, diff_OUTS, diff_R, diff_H, diff_BB, diff_SLG, diff_HR, diff_SO, diff_G = row
            diff_AB = diff_H + diff_OUTS
            ip = diff_OUTS // 3 + (diff_OUTS % 3) / 10
            era = round(diff_R / diff_OUTS * 27, 2) if diff_OUTS else 0
            avg = round(diff_H / diff_AB, 3) if diff_H else 0
            walkrate = round((diff_BB / (diff_AB + diff_BB)) * 100, 1) if (diff_AB + diff_BB) else 0
            obp = round((diff_H + diff_BB) / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) else 0
            hrrate = round((diff_HR / diff_AB) * 100, 1) if diff_AB else 0
            slg = diff_SLG if diff_AB else 0
            ops = round(obp + slg, 3)
            krate = round((diff_SO / diff_AB) * 100, 1) if diff_AB else 0
            whip = round((diff_BB + diff_H) / diff_OUTS * 3, 3) if diff_OUTS else 0
            ipg = round(ip / diff_G, 3) if diff_G > 0 else 0

            data.append([player_name, diff_G, ip, ipg, era, avg, obp, slg, ops, diff_BB, walkrate, diff_HR, hrrate, diff_SO, krate, whip])

        columns = ["Player Name", "G", "IP", "AVG IP/G", "ERA", "AVG", "OBP", "SLG", "OPS", "BB", "BB%", "HR", "HR%", "K", "K%", "WHIP"]

        df = pd.DataFrame(data, columns=columns)
        df = df.sort_values(by="ERA")

        fig, ax = plt.subplots(figsize=(24, len(df) * 0.5 + 1))
        ax.axis("off")
        table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.auto_set_column_width(col=list(range(len(df.columns))))

        cell_dict = table.get_celld()
        for (row, col), cell in cell_dict.items():
            if row == 0 or col == 0:
                cell.set_text_props(weight="bold")

        row_height = 1 / (len(df) + 1)
        for (row, col), cell in cell_dict.items():
            cell.set_height(row_height)

        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight", dpi=300)
        buffer.seek(0)
        plt.close(fig)
        return buffer

    @commands.command()
    async def pitchers(self, ctx):
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images.")
            return

        discord_id = ctx.author.id
        await ctx.send(f"Processing for {discord_id}...")

        try:
            await asyncio.to_thread(self.delete_user_data, discord_id)

            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                extracted_data = await asyncio.to_thread(self.parse_image, image_data)
                timing = "before" if i <= 1 else "after"
                await asyncio.to_thread(self.process_insert, extracted_data, discord_id, timing)

            await ctx.send(f"✅ Data updated for {discord_id}!")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command()
    async def rankedpitch(self, ctx):
        discord_id = ctx.author.id
        try:
            results = await asyncio.to_thread(self.fetch_comparison_data, discord_id)
            if not results:
                await ctx.send("No matching records found.")
                return
            buffer = await asyncio.to_thread(self.create_pitching_plot, results)
            file = discord.File(fp=buffer, filename="stats_comparison.png")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"⚠️ Error comparing stats: {e}")

async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedPitchStats(bot, connection))
