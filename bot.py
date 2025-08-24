import feedparser
import os
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler

# ---- Настройки из переменных окружения ----
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ---- RSS источники (расширенный список) ----
RSS_FEEDS = {
    "Главные новости": [
        "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "https://cointelegraph.com/rss/tag/nft",
        "https://decrypt.co/feed/tag/nft",
        "https://nftnow.com/feed/"
    ],
    "Маркетплейсы": [
        "https://opensea.io/blog/rss",
        "https://rarible.medium.com/feed",
        "https://dappradar.com/blog/rss",
        "https://nftcalendar.io/rss"
    ],
    "TON-проекты": [
        "https://tonkeeper.com/blog/rss",
        "https://ton.org/rss",
        "https://t.me/s/ton_news?format=rss"
    ],
    "Сообщество": [
        "https://www.reddit.com/r/NFT/.rss",
        "https://twitrss.me/twitter_user_to_rss/?user=NFTNow",
        "https://nfteventcalendar.com/rss"
    ]
}

KEYWORDS = ["NFT", "TON", "NFT marketplace", "collection"]

HISTORY_FILE = "sent_news.txt"
bot = Bot(token=TELEGRAM_TOKEN)
scheduler = BlockingScheduler()

# ---- Функции ----
def load_sent_news():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f.readlines())

def save_sent_news(sent):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for url in sent:
            f.write(url + "\n")

def fetch_news():
    news_items = {}
    sent_news = load_sent_news()
    new_sent = set(sent_news)

    for section, feeds in RSS_FEEDS.items():
        section_items = []
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if any(keyword.lower() in entry.title.lower() for keyword in KEYWORDS):
                    if entry.link not in sent_news:
                        section_items.append(f"• {entry.title}\n{entry.link}")
                        new_sent.add(entry.link)
        if section_items:
            news_items[section] = section_items

    save_sent_news(new_sent)
    return news_items

def send_digest():
    news_items = fetch_news()
    if not news_items:
        bot.send_message(chat_id=CHAT_ID, text="Сегодня новостей NFT нет 😎")
        return

    date_str = datetime.now().strftime("%d.%m.%Y")
    digest = f"📣 NFT Дайджест – {date_str}\n\n"
    for section, items in news_items.items():
        digest += f"📌 {section}:\n" + "\n".join(items) + "\n\n"

    bot.send_message(chat_id=CHAT_ID, text=digest)

# ---- Планировщик ----
scheduler.add_job(send_digest, 'cron', hour=9, minute=0)
scheduler.start()
