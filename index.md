---
layout: default
title: AI Daily Report
---

# 🤖 AI Daily Report

每日自动更新的 AI、科技、加密货币资讯日报。

## 📰 最新日报

<ul class="post-list">
{% for post in site.posts limit:10 %}
  <li class="post-list-item">
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
    <p class="post-meta">📅 {{ post.date | date: "%Y年%m月%d日" }}</p>
    <p class="post-excerpt">{{ post.excerpt | strip_html | truncate: 150 }}</p>
  </li>
{% endfor %}
</ul>

---

## 📊 关于

- 🤖 自动采集 AI/科技/加密货币领域最新资讯
- ⏰ 每日 8:00（北京时间）自动更新
- 🔄 基于 GitHub Pages + Jekyll
- 📡 [RSS 订阅](/feed.xml)

## 🔧 技术

本项目使用 GitHub Actions 自动执行以下流程：

1. 定时触发（每天 UTC 0 点）
2. 采集 RSS 订阅源
3. 提取文章标题、摘要、图片
4. 生成静态网页并发布

## ☁️ 部署

Hosted on **GitHub Pages** - 免费静态网站托管。