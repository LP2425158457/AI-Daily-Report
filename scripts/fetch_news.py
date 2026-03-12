#!/usr/bin/env python3
"""
AI Daily News Fetcher
动态抓取新闻并保存为 JSON，供前端调用
"""

import os
import json
import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

# 配置
OUTPUT_FILE = "data/news.json"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 数据源配置
FEEDS = [
    # AI
    ("Hacker News", "https://news.ycombinator.com/rss"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
    # 科技
    ("36kr", "https://36kr.com/feed"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    # 加密
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
]

# 分类关键词
CATEGORY_KEYWORDS = {
    "ai": ["AI", "人工智能", "GPT", "LLM", "大模型", "OpenAI", "Claude", "机器学习", "深度学习", "Neural", "Transformer"],
    "tech": ["科技", "互联网", "软件", "硬件", "芯片", "5G", "云计算", "Tech", "Startup"],
    "crypto": ["比特币", "以太坊", "区块链", "DeFi", "NFT", "加密", "Bitcoin", "Ethereum", "Crypto", "Web3"]
}

# 图片映射（根据来源域名）
IMAGE_FALLBACK = {
    "news.ycombinator.com": "https://news.ycombinator.com/favicon.ico",
    "technologyreview.com": "https://www.technologyreview.com/wp-content/uploads/2023/10/GettyImages-1458322671-e1698973217743.jpg?resize=750,563",
    "openai.com": "https://upload.wikimedia.org/wikipedia/commons/4/4d/OpenAI_Logo.svg",
    "36kr.com": "https://cdn.36kr.com/static/web/pwa/assets/logo.svg",
    "techcrunch.com": "https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png",
    "coindesk.com": "https://www.coindesk.com/img/resize/1200x600/wp-content/uploads/2023/04/coindesk-logo-e1682474040522.jpg",
    "cointelegraph.com": "https://cointelegraph.com/images/840x420/4aDFIa3ILS6J9jqhRYSgqYbXz_M=/0x400:3000x1900/filters:quality(70)/https://cointelegraph.com/assets/img/meta/cointelegraph-logo-OG.png",
}


def fetch_feed(url):
    """获取 RSS 订阅"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        
        if response.status_code == 200:
            return feedparser.parse(response.text)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


def classify_content(title, summary):
    """分类内容"""
    text = f"{title} {summary}".lower()
    
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        scores[category] = score
    
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "general"


def get_image_url(entry, source_url):
    """获取图片 URL"""
    # 尝试从 media 获取
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    
    # 从 summary 提取
    if hasattr(entry, 'summary'):
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img.get('src')
    
    # 使用域名对应的默认图
    domain = urlparse(source_url).netloc
    for key, img in IMAGE_FALLBACK.items():
        if key in domain:
            return img
    
    return ""


def fetch_all_news():
    """抓取所有新闻"""
    all_news = []
    seen_hashes = set()
    
    for source_name, url in FEEDS:
        print(f"Fetching: {source_name}")
        feed = fetch_feed(url)
        
        if not feed or not feed.entries:
            print(f"  No entries")
            continue
        
        for entry in feed.entries[:15]:
            url = entry.get('link', '')
            title = entry.get('title', 'No title')
            summary = entry.get('summary', '')[:300]
            
            # 去重
            content_hash = hashlib.md5(f"{title}{url}".encode()).hexdigest()
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
            
            # 分类
            category = classify_content(title, summary)
            
            # 图片
            image = get_image_url(entry, url)
            
            # 来源域名
            domain = urlparse(url).netloc.replace('www.', '')
            
            news_item = {
                "id": content_hash[:12],
                "title": title.strip(),
                "summary": summary.strip() if summary else "",
                "url": url,
                "source": source_name,
                "domain": domain,
                "category": category,
                "image": image,
                "published": entry.get('published', '')
            }
            
            all_news.append(news_item)
    
    return all_news


def save_news():
    """保存新闻到 JSON"""
    print("="*50)
    print(f"Fetching news at {datetime.now().strftime(DATE_FORMAT)}")
    print("="*50)
    
    news = fetch_all_news()
    
    # 按分类分组
    categorized = {"ai": [], "tech": [], "crypto": [], "general": []}
    for item in news:
        categorized[item["category"]].append(item)
    
    data = {
        "last_updated": datetime.now().isoformat(),
        "total": len(news),
        "news": news,
        "categories": {
            "ai": categorized["ai"],
            "tech": categorized["tech"],
            "crypto": categorized["crypto"],
            "general": categorized["general"]
        }
    }
    
    # 保存
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal: {len(news)} news")
    print(f"  AI: {len(categorized['ai'])}")
    print(f"  Tech: {len(categorized['tech'])}")
    print(f"  Crypto: {len(categorized['crypto'])}")
    print(f"\nSaved to: {OUTPUT_FILE}")
    
    return len(news)


if __name__ == "__main__":
    try:
        save_news()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)