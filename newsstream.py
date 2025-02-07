import requests
import time
import logging
from textblob import TextBlob
from gtts import gTTS
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os
import json
import random
import subprocess

# This software created to run on an UBUNTU machine with HomeAssistant and LLAMA.CPP and the stream generated can be accessed via the machine's IP address on port 8000 using VLC's network stream playing option.

# Configuration for NewsAPI
NEWS_API_URL = "https://newsapi.org/v2/everything"
NEWS_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your free NewsAPI key from https://newsapi.org
NEWS_QUERY = "cryptocurrency OR technology OR business"

# Configuration for CoinGecko API (no API key needed but beware of throttling)
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINS = ["bitcoin", "ethereum", "solana", "cosmos"]
#COINS = ["bitcoin", "ethereum", "solana", "cosmos", "dogecoin", "shiba-inu"]
#COINS = ["bitcoin"]

# Configuration for LLM APIs with failover
LLM_API_URLS = [
    "http://192.168.42.254:8080/completion",  # Primary LLM URL
    "http://192.168.42.15:8080/completion"   # Failover LLM URL
]

# Instructions for the chatbot
INSTRUCTIONS = """
You are a news anchor. Summarize the following story and remind viewers to like and subscribe. Replace any advertisements with the phrase Sponsored by Graphinex Tech Services
"""

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("news_sentiment.log"), logging.StreamHandler()]
)

analyzed_articles_file = "analyzed_articles.json"
previous_analyzed_articles = {}
looping_tts_clips = []

musac_clips = ["musac1.mp4", "musac2.mp4", "musac3.mp4"]  # Paths to musac clips

def load_analyzed_articles():
    """
    Loads previously analyzed articles from the file.
    """
    global previous_analyzed_articles
    try:
        with open(analyzed_articles_file, "r") as file:
            previous_analyzed_articles = json.load(file)
    except FileNotFoundError:
        previous_analyzed_articles = {}

def save_analyzed_articles():
    """
    Saves the analyzed articles to the file.
    """
    with open(analyzed_articles_file, "w") as file:
        json.dump(previous_analyzed_articles, file)

def fetch_news():
    """
    Fetches crypto-related news from NewsAPI.
    """
    params = {
        "q": NEWS_QUERY,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
    }
    response = requests.get(NEWS_API_URL, params=params)
    response.raise_for_status()
    return response.json().get("articles", [])

def fetch_coin_metrics():
    """
    Fetches cryptocurrency metrics from CoinGecko.
    """
    coin_metrics = []
    for coin in COINS:
        url = f"{COINGECKO_API_URL}/coins/{coin}"
        response = requests.get(url)
        data = response.json()

        # Print the data to debug
        print(data)

        # Safely access dictionary keys
        name = data.get("name", "Unknown")
        symbol = data.get("symbol", "Unknown").upper()
        market_data = data.get("market_data", {})
        price = market_data.get("current_price", {}).get("usd", 0)
        price_change_24h = market_data.get("price_change_percentage_24h", 0)
        price_change_7d = market_data.get("price_change_percentage_7d", 0)
        market_cap = market_data.get("market_cap", {}).get("usd", 0)
        volume_24h = market_data.get("total_volume", {}).get("usd", 0)
        high_24h = market_data.get("high_24h", {}).get("usd", 0)
        low_24h = market_data.get("low_24h", {}).get("usd", 0)

        metric_text = (
            f"{name} ({symbol}) is currently trading at ${price:,.2f}, "
            f"{'up' if price_change_24h >= 0 else 'down'} {abs(price_change_24h):.2f}% in the last 24 hours "
            f"and {abs(price_change_7d):.2f}% over the past week. "
#            f"The market cap is ${market_cap:,.0f}, with a 24-hour trading volume of ${volume_24h:,.0f}. "
            f"Today's high and low prices were ${high_24h:,.2f} and ${low_24h:,.2f}."
        )
        coin_metrics.append(metric_text)

        # Add a delay to avoid hitting the rate limit
        time.sleep(2)  # Adjust the delay as needed

    return coin_metrics

def analyze_sentiment(text):
    """
    Analyzes the sentiment of the given text using TextBlob.
    """
    return TextBlob(text).sentiment.polarity

def generate_response(prompt):
    """
    Generates a response using the locally hosted ChatGPT-like API.
    """
    payload = {
        "prompt": f"{INSTRUCTIONS} {prompt}",
        "temperature": 0.7,
        "max_tokens": 500,
    }
    for url in LLM_API_URLS:
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json().get("content", "").strip() if response.json() else None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to generate response from {url}: {e}")
            continue
    return None

def generate_visuals_with_audio(text, output_video_path):
    """
    Generates a video with visuals and embedded audio using FFmpeg.
    """
    # Generate TTS audio
    tts = gTTS(text=text, lang='en')
    audio_path = "temp_audio.mp3"
    tts.save(audio_path)

    # Generate subtitles
    subtitle_path = "temp_subtitles.srt"
    with open(subtitle_path, "w") as subtitle_file:
        subtitle_file.write(f"1\n00:00:00,000 --> 00:00:10,000\n{text}\n")

    # FFmpeg command to generate visuals with audio and subtitles
    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Overwrite output file if it exists
        "-i", audio_path,  # Input audio file
