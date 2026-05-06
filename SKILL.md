---
name: markdown-poster
description: |
  将 Markdown 文章自动排版成小红书/社交媒体图文卡片。
  输入 Markdown 正文 → 自动分页 → 生成 HTML → Playwright 截图 → 输出 PNG/WebP。
  触发词：「排版成图文」「生成小红书卡片」「XHS card」「做图文」「markdown poster」。
---

> 你是 AI 助手。用户把 Markdown 文章给你，你的任务是用 markdown-poster 工具帮他们生成排版精美的图片卡片。

## 你的工作流

### Step 1: 收集信息

收到请求后，确认以下信息。用户没提供的就主动问：

| 必填 | 说明 | 从哪里获取 |
|------|------|-----------|
| 源文件 | Markdown 文章路径 | 用户提供 |
| 标题 | 卡片首页大标题 | Markdown H1，或让用户给 |
| 作者名 | 显示在作者区 | 问用户 |

| 可选 | 默认值 |
|------|--------|
| 日期 | 今天 |
| 头像 | 不传则无头像图 |
| 主题 | light |
| 格式 | png |
| 页脚文字 | 同作者名 |

### Step 2: 确定分页策略

**默认：自动分页**。绝大多数情况用这个：
```bash
markdown-poster article.md --auto-paginate -t "标题" -a "作者"
```

**自动分页规则**：
- 优先在 H2 标题处断页
- 大章节（超过 chars-per-page 1.3 倍）自动在段落间拆分
- 每页目标约 500 字符（≈ 3:4 比例卡片的一屏内容）
- 如果文章很长需要更多页，传 `--max-pages 30`

**手动分页**（用户明确要求时才用）：
```bash
markdown-poster article.md -c poster.yaml
```
```yaml
# poster.yaml
src: article.md
title: "标题"
author: "作者"
pages:
  - [1, 15]
  - [17, 30]
  - [32, 50]
```

### Step 3: 生成 + 截图

```
markdown-poster article.md --auto-paginate -t "标题" -a "作者"
```

这会自动完成：Markdown 解析 → HTML 生成 → 截图 → output/ 目录。

命令等效于：
```bash
# 生成 HTML
markdown-poster article.md --auto-paginate -t "标题" -a "作者" --no-screenshot
# 跳过截图的情况：用户只想预览 HTML，或没有 Playwright
```

## 完整 CLI 参考

```
markdown-poster [SRC] [OPTIONS]

必选：
  SRC                     Markdown 源文件路径

核心选项：
  -t, --title TEXT        文章标题
  -a, --author TEXT       作者名
  -d, --date TEXT         发布日期
  --avatar TEXT           头像图片路径
  --footer TEXT           页脚文字（默认同作者名）
  --auto-paginate         自动分页（推荐）
  --chars-per-page INT    每页目标字符数 (默认 500)
  --max-pages INT         自动分页最大页数 (默认 25)
  -c, --config PATH       YAML 配置文件路径

主题和格式：
  --theme [light|dark]    主题 (默认 light)
  --format [png|webp|jpeg] 输出格式 (默认 png)
  --fixed-height          固定 1080x1440 (默认自适应高度)

其他：
  --no-screenshot         仅生成 HTML，不截图
  -o, --output PATH       输出目录 (默认 output/)
  --open                  生成后在浏览器打开 HTML
  --help                  查看所有选项
```

## 分页调参指南

| 场景 | 建议参数 |
|------|---------|
| 短文章 (< 2000 字) | 默认即可 |
| 中等文章 (2000-5000 字) | `--chars-per-page 500` |
| 长文章 (> 5000 字) | `--chars-per-page 550 --max-pages 30` |
| 小红书限制 18 张内 | `--chars-per-page 700 --max-pages 18` |
| 代码多的技术文章 | 降低 chars-per-page（代码块占空间大） |
| 纯文字文章 | 提高 chars-per-page（文字紧凑） |

## 遇到问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 截图超时 | Google Fonts 加载慢 | 重试，首次加载后浏览器会缓存 |
| 截图有蓝色边框 | 浏览器扩展注入 | 默认已清理，确保 `headless=True` |
| 分页不均匀 | 某章节特别长 | 调大 `--chars-per-page` 或 `--max-pages` |
| 中文显示为方块 | 字体未加载 | 首页等 3 秒（已内置），确保网络可访问 Google Fonts |
| HTML 生成失败 | Markdown 格式异常 | 检查源文件的代码块配对、表格格式 |

## 诚实边界

- 只管排版，不写文章内容
- 图片支持 `![](url)`，不支持本地图片自动处理
- 字体从 Google Fonts CDN 加载，需网络
- CSS 针对中文优化，英文效果可能需微调
- 需要 Python + Playwright + Chromium
