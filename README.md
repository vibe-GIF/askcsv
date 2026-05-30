<div align="center">

# 🗣️ askcsv

**用大白话问数据，AI 帮你跑分析**

不用写一行 pandas。问一句话，AI 自动写代码、跑出结果、画好图。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI Compatible](https://img.shields.io/badge/LLM-OpenAI%20%7C%20DeepSeek%20%7C%20Kimi%20%7C%20Ollama-orange.svg)](#-配置任意大模型)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-orange.svg)](#-参与贡献)

[English](#english) · [快速开始](#-快速开始) · [支持的模型](#-配置任意大模型) · [安全说明](#-安全说明)

</div>

---

## 🎬 一眼看懂

```console
$ askcsv sample_sales.csv "哪个城市的销售额最高？各城市差距多大？"
✓ 已加载 sample_sales.csv：800 行 × 8 列

💡 销售额最高的城市是「上海」，约 ¥58,200，其次是北京（¥54,900）。
   前两名明显领先，成都最低，约为上海的 38%。

📊 图已保存：askcsv_chart.png
```

> 你只管用人话问，pandas 代码、计算、画图全交给 AI。

## 💡 为什么做这个

数据分析里最烦的，往往不是「想不到问什么」，而是**把问题翻译成代码**：
`groupby` 还是 `pivot_table`？日期怎么 resample？图怎么画……

`askcsv` 把这一步交给大模型：**你提问 → AI 写 pandas 代码 → 自动执行 → 给你结论和图**。
跑错了它还会**自己看报错、改代码、重试**，直到跑通。

## ✨ 功能特性

| | 功能 | 说明 |
|---|---|---|
| 🗣️ | **自然语言提问** | 中文/英文都行，不用懂 pandas |
| 🔁 | **自动纠错重试** | 代码报错时，把错误喂回模型自我修复 |
| 📊 | **自动画图** | 需要时自动出图并保存 |
| 💬 | **交互模式** | 加载一次，连续追问 |
| 🔌 | **兼容任意大模型** | OpenAI / DeepSeek / Kimi / 智谱 / 本地 Ollama |
| 🛡️ | **基础安全沙箱** | 禁用文件/网络/系统调用，拦截危险代码 |
| 🐍 | **可当库调用** | 一个 `ask()` 函数集成进你的项目 |

## 🚀 快速开始

### 1. 安装

```bash
pip install askcsv
```

### 2. 配置大模型（环境变量）

```bash
# 用 OpenAI
export ASKCSV_API_KEY="sk-..."

# 或用国内模型（示例：DeepSeek，便宜量大）
export ASKCSV_API_KEY="sk-..."
export ASKCSV_BASE_URL="https://api.deepseek.com/v1"
export ASKCSV_MODEL="deepseek-chat"
```

> Windows PowerShell 用 `$env:ASKCSV_API_KEY="sk-..."`

### 3. 开问

```bash
# 一次性提问
askcsv data.csv "上个季度哪个品类增长最快？"

# 进入交互模式，连续追问
askcsv data.csv

# 顺便看看 AI 写了什么代码
askcsv data.csv "客单价最高的渠道是？" --show-code
```

## 🔌 配置任意大模型

只要兼容 OpenAI 的 `/chat/completions` 接口都能用，改三个环境变量即可：

| 服务 | `ASKCSV_BASE_URL` | `ASKCSV_MODEL`（示例） |
|---|---|---|
| OpenAI | （默认，可不填） | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Kimi / Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| 本地 Ollama | `http://localhost:11434/v1` | `qwen2.5` |

> 用本地 Ollama 时，`ASKCSV_API_KEY` 随便填一个非空值即可，数据不出本机。

## 🐍 在 Python 里用

```python
import askcsv

df = askcsv.load_data("data.csv")
client = askcsv.LLMClient()                 # 读环境变量配置
res = askcsv.ask(df, "哪个城市销售额最高？", client)

print(res.answer)        # 文字结论
print(res.code)          # AI 生成的代码
print(res.chart_path)    # 图片路径（如果画了图）
```

## 🎮 上手体验

```bash
python examples/generate_sample.py     # 生成 sample_sales.csv
askcsv sample_sales.csv "线上和线下哪个渠道客单价更高？"
```

## 🛡️ 安全说明

askcsv 会**执行大模型生成的 Python 代码**。为降低风险，它已经：

- 只在受限命名空间运行，**禁用** `open`/`eval`/`exec` 等危险内置函数；
- **静态拦截** `import os`、`subprocess`、网络请求等关键字；
- 只暴露 `df` / `pd` / `np` / `plt`。

即便如此，仍建议**只在可信数据上使用**；对不可信数据，请放进容器/沙箱运行。

## 🗺️ Roadmap

- [ ] 多轮对话记忆（基于上一问的结果继续追问）
- [ ] 导出分析报告（结合 [QuickEDA](https://github.com/vibe-GIF/quickeda)）
- [ ] 支持直接连数据库（SQLite / MySQL）
- [ ] 把生成的代码沉淀成可复用脚本

## 🤝 参与贡献

欢迎 PR！如果这个项目帮到了你，点个 ⭐ Star 是最大的支持。

## 📄 License

[MIT](LICENSE) © 2026

---

<a name="english"></a>

## English

**askcsv** — Ask your data questions in plain English; AI writes the pandas, runs it, and plots it.

```bash
pip install askcsv
export ASKCSV_API_KEY="sk-..."
askcsv data.csv "which city has the highest sales?"
```

- Natural-language questions → AI-generated pandas code → executed → answer + chart
- Self-corrects on errors (feeds the traceback back to the model and retries)
- Works with any OpenAI-compatible API: OpenAI / DeepSeek / Kimi / local Ollama
- Basic sandbox: dangerous builtins disabled, file/network/system calls blocked

> ⚠️ It executes LLM-generated code — use on trusted data, or run in a sandbox.

MIT licensed. A ⭐ would mean a lot!
