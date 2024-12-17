import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

class NoticeScraper(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.base_url = "https://withhive.com/notice/game/509"
        self.today_date = "2024-12-17"
        #datetime.now().strftime("%Y-%m-%d")
        self.connection = connection
        self.check_notices.start()  # Start the periodic task

    def fetch_sent_notices(self):
        """Load sent notices from the database."""
        with self.connection.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS sent_notices (title TEXT PRIMARY KEY);")
            cur.execute("SELECT title FROM sent_notices;")
            return {row[0] for row in cur.fetchall()}

    def save_sent_notice(self, title):
        """Save the notice title to avoid re-sending."""
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO sent_notices (title) VALUES (%s) ON CONFLICT DO NOTHING;", (title,)
            )
        self.connection.commit()

    @tasks.loop(minutes=10)
    async def check_notices(self):
        print("Checking notices...")
        """Check for new notices."""
        # Configure Chrome options for Heroku
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")  # Required for non-GUI systems
        options.add_argument("--no-sandbox")  # Required for Heroku
        options.add_argument("--disable-dev-shm-usage")  # Prevent memory issues

        # Use Chrome path provided by Heroku buildpack
        options.binary_location = "/app/.apt/usr/bin/google-chrome"

        # ChromeDriver path is managed by Heroku buildpacks
        service = Service("/app/.chromedriver/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(self.base_url)
            await self.scrape_notices(driver)
        except Exception as e:
            print(f"Error during notice scraping: {e}")
        finally:
            driver.quit()

    async def scrape_notices(self, driver):
        """Find and send notices with today's date."""
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel 'bot-testing' not found.")
            return

        print("Starting to scrape notices...")
        sent_notices = self.fetch_sent_notices()
        print(f"Already sent notices: {sent_notices}")

        # Parse the static page source
        soup = BeautifulSoup(driver.page_source, "html.parser")
        notice_rows = soup.select("ul#notice_list_ul li.row")  # Target each row in the list
        print(f"Found {len(notice_rows)} rows in the table.")

        for row in notice_rows:
            try:
                # Extract date from the last 'div' column
                date_column = row.find_all("div", class_="col")[-1]
                site_date = date_column.get_text(strip=True)
                print(f"Checking row with date: {site_date}")

                if site_date == self.today_date:
                    # Extract title and onclick function
                    link_element = row.find("a", onclick=True)
                    if link_element:
                        title = link_element.get_text(strip=True)
                        onclick_attr = link_element["onclick"]  # e.g., notice.goDetailUrlView(76532)

                        # Extract notice ID using regex
                        match = re.search(r'goDetailUrlView\((\d+)\)', onclick_attr)
                        if match:
                            notice_id = match.group(1)
                            full_url = f"https://withhive.com/notice/view/{notice_id}"
                            print(f"Found notice: {title} - {full_url}")

                            if title not in sent_notices:
                                # Fetch content and send notice
                                content = self.fetch_notice_content(driver, full_url)
                                print(f"Fetched content for '{title}': {content[:100]}")
                                await self.send_notice(channel, title, full_url, content)
                                self.save_sent_notice(title)
                                sent_notices.add(title)
            except Exception as e:
                print(f"Error processing row: {e}")

    def fetch_notice_content(self, driver, url):
        """Fetch the content of a specific notice."""
        driver.get(url)
        time.sleep(2)  # Allow the page to load
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content = soup.find("div", class_="board_view")
        return content.get_text(strip=True) if content else "Content not found."

    async def send_notice(self, channel, title, url, content):
        """Send the notice as an embed to Discord."""
        embed = discord.Embed(
            title=title,
            url=url,
            description=content[:1500] + "...",  # Limit content size to 1500 characters
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Posted on {self.today_date}")
        await channel.send(embed=embed)

    @check_notices.before_loop
    async def before_check_notices(self):
        """Ensure the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

async def setup(bot):
    connection = bot.connection  # Retrieve the connection from the bot instance
    await bot.add_cog(NoticeScraper(bot, connection))