#        "-vf", f"subtitles={subtitle_path}",  # Add subtitles
        "-filter_complex", "showwaves=mode=line:colors=0xFFFFFF:rate=25:size=1280x720",  # Waveform visualization
        "-c:v", "libx264",  # Video codec
        "-pix_fmt", "yuv420p",  # Pixel format
        "-c:a", "aac",  # Audio codec
        "-strict", "experimental",  # Allow experimental codecs
        output_video_path,  # Output video file
    ]

    try:
        # Run the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        logging.info(f"Generated video with visuals and audio at {output_video_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to generate video: {e}")
    finally:
        # Clean up temporary files
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(subtitle_path):
            os.remove(subtitle_path)

def pre_generate_tts_clips():
    """
    Pre-generates TTS clips and adds them to the looping queue.
    """
    global previous_analyzed_articles, looping_tts_clips

    # Queue the intro which will loop while the news articles build.
    print('Queueing intro..')
    looping_tts_clips.append('musac1.mp4')

    # Fetch cryptocurrency metrics
    print('Fetching coin market metrics...')
    coin_metrics = fetch_coin_metrics()
    for metric in coin_metrics:
        print('Generating coin market TTS...')
        tts = gTTS(text=metric, lang='en')
        clip_path = f"tts_clips/coin_metrics_{hash(metric)}.mp3"
        tts.save(clip_path)

        print('Generating coin market visuals..')
        # Generate visuals for the TTS clip
        video_path = f"tts_clips/coin_metrics_{hash(metric)}.mp4"
        generate_visuals_with_audio(metric, video_path)
        looping_tts_clips.append(video_path)

    print('Fetching news articles..')
    articles = fetch_news()
    if not articles:
        logging.warning("No articles found.")
        return

    for article in articles:
        article_id = article["url"]
        # Handle case where description is None
        article_title = article["title"]
        article_text = (article.get("description") or "")
        current_sentiment = analyze_sentiment(article_text)
        sentiment_label = "Positive" if current_sentiment > 0 else "Negative"
        article_full = article_title + article_text
        print('News LLM synopsis..')
        # Initialize the article entry if it doesn't exist
        if article_id not in previous_analyzed_articles:
            prompt = f"Analyze this article: {article_text}"
            llm_response = generate_response(prompt)
            if llm_response:
                previous_analyzed_articles[article_id] = {
                    "sentiment": current_sentiment,
                    "analysis": llm_response,
                }
                save_analyzed_articles()
            else:
                # If no response is generated, skip this article with a continue (now disabled)
#                continue
                # Default to using article text if LLM not available
                previous_analyzed_articles[article_id] = {
                    "sentiment": current_sentiment,
                    "analysis": article_full,
                }

        # Ensure the article entry exists and has the required keys
        print('Generating news TTS..')
        if article_id in previous_analyzed_articles and "analysis" in previous_analyzed_articles[article_id]:
            message = f"{article_title} {previous_analyzed_articles[article_id]['analysis']}"
            tts = gTTS(text=message, lang='en')
            clip_path = f"tts_clips/{article_id.replace('/', '_')}.mp3"
            tts.save(clip_path)

            print('Generating news visuals..')
            # Generate visuals for the TTS clip
            video_path = f"tts_clips/{article_id.replace('/', '_')}.mp4"
            generate_visuals_with_audio(message, video_path)
            looping_tts_clips.append(video_path)

    # Add musac clips to the looping TTS queue
#    for i in range(len(looping_tts_clips)):
#        if i % 15 == 0:  # Insert musac clip every 15 clips
#            looping_tts_clips.insert(i, random.choice(musac_clips))

class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global looping_tts_clips
        if looping_tts_clips:
            clip_path = looping_tts_clips.pop(0)
            looping_tts_clips.append(clip_path)  # Add the clip back to the end of the queue for infinite loop
            self.send_response(200)
            self.send_header("Content-type", "video/mp4")
            self.end_headers()
            with open(clip_path, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_response(204)  # No Content
            self.end_headers()

def start_tts_server():
    server_address = ('', 8000)  # Serve on all network interfaces, port 8000
    httpd = HTTPServer(server_address, TTSHandler)
    httpd.serve_forever()

def main():
    """
    Main function to run the news sentiment aggregator and TTS server.
    """
    load_analyzed_articles()

    # Ensure the tts_clips directory exists
    os.makedirs("tts_clips", exist_ok=True)

    tts_server_thread = threading.Thread(target=start_tts_server)
    tts_server_thread.daemon = True
    tts_server_thread.start()

    pre_generate_tts_clips()  # Pre-generate TTS clips and populate the looping queue

    while True:
        time.sleep(900)  # 15 minutes

if __name__ == "__main__":
    main()
