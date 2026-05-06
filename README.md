# markdown-poster

**Markdown → 小红书图文卡片，一行命令出图。**

将 Markdown 文章自动排版成精美的社交媒体图片。支持自动分页、双主题、3:4 比例，专为中文长文优化。

## 效果预览

Markdown 正文 → HTML + CSS → Playwright 截图 → PNG / WebP 卡片，带标题、作者区、页码和页脚。

## 快速开始

```bash
# 安装
pip install -e .
playwright install chromium

# 一行出图
markdown-poster article.md --auto-paginate -t "标题" -a "作者"
```

输出在 `output/` 目录下。

## 用法

```bash
# 自动分页 + 暗色主题 + WebP
markdown-poster article.md --auto-paginate --theme dark --format webp

# 固定 1080×1440 比例
markdown-poster article.md --auto-paginate --fixed-height

# YAML 配置驱动
markdown-poster -c poster.yaml

# 仅生成 HTML（不截图）
markdown-poster article.md --auto-paginate --no-screenshot
```

### 参数表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --title` | 文章标题 | — |
| `-a, --author` | 作者名 | — |
| `-d, --date` | 发布日期 | 今天 |
| `--avatar` | 头像图片路径 | 无 |
| `--footer` | 页脚文字 | 同作者名 |
| `--auto-paginate` | 自动分页 | 关闭 |
| `--chars-per-page` | 每页目标字数 | 500 |
| `--max-pages` | 最大页数 | 25 |
| `--theme` | light / dark | light |
| `--format` | png / webp / jpeg | png |
| `--fixed-height` | 固定 1080×1440 | 自适应 |
| `--no-screenshot` | 仅生成 HTML | 关闭 |
| `--open` | 浏览器打开 HTML | 关闭 |
| `-o, --output` | 输出目录 | output/ |
| `-c, --config` | YAML 配置文件路径 | — |

### YAML 配置

```yaml
# poster.yaml
src: article.md
title: "文章标题"
author: "作者"
date: "2026年5月6日"
avatar: avatar.jpg
footer: "页脚文字"
auto_paginate: true
chars_per_page: 500
max_pages: 25
theme: light
format: png
fixed_height: false
```

配置文件与 CLI 参数可混用，CLI 优先级更高。

## 项目结构

```
markdown-poster/
├── poster/
│   ├── cli.py          # Click CLI 入口
│   ├── config.py       # 配置系统 (YAML + CLI 合并)
│   ├── markdown.py     # mistune v3 渲染器
│   ├── builder.py      # HTML 拼装
│   ├── pagination.py   # 自动分页引擎
│   ├── screenshot.py   # Playwright 截图
│   └── themes/         # Light / Dark 主题
├── templates/
│   └── xhs.css         # CSS 设计系统
├── tests/              # 34 项单元测试
├── examples/           # 示例文章
└── pyproject.toml
```

## 技术栈

| 组件 | 技术 |
|------|------|
| Markdown 解析 | mistune v3 |
| 截图 | Playwright (Chromium) |
| CLI | Click |
| 配置 | YAML |
| 字体 | Noto Serif SC / Inter / JetBrains Mono |

## 分页说明

自动分页优先在 H2 标题处断页，过大章节会在段落边界继续拆分，短页自动合并。每页目标 500 字符，适合 3:4 比例卡片的一屏内容。

| 场景 | 建议参数 |
|------|---------|
| 短文章 (< 2000 字) | 默认即可 |
| 长文章 (> 5000 字) | `--chars-per-page 550 --max-pages 30` |
| 18 张限制 | `--chars-per-page 700 --max-pages 18` |
| 代码多 | 降低 chars-per-page |

## License

MIT
