---
name: collect-financial-news
description: Collect, rank, verify, and write investor-oriented daily financial news briefs as TXT files. Use when the user asks for market-moving news, daily finance digests, investment research news, U.S. stocks, China markets, macro rates, regulation, geopolitics, commodities, currencies, bonds, listed companies, or any dynamic industry theme such as AI, healthcare, energy, banks, real estate, chips, consumer, new energy, internet, insurance, brokers, or defense.
---

# Collect Financial News

## Overview

Create a daily financial news brief for investment research readers. Write the final TXT in Chinese as the main reading language, keep English original headlines or source text for verification, and focus on market impact rather than raw news volume.

## Workflow

1. Treat the user's requested industries as dynamic focus themes. Do not hard-code chips or any other sector as the default; chips are only one possible example.
2. Gather current news with web search and/or `scripts/collect_news.py`. Always verify time-sensitive news with recent sources.
3. Use `scripts/collect_news.py` only as a candidate collector and first-pass sorter. Do not present the script's machine translation or rough candidate notes as the final research brief without review.
4. Verify and improve the most important items with primary or reputable sources: regulators, central banks, company filings, exchanges, Reuters, Bloomberg, WSJ, FT, CNBC, Caixin, Yicai, Securities Times, CSRC, SSE, SZSE, HKEX, and official ministry releases.
5. Rank by market impact: liquidity, rates, earnings, valuation, policy permission, supply chain, demand, margins, risk appetite, and affected assets.
6. Write a concise TXT report using the required format below. Use Chinese for analysis and English for original headlines/source checks.
7. Separate confirmed facts from inference. Label rumors or weakly sourced items as unconfirmed or exclude them.

## Quick Script

Use the script for candidate collection:

```bash
python scripts/collect_news.py --output financial_news_candidates.txt
```

Useful examples:

```bash
python scripts/collect_news.py --topics us-stocks macro-policy --output daily_candidates.txt
python scripts/collect_news.py --query "healthcare stocks FDA regulation" --output healthcare_candidates.txt
python scripts/collect_news.py --query "AI energy banks China real estate" --output multi_theme_candidates.txt
```

After running it, review the candidate TXT, verify high-impact items, and rewrite the final TXT in polished financial Chinese.

## Required TXT Format

Use this structure unless the user gives a different template:

```text
每日金融新闻简报 / Daily Financial News Brief
日期 / Date: YYYY-MM-DD
生成时间 / Generated: HH:MM 时区
覆盖范围 / Scope: 美国市场、中国市场、全球宏观、重点行业
重点主题 / Focus Themes: 用户指定主题；如未指定，则按市场影响力自动筛选

============================================================
一、今日最重要的 3 件事 / Top 3 Market Drivers
============================================================

1. 【中文标题】
   English: [Original English Headline]

   核心事实：
   - ...

   为什么重要：
   - ...

   影响方向：
   - 风险偏好：
   - 相关行业：
   - 相关资产/标的：

   来源：
   - Source: ...
   - Link: ...

============================================================
二、分领域重点新闻 / Key News by Category
============================================================

【宏观与利率 / Macro & Rates】
1. 【中文标题】
   English: ...
   摘要：...
   影响：...
   相关资产：...
   来源：...

【美股与全球市场 / U.S. Stocks & Global Markets】
...

【中国市场 / China Markets】
...

【政策与监管 / Policy & Regulation】
...

【重点行业 / Focus Industries】
行业：动态行业名称
...

============================================================
三、市场影响总结 / Market Implications
============================================================

1. 对风险偏好的影响：
2. 对利率、美元、美债的影响：
3. 对股票市场的影响：
4. 对中国资产的影响：
5. 对重点行业的影响：

============================================================
四、后续关注 / Watchlist
============================================================

1. 事件：
   时间：
   为什么重要：
   需要观察的数据/信号：

============================================================
五、来源说明 / Source Notes
============================================================

- ...
- 本简报仅用于信息整理，不构成投资建议。
```

## Quality Rules

- Keep the final report compact: Top 3 plus a small number of categorized items.
- Prefer Chinese conclusions over literal translation. English is mainly for headline/source verification.
- For every important item, include what happened, why it matters, related assets, source, and link.
- Connect U.S. news to indexes, sectors, mega-cap stocks, rates, earnings, liquidity, or regulation where relevant.
- Connect China news to A-shares, Hong Kong stocks, ADRs, RMB, policy, real estate, consumption, exports, or industry chains where relevant.
- For industry news, name the affected value-chain nodes when possible: upstream, midstream, downstream, application, customers, suppliers, or capex.
- Use absolute dates and times when available.
