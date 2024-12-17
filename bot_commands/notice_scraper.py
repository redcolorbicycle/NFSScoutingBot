import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

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
        """Scrape notices with retries to ensure correct content."""
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel 'bot-testing' not found.")
            return

        retries = 5  # Number of retries to fetch the correct content
        wait_time = 3  # Seconds to wait between retries
        correct_content = None

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}/{retries} to fetch page content...")
                response = requests.get(self.base_url, timeout=10)
                if response.status_code == 200:
                    # Parse the page content and check for the target element
                    soup = BeautifulSoup(response.text, "html.parser")
                    notice_list = soup.find("ul", id="notice_list_ul")
                    await channel.send(notice_list)

                    if notice_list:  # If the correct content is loaded
                        correct_content = soup
                        print("Correct content loaded.")
                        break
                else:
                    print(f"Response status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")

            time.sleep(wait_time)  # Wait before retrying

        if not correct_content:
            await channel.send("Failed to load the correct content after retries.")
            return

        # Extract rows with today's date
        notice_list = correct_content.find("ul", id="notice_list_ul")
        rows = notice_list.find_all("li", class_="row")
        matched_rows = []

        for row in rows:
            date_col = row.find("div", class_="col")  # Date column
            if date_col and date_col.get_text(strip=True) == self.today_date:
                matched_rows.append(row)

        # Send the matched rows to Discord
        if matched_rows:
            for row in matched_rows:
                row_text = row.get_text(separator="\n", strip=True)
                await self.send_in_chunks(channel, row_text)
        else:
            await channel.send("No notices found for today's date.")

    async def send_in_chunks(self, channel, text, chunk_size=2000):
        """Send long text in chunks."""
        for i in range(0, len(text), chunk_size):
            await channel.send(f"```{text[i:i+chunk_size]}```")

    @check_notices.before_loop
    async def before_check_notices(self):
        """Ensure the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(NoticeScraper(bot, connection))
