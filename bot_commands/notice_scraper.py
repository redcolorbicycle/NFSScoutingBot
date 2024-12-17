import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class NoticeScraper(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.base_url = "https://withhive.com/notice/game/509"
        self.today_date = "2024-12-17"
        #datetime.now().strftime("%Y-%m-%d")  # Get today's date
        self.connection = connection
        self.check_notices.start()  # Start the periodic task

    @tasks.loop(minutes=10)
    async def check_notices(self):
        """Fetch and send rows from the page where the date matches today's date."""
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel 'bot-testing' not found.")
            return

        try:
            # Step 1: Fetch the webpage content
            response = requests.get(self.base_url)
            response.raise_for_status()  # Raise an error if the page couldn't be fetched
            
            # Step 2: Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")
            await channel.send(soup)

            # Step 3: Find all rows under 'notice_list_ul'
            notice_list = soup.find("ul", id="notice_list_ul")
            if not notice_list:
                print("Could not find the 'notice_list_ul' element.")
                await channel.send("Could not retrieve notices.")
                return

            rows = notice_list.find_all("li", class_="row")  # Rows within the list
            matched_rows = []

            # Step 4: Check each row for today's date
            for row in rows:
                date_col = row.find("div", class_="col")  # Find the date column
                if date_col and date_col.get_text(strip=True) == self.today_date:
                    matched_rows.append(row)

            # Step 5: Send matched rows to the Discord channel
            if matched_rows:
                for row in matched_rows:
                    # Extract the whole row as text
                    row_text = row.get_text(separator="\n", strip=True)
                    await channel.send(f"```{row_text}```")
            else:
                await channel.send("No notices found for today's date.")

        except Exception as e:
            print(f"Error fetching or parsing notices: {e}")
            await channel.send(f"Error fetching notices: {e}")

    @check_notices.before_loop
    async def before_check_notices(self):
        """Ensure the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(NoticeScraper(bot, connection))
