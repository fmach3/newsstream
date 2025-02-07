# News Sentiment Aggregator with TTS

This project fetches cryptocurrency-related news articles, analyzes their sentiment, and generates a Text-to-Speech (TTS) summary. It also fetches cryptocurrency metrics and generates visual content with embedded audio.

## Features

- Fetches news articles related to cryptocurrency, technology, and business.
- Analyzes the sentiment of the articles using TextBlob.
- Fetches cryptocurrency metrics from CoinGecko.
- Generates TTS summaries of the news articles and cryptocurrency metrics.
- Generates video content with embedded audio and subtitles using FFmpeg.
- Serves the generated TTS clips via an HTTP server.

## Prerequisites

- Python 3.7+
- FFmpeg
- NewsAPI key
- CoinGecko API (no key required)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/news-sentiment-tts.git
   cd news-sentiment-tts

This bot collects API crypto and news sources and passes the news articles to local LLM (ie LLAMA.CPP)and then generates TTS sound, and adds video with visuals, using FFmpeg in Python.

The resulting queue is served on port 8000 and can be played with VLC and streamed or recorded. Put VLN on "1 LOOP" to repeatedly reload the stream while it queues content, or give it time to queue up a few articles.

Created by Frank Machnick to generate a custom news stream to monitor crypto prices and random news categories on my whim. 

As this software does a lot of analysis and conversion, it's very process intensive.

The LLM can be accelerated with CUDA supported video cards (RTX series for example but not openCL) or can run on the CPU. You can also specify an LLM on another IP or use chatGPT, deepseek or similar.


Optional: LLM


Install:

Install the required Python packages: pip install -r requirements.txt

Set up your NewsAPI key: Replace NEWS_API_KEY in newsstream.py with your actual NewsAPI key and confirm other settings.

Ensure FFmpeg is installed on your system:

On Ubuntu:

sudo apt-get install ffmpeg
On macOS:

brew install ffmpeg

Usage:
sudo python3 newsstream.py

(Then access in browser with http://YOUR_IP_ADDRESS:8000)


news-sentiment-tts/
├── README.md
├── requirements.txt
├── newsstream.py
├── tts_clips/
├── analyzed_articles.json
├── musac_clips/
│   ├── musac1.mp4
│   ├── musac2.mp4
│   ├── musac3.mp4
├── .gitignore
