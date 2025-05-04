import discord
from discord.ext import commands
import asyncio
import requests
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

class RankedBatStats(commands.Cog):
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

    def process_insert(self, raw_data, discord_id, timing, submission_time):
        try:
            data, newrow = [], []
            for i in range(len(raw_data)):
                if raw_data[i][0].isupper() or (raw_data[i][0:2] == "0." and raw_data[i][2].isalpha()):
                    newrow = [raw_data[i]]
                    continue
                elif len(newrow) in [1, 2, 3, 4, 5, 6, 7]:
                    newrow.append(raw_data[i])
                if len(newrow) == 8:
                    newrow.append("0" if newrow[-1] == "0" else raw_data[i + 1])
                    data.append(newrow)
                    newrow = []
            with self.connection.cursor() as cursor:
                for row in data:
                    cursor.execute("""
                        INSERT INTO rankedbatstats (
                            DISCORDID, PLAYERNAME, AB, H, BB, SLG, K, HR, SB, SBPCT, TIMING, submission_time
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (DISCORDID, PLAYERNAME, TIMING, submission_time) DO NOTHING;
                    """, (discord_id, *row, timing, submission_time))
                self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Insert Error: {e}")

    def trim_old_submissions(self, discord_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM rankedbatstats
                    WHERE (DISCORDID, submission_time) NOT IN (
                        SELECT DISCORDID, submission_time FROM rankedbatstats
                        WHERE DISCORDID = %s
                        ORDER BY submission_time DESC
                        LIMIT 4
                    );
                """, (discord_id,))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Trim Error: {e}")

    @commands.command()
    async def batters(self, ctx):
        attachments = ctx.message.attachments
        if len(attachments) != 4:
            await ctx.send("Please attach exactly 4 images.")
            return

        discord_id = ctx.author.id
        await ctx.send(f"Processing for {discord_id}...")

        try:
            submission_time = datetime.now()
            for i, attachment in enumerate(attachments):
                image_data = await attachment.read()
                extracted_data = await asyncio.to_thread(self.parse_image, image_data)
                timing = "before" if i <= 1 else "after"
                await asyncio.to_thread(self.process_insert, extracted_data, discord_id, timing, submission_time)
            await asyncio.to_thread(self.trim_old_submissions, discord_id)
            await ctx.send(f"✅ Data updated for {discord_id}!")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command()
    async def rankedbat(self, ctx):
        discord_id = ctx.author.id
        try:
            results = await asyncio.to_thread(self.fetch_comparison_data, discord_id)
            if not results:
                await ctx.send("No matching records found.")
                return
            buffer = await asyncio.to_thread(self.create_comparison_plot, results)
            file = discord.File(fp=buffer, filename="stats_comparison.png")
            await ctx.send(file=file)
        except Exception as e:
            await ctx.send(f"⚠️ Error comparing stats: {e}")


    def fetch_comparison_data(self, discord_id):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
    SELECT a.PLAYERNAME,
        b.AB - a.AB, b.H - a.H, b.HR - a.HR, b.BB - a.BB,
        b.SLG * b.AB - a.SLG * a.AB, b.SB - a.SB,
        CASE WHEN b.SBPCT > 0 AND a.SBPCT > 0 THEN
            ROUND((CAST(b.SB AS FLOAT) / CAST(b.SBPCT AS FLOAT)) * 100) -
            ROUND((CAST(a.SB AS FLOAT) / CAST(a.SBPCT AS FLOAT)) * 100)
        ELSE 0 END,
        b.K - a.K
    FROM rankedbatstats a
    JOIN rankedbatstats b 
        ON a.PLAYERNAME = b.PLAYERNAME 
        AND a.submission_time = b.submission_time
    WHERE a.DISCORDID = %s AND b.DISCORDID = %s
      AND a.TIMING = 'before' AND b.TIMING = 'after'
      AND a.submission_time = (
          SELECT MAX(submission_time) FROM rankedbatstats WHERE DISCORDID = %s
      );
""", (discord_id, discord_id, discord_id))

                return cursor.fetchall()
        except Exception as e:
            print(f"Fetch Error: {e}")
            return []

    def create_comparison_plot(self, results):
        data = []
        for row in results:
            player_name, diff_AB, diff_H, diff_HR, diff_BB, diff_BASES, diff_SB, diff_SBA, diff_K = row

            avg = round(diff_H / diff_AB, 3) if diff_AB else 0
            walkrate = round((diff_BB / (diff_AB + diff_BB)) * 100, 1) if (diff_AB + diff_BB) else 0
            obp = round((diff_H + diff_BB) / (diff_AB + diff_BB), 3) if (diff_AB + diff_BB) else 0
            hrrate = round((diff_HR / diff_AB) * 100, 1) if diff_AB else 0
            slg = round(diff_BASES / diff_AB, 3) if diff_AB else 0
            ops = round(obp + slg, 3)
            sbrate = round((diff_SB / diff_SBA) * 100, 1) if (diff_SBA > 0 and diff_SB > 0) else 0
            krate = round((diff_K / diff_AB) * 100, 1) if diff_AB else 0

            data.append([
                player_name, diff_AB, avg, diff_BB, walkrate, diff_K, krate, obp,
                diff_HR, hrrate, slg, ops, diff_SB, sbrate
            ])

        columns = [
            "Player Name", "AB", "Avg", "BB", "BB%", "K", "K%", "OBP",
            "HR", "HR%", "SLG", "OPS", "SB", "SB%"
        ]

        df = pd.DataFrame(data, columns=columns)
        df = df.sort_values(by="OPS", ascending=False)

        fig, ax = plt.subplots(figsize=(24, len(df) * 0.5 + 1))
        ax.axis("tight")
        ax.axis("off")

        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc="center",
            loc="center",
        )

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

    def fetch_metric_trend(self, discord_id, metric):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT submission_time
                    FROM rankedbatstats
                    WHERE DISCORDID = %s
                    ORDER BY submission_time DESC
                    LIMIT 4;
                """, (discord_id,))
                timestamps = [row[0] for row in cursor.fetchall()][::-1]

            player_data = {}
            for ts in timestamps:
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT PLAYERNAME, SUM(H), SUM(BB), SUM(SLG * AB), SUM(AB)
                        FROM rankedbatstats
                        WHERE DISCORDID = %s AND submission_time = %s
                        GROUP BY PLAYERNAME;
                    """, (discord_id, ts))
                    rows = cursor.fetchall()

                current_players = set(name for name, *_ in rows)
                for name, h, bb, total_bases, ab in rows:
                    value = 0
                    if ab:
                        if metric == "avg":
                            value = round(h / ab, 3)
                        elif metric == "obp":
                            value = round((h + bb) / (ab + bb), 3) if (ab + bb) else 0
                        elif metric == "slg":
                            value = round(total_bases / ab, 3)
                        elif metric == "ops":
                            obp = round((h + bb) / (ab + bb), 3) if (ab + bb) else 0
                            slg = round(total_bases / ab, 3)
                            value = round(obp + slg, 3)
                    player_data.setdefault(name, []).append(value)
                for name in player_data:
                    if name not in current_players:
                        player_data[name].append(None)
            return timestamps, player_data
        except Exception as e:
            print(f"Fetch metric trend error: {e}")
            return [], {}

    def plot_metric_trend(self, timestamps, player_data, metric):
        plt.figure(figsize=(12, 6))
        x_labels = [f"#{i+1}" for i in range(len(timestamps))]
        for name, values in player_data.items():
            plt.plot(x_labels, values, marker='o', label=name)
        plt.title(f"{metric.upper()} over last 4 uploads")
        plt.xlabel("Submission Order")
        plt.ylabel(metric.upper())
        plt.ylim(0, 2)
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.grid(True)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
        buffer.seek(0)
        plt.close()
        return buffer

    @commands.command()
    async def rankedavg(self, ctx):
        timestamps, player_data = await asyncio.to_thread(self.fetch_metric_trend, ctx.author.id, "avg")
        if not player_data:
            await ctx.send("No data to plot AVG.")
            return
        buffer = await asyncio.to_thread(self.plot_metric_trend, timestamps, player_data, "avg")
        await ctx.send(file=discord.File(fp=buffer, filename="rankedavg.png"))

    @commands.command()
    async def rankedobp(self, ctx):
        timestamps, player_data = await asyncio.to_thread(self.fetch_metric_trend, ctx.author.id, "obp")
        if not player_data:
            await ctx.send("No data to plot OBP.")
            return
        buffer = await asyncio.to_thread(self.plot_metric_trend, timestamps, player_data, "obp")
        await ctx.send(file=discord.File(fp=buffer, filename="rankedobp.png"))

    @commands.command()
    async def rankedslg(self, ctx):
        timestamps, player_data = await asyncio.to_thread(self.fetch_metric_trend, ctx.author.id, "slg")
        if not player_data:
            await ctx.send("No data to plot SLG.")
            return
        buffer = await asyncio.to_thread(self.plot_metric_trend, timestamps, player_data, "slg")
        await ctx.send(file=discord.File(fp=buffer, filename="rankedslg.png"))

    @commands.command()
    async def rankedops(self, ctx):
        timestamps, player_data = await asyncio.to_thread(self.fetch_metric_trend, ctx.author.id, "ops")
        if not player_data:
            await ctx.send("No data to plot OPS.")
            return
        buffer = await asyncio.to_thread(self.plot_metric_trend, timestamps, player_data, "ops")
        await ctx.send(file=discord.File(fp=buffer, filename="rankedops.png"))

async def setup(bot):
    connection = bot.connection
    await bot.add_cog(RankedBatStats(bot, connection))
