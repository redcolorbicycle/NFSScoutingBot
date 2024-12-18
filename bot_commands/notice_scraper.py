import discord
from discord.ext import commands, tasks
import requests
from datetime import datetime

class NoticeScraper(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.connection = connection
        self.api_url = "https://withhive.com/api/notice/list/509"
        self.today_date = datetime.now().strftime("%Y-%m-%d")
        self.check_notices.start()
        
        # Initialize the database table
        self.create_table()

    def create_table(self):
        """Create the table to store sent notice IDs if it doesn't exist."""
        with self.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sent_notices (
                    notice_id BIGINT PRIMARY KEY
                );
            """)
        self.connection.commit()

    def is_notice_sent(self, notice_id):
        """Check if a notice ID has already been sent."""
        with self.connection.cursor() as cur:
            cur.execute("SELECT 1 FROM sent_notices WHERE notice_id = %s;", (notice_id,))
            return cur.fetchone() is not None

    def mark_notice_as_sent(self, notice_id):
        """Mark a notice ID as sent by storing it in the database."""
        with self.connection.cursor() as cur:
            cur.execute("INSERT INTO sent_notices (notice_id) VALUES (%s) ON CONFLICT DO NOTHING;", (notice_id,))
        self.connection.commit()

    @tasks.loop(minutes=1)
    async def check_notices(self):
        print("Checking notices...")
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel not found.")
            return

        # Mimic browser headers
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://withhive.com/notice/game/509",
            "X-Requested-With": "XMLHttpRequest",
        }

        payload = {"page": 1, "size": 20}

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                notices = self.parse_notices(response.json())
                for notice in notices:
                    notice_id = notice['id']

                    # Skip if notice has already been sent
                    if self.is_notice_sent(notice_id):
                        print(f"Skipping already sent notice: {notice_id}")
                        continue

                    # Send the notice
                    await channel.send(
                        f"**{notice['title']}**\n[View Notice]({notice['link']})"
                    )
                    print(f"Sent notice: {notice['title']}")

                    # Mark notice as sent
                    self.mark_notice_as_sent(notice_id)
            else:
                print(f"Failed to fetch notices. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching notices: {e}")

    def parse_notices(self, data):
        """Parse the JSON response to extract notice IDs with today's date."""
        notices = []
        try:
            notice_list = data.get("data", {}).get("notice_list", [])
            for item in notice_list:
                notice_date = item.get("startTime")
                if notice_date == self.today_date:
                    notices.append({
                        "id": item.get("noticeId"),
                        "title": item.get("noticeTitle"),
                        "date": notice_date,
                        "link": f"https://withhive.com/notice/509/{item.get('noticeId')}",
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
