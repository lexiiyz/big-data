import asyncio
import os
import json
import urllib.request
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pymongo import MongoClient
from playwright.async_api import async_playwright

app = FastAPI(title="Twitter Scraper API")

class ScrapeRequest(BaseModel):
    query: str
    max_tweets: int = 30

async def scrape_x_topic(page, query, max_tweets=50):
    print(f"Navigasi ke pencarian X untuk: {query}")
    encoded_query = query.replace(" ", "%20")
    await page.goto(f"https://x.com/search?q={encoded_query}&src=typed_query")
    
    print("Menunggu tweet load...")
    try:
        await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
    except Exception:
        print("Gagal memuat tweet.")
        return []

    tweets_data = []
    seen_tweets = set()
    
    while len(tweets_data) < max_tweets:
        tweets = await page.query_selector_all('[data-testid="tweet"]')
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
                    pass
                
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
                    "query_topic": query # Tambahan untuk nandain ini hasil query apa
                }
                
                if text_content: 
                    tweets_data.append(tweet_detail)
                        
                if len(tweets_data) >= max_tweets:
                    break
                    
            except Exception:
                continue

        if len(tweets_data) < max_tweets:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
        
    return tweets_data

async def run_scraper(query: str, max_tweets: int):
    async with async_playwright() as p:
        cdp_url = os.getenv("CDP_URL", "http://127.0.0.1:9222")
        try:
            req = urllib.request.Request(f"{cdp_url.replace('ws://', 'http://')}/json/version")
            req.add_header('Host', 'localhost:9222')
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                ws_url = data['webSocketDebuggerUrl']
                if "host.docker.internal" in cdp_url:
                    ws_url = ws_url.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
                cdp_url = ws_url
        except Exception:
            pass
            
        try:
            browser = await p.chromium.connect_over_cdp(cdp_url)
            
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                page = pages[0] if pages else await context.new_page()
            else:
                context = await browser.new_context()
                page = await context.new_page()

            hasil_scrape = await scrape_x_topic(page, query, max_tweets=max_tweets)
            
            mongo_uri = os.getenv("MONGO_URI")
            if mongo_uri and hasil_scrape:
                client = MongoClient(mongo_uri)
                db = client["sentiment_db"]
                collection = db["tweets"]
                
                # Menggunakan upsert untuk menghindari duplikasi data berdasarkan teks tweet
                inserted_count = 0
                for tweet in hasil_scrape:
                    result = collection.update_one(
                        {"text": tweet["text"]}, 
                        {"$set": tweet}, 
                        upsert=True
                    )
                    if result.upserted_id:
                        inserted_count += 1
                        
                print(f"Berhasil menyimpan {inserted_count} tweet baru ke MongoDB (dari {len(hasil_scrape)} yang di-scrape)!")
                
            return len(hasil_scrape)
            
        except Exception as e:
            print(f"Scraper Error: {e}")
            raise e

@app.post("/api/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scraper, request.query, request.max_tweets)
    return {
        "status": "success", 
        "message": f"Mulai scraping otomatis untuk '{request.query}'. Data akan masuk ke MongoDB."
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "twitter_scraper_api"}
