# 我的第一个 Codex Skill：金融新闻简报助手

这是我的第一个 GitHub 仓库，也是我的第一个 Codex skill。

这个仓库目前收录了一个名为 `collect-financial-news` 的 skill。它的目标是帮助我收集、筛选和整理对金融市场有影响的新闻，并输出适合投资研究者阅读的中文金融新闻简报。

## 这个 Skill 做什么

`collect-financial-news` 用来生成“每日金融新闻简报 / Daily Financial News Brief”。

它关注的不是简单的新闻列表，而是更接近研究工作流的金融信息整理：

- 收集可能影响市场的新闻
- 按市场影响力进行初步筛选
- 保留英文原始标题和来源，方便核验
- 用中文整理核心事实和影响判断
- 按宏观、美股、中国市场、政策监管、重点行业等分类
- 输出 TXT 格式的候选简报

重点行业不是固定的。芯片只是一个例子，这个 skill 也可以关注 AI、医药、能源、银行、地产、消费、新能源、互联网、保险、券商、商品、军工等主题。

## 目录结构

```text
collect-financial-news/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── impact-framework.md
└── scripts/
    └── collect_news.py
```

## 文件说明

- `SKILL.md`：定义 skill 的用途、工作流、输出格式和质量要求。
- `agents/openai.yaml`：Codex 中显示这个 skill 时使用的元信息。
- `references/impact-framework.md`：判断新闻是否具有市场影响力的参考框架。
- `scripts/collect_news.py`：抓取、去重、初筛新闻，并生成 TXT 候选简报的脚本。

## 使用示例

生成默认每日候选简报：

```bash
python collect-financial-news/scripts/collect_news.py --output financial_news_candidates.txt
```

关注美国股市和宏观政策：

```bash
python collect-financial-news/scripts/collect_news.py --topics us-stocks macro-policy --output daily_candidates.txt
```

关注自定义主题：

```bash
python collect-financial-news/scripts/collect_news.py --query "AI energy banks China real estate" --output multi_theme_candidates.txt
```

## 输出格式

脚本会生成一个 TXT 候选简报，主要包括：

1. 今日最重要的 3 件事 / Top 3 Market Drivers
2. 分领域重点新闻 / Key News by Category
3. 市场影响总结 / Market Implications
4. 后续关注 / Watchlist
5. 来源说明 / Source Notes

这个 TXT 是候选简报，不是最终投资报告。最终版本仍需要对重点新闻进行核验、重排、中文润色和研究化判断。

## 设计原则

- 中文为主，英文标题用于核验。
- 不做机械逐句翻译。
- 不追求新闻数量，优先关注市场影响。
- 明确区分事实和推断。
- 弱来源、传闻和转载内容需要标注或排除。
- 本项目仅用于信息整理，不构成投资建议。

## 小记

这是一个起点。第一个仓库、第一个 skill，也是一套属于自己的信息处理工作流。

后续可以继续改进新闻源、分类逻辑、摘要质量、自动化运行和最终简报生成方式。
