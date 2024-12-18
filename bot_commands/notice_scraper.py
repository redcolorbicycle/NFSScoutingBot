import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime

class NoticeScraper(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.api_url = "https://withhive.com/api/notice/list/509"
        self.today_date = "2024-12-17"
        #datetime.now().strftime("%Y-%m-%d")
        self.check_notices.start()

    @tasks.loop(minutes=1)
    async def check_notices(self):
        print("Checking notices...")
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel 'bot-testing' not found.")
            return

        # Mimic browser headers copied from Network tab
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://withhive.com/notice/game/509",
            "X-Requested-With": "XMLHttpRequest",
        }

        payload = {
            "page": 1,  # Pagination
            "size": 20  # Fetch 20 results at a time
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)

            if response.status_code == 200:
                try:
                    json_response = response.json()
                    notices = self.parse_notices(json_response)
                    for notice in notices:
                        await channel.send(f"**{notice['title']}**\n{notice['link']}\n")
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
            else:
                print(f"Failed to fetch notices. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching notices: {e}")

    def parse_notices(self, data):
        """Parse the JSON response to extract notice IDs with today's date."""
        notices = []
        try:
            # Access the notice list inside the "data" key
            notice_list = data.get("data", {}).get("notice_list", [])
            
            for item in notice_list:
                # Extract the `startTime` key to match against today's date
                notice_date = item.get("startTime")
                if notice_date == self.today_date:  # Compare against today's date
                    notices.append({
                        "id": item.get("noticeId"),  # Extract the notice ID
                        "title": item.get("noticeTitle"),  # Extract the title
                        "date": notice_date,  # Include the notice date
                        "link": f"https://withhive.com/notice/509/{item.get('noticeId')}",  # Construct the notice link
                    })
        except Exception as e:
            print(f"Error parsing notices: {e}")

        return notices


    @check_notices.before_loop
    async def before_check_notices(self):
        """Ensure the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    connection = bot.connection
    await bot.add_cog(NoticeScraper(bot, connection))
