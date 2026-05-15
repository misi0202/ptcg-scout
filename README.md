# PTCG Scout

宝可梦卡牌舆情监控与升值潜力预测系统。通过监控真实成交价、社群热度、PSA Pop 数据，基于供需分析 + 四象限模型，筛选出有升值潜力的卡牌和处于低点的卡盒。

## 核心逻辑

```
综合分 = (审美共识 × 0.35 + IP强度 × 0.40 + 叙事价值 × 0.25) × Pop乘数
```

- **四象限模型**：审美共识、IP强度、叙事价值、稀有度(Pop乘数)
- **供需分析**：量价关系、30天趋势判断
- **趋势信号**：🟢强烈看涨 / 🟡谨慎观望 / 🔴规避 / 🔵关注

## 项目结构

```
ptcg-scout/
├── collectors/        # 数据采集 (eBay/PSA/TCGPlayer/Reddit)
├── analyzer/          # 分析引擎 (评分/供需/趋势/卡盒)
├── notifier/          # 飞书通知
├── db/                # SQLite 存储
├── web/               # Next.js 前端看板
├── config/            # 宝可梦IP热度梯队配置
├── data/              # JSON 输出 + 历史快照
└── .github/workflows/ # 每日定时运行
```

## 快速开始

```bash
# Python 环境
conda create -n ptcg-scout python=3.12 -y
conda activate ptcg-scout
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 FEISHU_WEBHOOK_URL / REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET

# 运行
python main.py

# 前端
cd web && npm install && npm run build
```

## 定时运行

GitHub Actions 每日 UTC 22:00（北京时间次日 6:00）自动运行。在仓库 Settings → Secrets 中配置 `FEISHU_WEBHOOK_URL`、`REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`。
