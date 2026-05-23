#!/usr/bin/env python3
"""Collect candidate market-moving financial news and write a structured TXT brief."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


TOPIC_QUERIES = {
    "us-stocks": [
        "U.S. stock market earnings Federal Reserve Nasdaq S&P 500",
        "US equities market moving news earnings guidance regulation",
    ],
    "china-markets": [
        "China markets A shares Hong Kong stocks policy yuan property consumption",
        "China economy listed companies market regulation Hong Kong ADR",
    ],
    "macro-policy": [
        "Federal Reserve inflation jobs Treasury yields dollar market impact",
        "central bank rates inflation bond yields stocks currency",
    ],
    "policy-regulation": [
        "financial regulation SEC antitrust trade policy market impact",
        "banking regulation capital markets enforcement listed companies",
    ],
    "global-markets": [
        "global markets stocks bonds commodities currencies geopolitical risk",
        "Europe Asia markets central banks commodities currencies",
    ],
    "commodities": [
        "oil gold copper commodities supply demand market impact",
        "energy metals agriculture commodity prices market impact",
    ],
    "ai": [
        "AI stocks artificial intelligence capex cloud chips software market impact",
        "artificial intelligence earnings investment data centers power demand",
    ],
    "healthcare": [
        "healthcare stocks FDA drug approval biotech pharma market impact",
        "pharmaceutical biotech medical device regulation earnings",
    ],
    "energy": [
        "energy stocks oil gas power utilities renewable market impact",
        "electricity grid natural gas crude oil energy policy",
    ],
    "banks": [
        "bank stocks lending credit deposits regulation market impact",
        "financials banks insurance brokers earnings capital requirements",
    ],
    "real-estate": [
        "real estate property developers mortgage REIT housing market impact",
        "China property US housing commercial real estate credit risk",
    ],
    "chips": [
        "semiconductor stocks chip equipment foundry memory export controls",
        "AI chips semiconductor supply chain market impact",
    ],
    "consumer": [
        "consumer stocks retail travel food inflation earnings market impact",
        "consumer discretionary staples spending confidence listed companies",
    ],
    "new-energy": [
        "new energy EV battery solar wind policy supply chain market impact",
        "electric vehicles batteries renewable energy stocks earnings",
    ],
    "internet": [
        "internet platform stocks e-commerce advertising cloud regulation earnings",
        "technology internet companies market impact antitrust AI",
    ],
    "insurance": [
        "insurance stocks premiums claims investment income regulation market impact",
        "life insurance property casualty insurers yields catastrophe risk",
    ],
    "brokers": [
        "brokerage securities firms trading volume IPO market regulation",
        "investment banks brokers exchanges capital markets activity",
    ],
    "defense": [
        "defense stocks military spending geopolitics aerospace market impact",
        "defense contractors orders budget sanctions supply chain",
    ],
}

BASE_FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.sec.gov/news/pressreleases.rss",
]

KEYWORDS = {
    "federal reserve": 7,
    "fed": 5,
    "rate": 5,
    "inflation": 5,
    "jobs": 4,
    "treasury": 4,
    "yield": 4,
    "dollar": 4,
    "earnings": 4,
    "guidance": 5,
    "revenue": 3,
    "profit": 3,
    "sec": 4,
    "regulation": 4,
    "export control": 6,
    "sanction": 5,
    "tariff": 5,
    "semiconductor": 5,
    "chip": 4,
    "ai": 4,
    "bank": 4,
    "credit": 4,
    "default": 6,
    "liquidity": 5,
    "oil": 4,
    "gold": 3,
    "china": 3,
    "property": 4,
    "ipo": 3,
    "merger": 4,
    "investigation": 4,
}

SOURCE_WEIGHTS = {
    "federalreserve.gov": 4,
    "FRB": 4,
    "sec.gov": 4,
    "SEC": 4,
    "Reuters": 3,
    "Bloomberg": 3,
    "Wall Street Journal": 3,
    "Financial Times": 3,
    "CNBC": 2,
    "US Top News and Analysis": 2,
    "Yahoo": 1,
    "Caixin": 2,
    "Yicai": 2,
    "The Sunday Guardian": -4,
}

DEFAULT_TOPICS = ["us-stocks", "macro-policy", "china-markets", "global-markets", "policy-regulation"]

CATEGORY_RULES = [
    ("宏观与利率 / Macro & Rates", ["fed", "federal reserve", "central bank", "inflation", "jobs", "treasury", "yield", "rate", "dollar", "currency", "bond"]),
    ("美股与全球市场 / U.S. Stocks & Global Markets", ["s&p", "nasdaq", "dow", "u.s. stock", "us stock", "wall street", "earnings", "guidance", "mega-cap", "global market"]),
    ("中国市场 / China Markets", ["china", "chinese", "hong kong", "a-share", "adr", "yuan", "renminbi", "property developer"]),
    ("政策与监管 / Policy & Regulation", ["sec", "regulation", "regulatory", "enforcement", "antitrust", "tariff", "sanction", "export control", "law", "policy"]),
]

FOCUS_INDUSTRY_RULES = {
    "AI": ["ai", "artificial intelligence", "cloud", "data center", "gpu", "software"],
    "医药 / Healthcare": ["healthcare", "fda", "drug", "biotech", "pharma", "medical"],
    "能源 / Energy": ["energy", "oil", "gas", "power", "utility", "electricity"],
    "银行与金融 / Banks & Financials": ["bank", "lending", "deposit", "credit", "insurance", "broker"],
    "地产 / Real Estate": ["property", "real estate", "housing", "mortgage", "reit"],
    "芯片 / Semiconductors": ["semiconductor", "chip", "foundry", "memory", "wafer"],
    "消费 / Consumer": ["consumer", "retail", "travel", "food", "spending"],
    "新能源 / New Energy": ["ev", "battery", "solar", "wind", "renewable"],
    "互联网 / Internet": ["internet", "e-commerce", "advertising", "platform", "cloud"],
    "军工 / Defense": ["defense", "military", "aerospace", "contractor"],
    "商品 / Commodities": ["commodity", "commodities", "gold", "copper", "oil", "agriculture"],
}


@dataclass
class Item:
    title: str
    link: str
    source: str
    published: datetime | None
    summary: str
    score: int


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 financial-news-skill/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def text_of(parent: ET.Element, tag: str) -> str:
    node = parent.find(tag)
    if node is None or node.text is None:
        return ""
    return html.unescape(re.sub(r"\s+", " ", node.text)).strip()


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def score_item(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    score = 0
    for keyword, weight in KEYWORDS.items():
        if keyword_in_text(keyword, text):
            score += weight
    if any(term in text for term in ("breaking", "exclusive", "urgent")):
        score += 3
    return score


def source_score(source: str, link: str) -> int:
    haystack = f"{source} {link}"
    score = 0
    for needle, weight in SOURCE_WEIGHTS.items():
        if needle.lower() in haystack.lower():
            score += weight
    return score


def parse_rss(xml_bytes: bytes, feed_url: str) -> list[Item]:
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    channel_title = text_of(channel if channel is not None else root, "title")
    items: list[Item] = []
    for node in root.findall(".//item"):
        title = text_of(node, "title")
        link = text_of(node, "link")
        summary = strip_html(text_of(node, "description"))
        source = text_of(node, "source") or channel_title or urllib.parse.urlparse(feed_url).netloc
        published = parse_date(text_of(node, "pubDate"))
        if not title or not link:
            continue
        score = score_item(title, summary) + source_score(source, link)
        items.append(Item(title, link, source, published, summary, score))
    return items


def google_news_feed(query: str, language: str) -> str:
    if language == "zh":
        params = {"q": query, "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"}
    else:
        params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def collect_feeds(topics: list[str], query: str | None, language: str, include_base_feeds: bool) -> tuple[list[str], list[str]]:
    feeds = list(BASE_FEEDS) if include_base_feeds else []
    queries: list[str] = []
    for topic in topics:
        queries.extend(TOPIC_QUERIES.get(topic, [topic]))
    if query:
        queries.append(query)
    search_languages = ["en", "zh"] if language in {"zh", "bilingual"} else ["en"]
    for q in queries:
        for search_language in search_languages:
            feeds.append(google_news_feed(q, search_language))
    return feeds, queries


def normalize_key(item: Item) -> str:
    title = re.sub(r"[^a-z0-9\u3400-\u9fff]+", " ", item.title.lower())
    return " ".join(title.split()[:12])


def collect_items(feeds: list[str], hours: int, min_score: int) -> tuple[list[Item], list[str]]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    by_key: dict[str, Item] = {}
    errors: list[str] = []
    for feed in feeds:
        try:
            parsed = parse_rss(fetch_url(feed), feed)
        except Exception as exc:
            errors.append(f"{feed} ({exc})")
            continue
        for item in parsed:
            if item.published and item.published < cutoff:
                continue
            if item.score < min_score:
                continue
            key = normalize_key(item)
            current = by_key.get(key)
            if current is None or item.score > current.score:
                by_key[key] = item
    return sorted(by_key.values(), key=lambda item: (item.score, item.published or datetime.min.replace(tzinfo=timezone.utc)), reverse=True), errors


def contains_cjk(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


def translate_to_zh(value: str, cache: dict[str, str]) -> str:
    value = value.strip()
    if not value:
        return ""
    if contains_cjk(value):
        return value
    if value in cache:
        return cache[value]
    params = urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": value})
    url = "https://translate.googleapis.com/translate_a/single?" + params
    try:
        data = json.loads(fetch_url(url, timeout=15).decode("utf-8"))
        translated = "".join(part[0] for part in data[0] if part and part[0]).strip()
    except Exception:
        translated = ""
    cache[value] = translated or "[候选翻译不可用，最终简报需人工补充]"
    return cache[value]


def impact_label(score: int) -> str:
    if score >= 12:
        return "高 / High"
    if score >= 7:
        return "中 / Medium"
    return "低 / Low"


def format_time(dt: datetime | None) -> str:
    if dt is None:
        return "Unknown"
    return dt.astimezone().strftime("%Y-%m-%d %H:%M %Z")


def shorten(value: str, width: int = 240) -> str:
    return textwrap.shorten(value, width=width, placeholder="...") if value else ""


def item_text(item: Item) -> str:
    return f"{item.title} {item.summary}".lower()


def keyword_in_text(keyword: str, text: str) -> bool:
    if len(keyword) <= 3 and keyword.isascii() and keyword.isalnum():
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text))
    return keyword in text


def choose_category(item: Item) -> str:
    text = item_text(item)
    for category, keywords in CATEGORY_RULES:
        if any(keyword_in_text(keyword, text) for keyword in keywords):
            return category
    return "美股与全球市场 / U.S. Stocks & Global Markets"


def choose_focus_industry(item: Item) -> str | None:
    text = item_text(item)
    for industry, keywords in FOCUS_INDUSTRY_RULES.items():
        if any(keyword_in_text(keyword, text) for keyword in keywords):
            return industry
    return None


def related_assets(item: Item) -> str:
    text = item_text(item)
    assets: list[str] = []
    checks = [
        ("美债 / Treasury yields", ["treasury", "yield", "bond"]),
        ("美元 / U.S. dollar", ["dollar", "currency", "fx"]),
        ("美股指数 / U.S. equity indexes", ["s&p", "nasdaq", "dow", "stock market"]),
        ("A股/港股/中概股 / China equities", ["china", "hong kong", "a-share", "adr", "yuan"]),
        ("银行与信用 / Banks and credit", ["bank", "credit", "deposit", "loan"]),
        ("能源与商品 / Energy and commodities", ["oil", "gas", "gold", "copper", "commodity"]),
        ("科技与成长股 / Technology and growth stocks", ["ai", "chip", "semiconductor", "cloud", "software"]),
        ("地产链 / Real estate chain", ["property", "real estate", "housing", "mortgage"]),
    ]
    for label, keywords in checks:
        if any(keyword_in_text(keyword, text) for keyword in keywords):
            assets.append(label)
    return "；".join(assets) if assets else "待最终简报核实 / To verify"


def zh_title(item: Item, cache: dict[str, str], translate: bool) -> str:
    if not translate:
        return "【候选中文标题待润色】"
    return translate_to_zh(item.title, cache)


def zh_summary(item: Item, cache: dict[str, str], translate: bool) -> str:
    summary = shorten(item.summary) or item.title
    if not translate:
        return "候选摘要待最终简报补充。"
    return translate_to_zh(summary, cache)


def write_separator(lines: list[str], title: str) -> None:
    lines.extend(["", "=" * 60, title, "=" * 60, ""])


def write_top_item(lines: list[str], index: int, item: Item, cache: dict[str, str], translate: bool) -> None:
    lines.extend(
        [
            f"{index}. 【{zh_title(item, cache, translate)}】",
            f"   English: {item.title}",
            "",
            "   核心事实：",
            f"   - {zh_summary(item, cache, translate)}",
            "",
            "   为什么重要：",
            f"   - 候选判断：影响等级 {impact_label(item.score)}，需结合来源核验其对流动性、盈利、估值或政策预期的影响。",
            "",
            "   影响方向：",
            "   - 风险偏好：待最终简报判断",
            f"   - 相关行业：{choose_focus_industry(item) or '待最终简报判断'}",
            f"   - 相关资产/标的：{related_assets(item)}",
            "",
            "   来源：",
            f"   - Source: {item.source}",
            f"   - Link: {item.link}",
            "",
            "-" * 60,
            "",
        ]
    )


def write_category_item(lines: list[str], index: int, item: Item, cache: dict[str, str], translate: bool) -> None:
    lines.extend(
        [
            f"{index}. 【{zh_title(item, cache, translate)}】",
            f"   English: {item.title}",
            f"   摘要：{zh_summary(item, cache, translate)}",
            f"   影响：候选影响等级 {impact_label(item.score)}，最终简报需补充研究判断。",
            f"   相关资产：{related_assets(item)}",
            f"   来源：{item.source} | {item.link}",
            "",
        ]
    )


def group_items(items: list[Item]) -> tuple[dict[str, list[Item]], dict[str, list[Item]]]:
    categories: dict[str, list[Item]] = {}
    industries: dict[str, list[Item]] = {}
    for item in items:
        categories.setdefault(choose_category(item), []).append(item)
        industry = choose_focus_industry(item)
        if industry:
            industries.setdefault(industry, []).append(item)
    return categories, industries


def write_report(
    items: list[Item],
    errors: list[str],
    output: Path,
    scope: str,
    focus_themes: str,
    limit: int,
    translate: bool,
) -> None:
    now = datetime.now().astimezone()
    date = now.strftime("%Y-%m-%d")
    generated = now.strftime("%H:%M %Z")
    cache: dict[str, str] = {}
    top_items = items[: min(3, len(items))]
    remaining = items[3:limit]
    categories, industries = group_items(remaining)

    lines: list[str] = [
        "每日金融新闻候选简报 / Daily Financial News Candidate Brief",
        f"日期 / Date: {date}",
        f"生成时间 / Generated: {generated}",
        f"覆盖范围 / Scope: {scope}",
        f"重点主题 / Focus Themes: {focus_themes}",
        "",
        "说明：本文件由脚本自动抓取、去重和初筛，供最终研究简报使用；中文为候选翻译/摘要，正式版本需人工核验和润色。",
    ]

    write_separator(lines, "一、今日最重要的 3 件事 / Top 3 Market Drivers")
    if top_items:
        for index, item in enumerate(top_items, start=1):
            write_top_item(lines, index, item, cache, translate)
    else:
        lines.append("暂无候选新闻。")

    write_separator(lines, "二、分领域重点新闻 / Key News by Category")
    base_categories = [
        "宏观与利率 / Macro & Rates",
        "美股与全球市场 / U.S. Stocks & Global Markets",
        "中国市场 / China Markets",
        "政策与监管 / Policy & Regulation",
    ]
    for category in base_categories:
        lines.append(f"【{category}】")
        category_items = categories.get(category, [])[:3]
        if category_items:
            for index, item in enumerate(category_items, start=1):
                write_category_item(lines, index, item, cache, translate)
        else:
            lines.extend(["暂无高相关候选新闻。", ""])

    lines.append("【重点行业 / Focus Industries】")
    if industries:
        for industry, industry_items in list(industries.items())[:6]:
            lines.append(f"行业：{industry}")
            for index, item in enumerate(industry_items[:2], start=1):
                write_category_item(lines, index, item, cache, translate)
    else:
        lines.extend(["行业：按当天新闻重要性自动判断", "暂无明确行业候选新闻。", ""])

    write_separator(lines, "三、市场影响总结 / Market Implications")
    lines.extend(
        [
            "1. 对风险偏好的影响：由最终简报根据 Top 3 新闻核验后判断。",
            "2. 对利率、美元、美债的影响：重点检查宏观与利率类新闻。",
            "3. 对股票市场的影响：重点检查盈利、监管、流动性和大型公司新闻。",
            "4. 对中国资产的影响：重点检查政策、人民币、港股/A股/中概股、地产和消费线索。",
            "5. 对重点行业的影响：根据用户主题或自动识别行业补充产业链影响。",
        ]
    )

    write_separator(lines, "四、后续关注 / Watchlist")
    lines.extend(
        [
            "1. 事件：Top 3 新闻的一手来源或后续官方回应",
            "   时间：未来 24-72 小时",
            "   为什么重要：确认新闻是否改变市场预期。",
            "   需要观察的数据/信号：价格反应、官方文件、公司公告、经济数据、分析师修正。",
            "",
            "2. 事件：重点行业相关政策、业绩、订单或监管进展",
            "   时间：按新闻事件后续日程确认",
            "   为什么重要：决定影响是短期情绪还是中期基本面变化。",
            "   需要观察的数据/信号：盈利指引、资本开支、供需变化、政策落地细则。",
        ]
    )

    write_separator(lines, "五、来源说明 / Source Notes")
    if errors:
        lines.append("部分来源抓取失败 / Some feeds could not be fetched:")
        lines.extend(f"- {error}" for error in errors[:10])
    else:
        lines.append("- 所有配置来源均已成功抓取。")
    lines.extend(
        [
            "- 优先使用官方公告、监管文件、公司公告、Reuters、Bloomberg、WSJ、FT、CNBC、财新、一财等来源。",
            "- 对社交媒体、市场传闻、转载内容，应标注“未确认”或不纳入最终正文。",
            "- 英文标题保留原文，中文摘要和影响判断应在最终简报中重新整理。",
            "- 本简报仅用于信息整理，不构成投资建议。",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect candidate financial news and write a structured TXT brief.")
    parser.add_argument(
        "--topics",
        nargs="*",
        default=None,
        help=f"Topic keys or free-form topics. Known: {', '.join(TOPIC_QUERIES)}",
    )
    parser.add_argument("--query", help="Additional free-form search query.")
    parser.add_argument("--hours", type=int, default=72, help="Keep items published within this many hours when dates are available.")
    parser.add_argument("--limit", type=int, default=15, help="Maximum candidate items used in the report.")
    parser.add_argument("--min-score", type=int, default=3, help="Minimum keyword impact score.")
    parser.add_argument("--language", choices=["en", "zh", "bilingual"], default="bilingual", help="Search language mode.")
    parser.add_argument("--no-translate", action="store_true", help="Skip candidate machine translation for Chinese fields.")
    parser.add_argument("--output", required=True, help="Output TXT path.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    topics = args.topics
    if topics is None:
        topics = [] if args.query else DEFAULT_TOPICS
    include_base_feeds = bool(topics) or not args.query
    feeds, queries = collect_feeds(topics, args.query, args.language, include_base_feeds)
    items, errors = collect_items(feeds, args.hours, args.min_score)
    if not items and args.query and not topics:
        items, retry_errors = collect_items(feeds, 24 * 14, 0)
        errors.extend(retry_errors)
    scope = "美国市场、中国市场、全球宏观、重点行业"
    focus_parts = list(topics)
    if args.query:
        focus_parts.append(args.query)
    focus_themes = "；".join(focus_parts) if focus_parts else "按市场影响力自动筛选"
    write_report(items, errors, Path(args.output), scope, focus_themes, args.limit, not args.no_translate)
    print(f"Wrote {min(len(items), args.limit)} candidate items to {args.output}")
    print(f"Used {len(queries)} search query group(s) and {len(feeds)} feed URL(s).")
    if errors:
        print(f"Warning: {len(errors)} feed(s) failed; see Source Notes in the report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
