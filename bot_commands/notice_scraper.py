import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time

class NoticeScraper(commands.Cog):
    def __init__(self, bot, connection):
        self.bot = bot
        self.base_url = "https://withhive.com/notice/game/509"
        self.today_date = datetime.now().strftime("%Y-%m-%d")
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
        print("checking notices...")
        """Check for new notices."""
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")  # Disable GPU acceleration for smoother headless mode
        service = Service("/path/to/chromedriver")  # Replace with your chromedriver path
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(self.base_url)
            await self.scrape_notices(driver)
        except Exception as e:
            print(f"Error during notice scraping: {e}")
        finally:
            driver.quit()

    async def scrape_notices(self, driver):
        """Scroll, find, and send notices with today's date."""
        channel = discord.utils.get(self.bot.get_all_channels(), name="bot-testing")
        if not channel:
            print("Channel 'bot-testing' not found.")
            return

        print("Starting to scrape notices...")
        sent_notices = self.fetch_sent_notices()
        print(f"Already sent notices: {sent_notices}")
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Parse the page source
            soup = BeautifulSoup(driver.page_source, "html.parser")
            rows = soup.select("table tbody tr")
            print(f"Found {len(rows)} rows in the table.")

            for row in rows:
                date_cell = row.find_all("td")[-1]  # Date is in the last column
                site_date = date_cell.get_text(strip=True)
                print(f"Checking row with date: {site_date}")

                if site_date == self.today_date:
                    link_element = row.find("a")
                    if link_element:
                        title = link_element.get_text(strip=True)
                        link = link_element["href"]
                        full_url = f"https://withhive.com{link}"

                        print(f"Found notice: {title} - {full_url}")

                        if title not in sent_notices:
                            content = self.fetch_notice_content(driver, full_url)
                            print("Fetched content:", content[:100])  # Log first 100 characters
                            await self.send_notice(channel, title, full_url, content)
                            self.save_sent_notice(title)
                            sent_notices.add(title)

            # Scroll down
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # Stop when no more content loads
                print("Reached bottom of the page.")
                break
            last_height = new_height

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
