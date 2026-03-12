#!/usr/bin/env python3
"""
AI Daily Report Generator
自动生成 AI、科技、加密货币日报
"""

import os
import sys
import json
import hashlib
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
import markdown
from jinja2 import Template

# 配置
OUTPUT_DIR = "_posts"
ASSETS_DIR = "assets/images"
DATE_FORMAT = "%Y-%m-%d"
POST_DATE_FORMAT = "%Y-%m-%d %H:%M:%S +0800"

# 数据源配置
FEEDS = {
    "ai": [
        ("Hacker News", "https://news.ycombinator.com/rss", None),
        ("MIT Tech Review", "https://www.technologyreview.com/feed/", None),
        ("OpenAI Blog", "https://openai.com/blog/rss.xml", None),
    ],
    "tech": [
        ("36kr", "https://36kr.com/feed", None),
        ("TechCrunch", "https://techcrunch.com/feed/", None),
        ("The Verge", "https://www.theverge.com/rss/index.xml", None),
    ],
    "crypto": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", None),
        ("CoinTelegraph", "https://cointelegraph.com/rss", None),
        ("Decrypt", "https://decrypt.co/feed", None),
    ]
}

# 关键词过滤
KEYWORDS = {
    "ai": ["AI", "人工智能", "GPT", "LLM", "大模型", "OpenAI", "Claude", "机器学习", "深度学习"],
    "tech": ["科技", "互联网", "软件", "硬件", "芯片", "5G", "云计算"],
    "crypto": ["比特币", "以太坊", "区块链", "DeFi", "NFT", "加密", "Bitcoin", "Ethereum"]
}


def slugify(text):
    """生成 URL 友好的 slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text[:50]


def fetch_feed(url, parser=None):
    """获取 RSS 订阅"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = response.apparent_encoding
        
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            return feed
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None


def classify_content(title, summary):
    """根据内容分类到对应领域"""
    text = f"{title} {summary}".lower()
    
    scores = {}
    for category, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        scores[category] = score
    
    # 返回得分最高的分类
    max_category = max(scores, key=scores.get)
    return max_category if scores[max_category] > 0 else "general"


def generate_summary(text, max_length=150):
    """生成摘要"""
    if not text:
        return ""
    
    # 简单摘要：取前 N 个字符
    text = text.strip().replace('\n', ' ')
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def get_image_url(entry):
    """从 RSS 条目中提取图片 URL"""
    # 尝试各种方式获取图片
    if 'media_thumbnail' in entry:
        return entry['media_thumbnail'][0].get('url', '')
    if 'media_content' in entry:
        return entry['media_content'][0].get('url', '')
    
    # 从 summary 中提取图片
    if 'summary' in entry:
        soup = BeautifulSoup(entry['summary'], 'html.parser')
        img = soup.find('img')
        if img:
            return img.get('src', '')
    
    return None


def collect_news():
    """收集所有新闻"""
    all_news = {
        "ai": [],
        "tech": [],
        "crypto": [],
        "general": []
    }
    
    seen_urls = set()
    
    for category, feeds in FEEDS.items():
        for source_name, url, parser in feeds:
            print(f"Fetching: {source_name}")
            feed = fetch_feed(url, parser)
            
            if not feed or not feed.entries:
                print(f"  No entries found")
                continue
            
            print(f"  Found {len(feed.entries)} entries")
            
            for entry in feed.entries[:10]:  # 每个源取前10条
                url = entry.get('link', '')
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = entry.get('title', 'No title')
                summary = entry.get('summary', '')
                published = entry.get('published', '')
                
                # 生成摘要
                summary_text = summary if len(summary) > 50 else generate_summary(entry.get('description', ''), 200)
                
                # 分类
                news_category = classify_content(title, summary_text)
                if news_category == "general":
                    news_category = category if category != "general" else "general"
                
                # 获取图片
                image_url = get_image_url(entry)
                
                news_item = {
                    "title": title,
                    "url": url,
                    "summary": summary_text,
                    "source": source_name,
                    "date": published,
                    "category": news_category,
                    "image": image_url
                }
                
                all_news[news_category].append(news_item)
                
    return all_news


def generate_markdown_content(date_str, news_data):
    """生成 Markdown 内容"""
    
    md_content = f"""---
title: "AI Daily Report - {date_str}"
date: {date_str}
layout: post
---

# AI Daily Report - {date_str}

"""
    
    # AI 板块
    if news_data["ai"]:
        md_content += "## 🤖 AI 资讯\n\n"
        for item in news_data["ai"][:10]:
            image_md = f'![{item["title"]}]({item["image"]})' if item["image"] else ''
            md_content += f"""### {item['title']}

> 来源：{item['source']} | 分类：AI

{item['summary'][:200]}...

{image_md}

[阅读原文]({item['url']})

---

"""
    
    # 科技板块
    if news_data["tech"]:
        md_content += "## 💻 科技资讯\n\n"
        for item in news_data["tech"][:10]:
            image_md = f'![{item["title"]}]({item["image"]})' if item["image"] else ''
            md_content += f"""### {item['title']}

> 来源：{item['source']} | 分类：科技

{item['summary'][:200]}...

{image_md}

[阅读原文]({item['url']})

---

"""
    
    # 加密板块
    if news_data["crypto"]:
        md_content += "## ₿ 加密货币\n\n"
        for item in news_data["crypto"][:10]:
            image_md = f'![{item["title"]}]({item["image"]})' if item["image"] else ''
            md_content += f"""### {item['title']}

> 来源：{item['source']} | 分类：加密货币

{item['summary'][:200]}...

{image_md}

[阅读原文]({item['url']})

---

"""
    
    md_content += f"""
---

*本日报由 AI 自动生成，更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return md_content


def save_daily_report():
    """保存日报"""
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    
    print(f"正在收集 {date_str} 的新闻...")
    
    # 收集新闻
    news_data = collect_news()
    
    total_news = sum(len(v) for v in news_data.values())
    print(f"共收集到 {total_news} 条新闻")
    print(f"  AI: {len(news_data['ai'])} 条")
    print(f"  科技: {len(news_data['tech'])} 条")
    print(f"  加密货币: {len(news_data['crypto'])} 条")
    
    # 生成 Markdown
    md_content = generate_markdown_content(date_str, news_data)
    
    # 保存文件
    filename = f"_posts/{today.strftime('%Y-%m-%d')}-daily-report.md"
    
    # 确保目录存在
    os.makedirs('_posts', exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"日报已保存到: {filename}")
    return filename


if __name__ == '__main__':
    try:
        save_daily_report()
        print("日报生成成功！")
    except Exception as e:
        print(f"生成日报时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)