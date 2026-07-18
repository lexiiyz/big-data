import asyncio
import os
import json
import socket
import urllib.request
import urllib.parse
from pymongo import MongoClient
from playwright.async_api import async_playwright


async def scrape_x_topic(page, query, max_tweets=50):
    print(f"Searching Twitter For: {query}")
    encoded_query = urllib.parse.quote(query, safe='()')
    await page.goto(f"https://x.com/search?q={encoded_query}")

    print("Tweet Load")
    try:
        await page.wait_for_selector('[data-testid="tweet"]', timeout=60000)
    except Exception as e:
        print(f"Failed to load tweet. Timeout: {e}")
        try:
            print(f"URL: {page.url}")
            print(f"Title: {await page.title()}")
        except Exception as inner_e:
            print(f"Error: {inner_e}")
        return []

    tweets_data = []
    seen_tweets = set()
    last_count = 0
    stuck_attempts = 0

    while len(tweets_data) < max_tweets:
        try:
            tweets = await page.query_selector_all('[data-testid="tweet"]')
        except Exception as e:
            print(f"DOM not stable, retrying... {e}")
            await page.wait_for_timeout(1000)
            continue

        for tweet in tweets:
            try:
                text_content = ""
                text_element = await tweet.query_selector('[data-testid="tweetText"]')
                if text_element:
                    text_content = await text_element.inner_text()
                    if not text_content or text_content in seen_tweets:
                        continue
                    seen_tweets.add(text_content)
                else:
                    handle_element = await tweet.query_selector('[data-testid="User-Name"]')
                    if not handle_element:
                        continue

                user_name = "Unknown"
                timestamp = "Unknown"
                likes = "0"

                user_info_element = await tweet.query_selector('[data-testid="User-Name"]')
                if user_info_element:
                    user_info_text = await user_info_element.inner_text()
                    lines = user_info_text.split('\n')
                    if len(lines) >= 2:
                        user_name = f"{lines[0]} ({lines[1]})"

                time_element = await tweet.query_selector('time')
                if time_element:
                    timestamp = await time_element.get_attribute('datetime')

                like_button = await tweet.query_selector('[data-testid="like"]')
                if like_button:
                    aria_label = await like_button.get_attribute('aria-label')
                    if aria_label:
                        likes = aria_label.split(' ')[0]
                        if likes == "Like":
                            likes = "0"

                tweet_detail = {
                    "user": user_name,
                    "timestamp": timestamp,
                    "likes": likes,
                    "text": text_content,
                    "query_topic": query
                }

                if text_content:
                    tweets_data.append(tweet_detail)

                if len(tweets_data) >= max_tweets:
                    break

            except Exception:
                continue

        if len(tweets_data) == last_count:
            stuck_attempts += 1
            if stuck_attempts >= 10:
                print(f"Stuck! No new tweet after {stuck_attempts} scroll. Done.")
                break
        else:
            stuck_attempts = 0

        last_count = len(tweets_data)

        if len(tweets_data) < max_tweets:
            print(f"Scrolling for more tweets... (Got {len(tweets_data)})")
            for _ in range(5):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(500)
            await page.wait_for_timeout(1000)

    print(f"Done. Total: {len(tweets_data)} tweets.")
    return tweets_data


async def run_twitter_scraper(query: str, max_tweets: int, topic: str = None, lang: str = None):
    final_query = f"{query} lang:{lang}" if lang else query

    async with async_playwright() as p:
        page = None
        browser = None
        try:
            base_cdp_url = os.getenv("CDP_URL", "http://localhost:9222")
            print(f"Getting WebSocket URL from {base_cdp_url}...")

            from urllib.parse import urlparse
            parsed = urlparse(base_cdp_url)
            try:
                host_ip = socket.gethostbyname(parsed.hostname)
            except Exception:
                host_ip = parsed.hostname
            port = parsed.port or 9222
            resolved_cdp_url = f"http://{host_ip}:{port}"

            req = urllib.request.Request(f"{resolved_cdp_url}/json/version")
            req.add_header("Host", f"localhost:{port}")
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    ws_url = data.get("webSocketDebuggerUrl")
                    if ws_url:
                        ws_url = ws_url.replace("localhost", host_ip).replace("127.0.0.1", host_ip)
                        cdp_url = ws_url
                    else:
                        cdp_url = resolved_cdp_url
            except Exception as e:
                print(f"Warning resolve json/version: {e}")
                cdp_url = resolved_cdp_url

            print(f"Connecting via CDP websocket: {cdp_url}")
            browser = await p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()

            hasil_scrape = await scrape_x_topic(page, final_query, max_tweets=max_tweets)
            display_topic = topic if topic else query

            mongo_uri = os.getenv("MONGO_URI")
            if mongo_uri and hasil_scrape:
                client = MongoClient(mongo_uri)
                collection = client["sentiment_db"]["tweets"]

                inserted_count = 0
                for tweet in hasil_scrape:
                    tweet["query_topic"] = display_topic
                    result = collection.update_one(
                        {"text": tweet["text"]},
                        {"$set": tweet},
                        upsert=True
                    )
                    if result.upserted_id:
                        inserted_count += 1

                print(f"Success save {inserted_count} new tweet to MongoDB (Topic: {display_topic})!")

            return len(hasil_scrape)

        except Exception as e:
            print(f"Twitter Scraper Error: {e}")
            raise e
        finally:
            if page: await page.close()
            if browser: await browser.close()
