import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import asyncio

class UpdateNotices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://withhive.com"
        self.notice_url = f"{self.base_url}/notice/game/509"
        self.last_posted = set()  # Store titles of notices already posted to avoid duplicates
        self.check_notices.start()  # Start the periodic task

    def cog_unload(self):
        self.check_notices.cancel()

    async def fetch_notice_content(self, url):
        """
        Fetches the content of a specific notice page.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract content; adjust the selector based on the page structure
            content = soup.find("div", class_="board_view")  # Example class
            if content:
                return content.get_text(strip=True)[:1500] + "..."  # Limit content size
            return "Unable to fetch the notice content."
        except Exception as e:
            return f"Error fetching notice content: {e}"

    @tasks.loop(minutes=10)  # Check for new updates every 10 minutes
    async def check_notices(self):
        """
        Periodically checks the WithHive notices page for new updates.
        """
        try:
            response = requests.get(self.notice_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the notices in the table
            notice_rows = soup.select("table tbody tr")  # Adjust this selector for accuracy
            channel = self.bot.get_channel(YOUR_CHANNEL_ID)  # Replace with your channel ID

            for row in notice_rows:
                # Extract columns: title, link, and registration date
                title_element = row.find("a")
                title = title_element.get_text(strip=True)
                link = f"{self.base_url}{title_element['href']}"
                date_element = row.find("td", text=True).get_text(strip=True)
                notice_date = datetime.strptime(date_element, "%Y-%m-%d").date()

                # Check if the notice is from today and not already posted
                if notice_date == datetime.now().date() and title not in self.last_posted:
                    self.last_posted.add(title)  # Mark as posted
                    content = await self.fetch_notice_content(link)

                    # Format and send the message
                    embed = discord.Embed(
                        title=title,
                        url=link,
                        description=content,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text=f"Posted on {notice_date}")
                    await channel.send(embed=embed)
                    await asyncio.sleep(2)  # Avoid spamming Discord API
        except Exception as e:
            print(f"Error checking notices: {e}")

    @check_notices.before_loop
    async def before_check_notices(self):
        """
        Wait until the bot is ready before starting the loop.
        """
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(UpdateNotices(bot))
