# Fund Flow Dashboard 💰

一个基于 Next.js + FastAPI 的全栈基金数据分析和投资管理平台。

[![GitHub](https://img.shields.io/badge/GitHub-FantasyStarry%2Ffund--flow--dashboard-blue?logo=github)](https://github.com/FantasyStarry/fund-flow-dashboard)

## 🚀 项目简介

Fund Flow Dashboard 是一个功能强大的基金数据仪表盘，提供实时基金行情、用户持仓管理、自选基金追踪等功能。采用现代化的技术栈，前后端分离架构，数据实时更新，界面简洁美观。

## ✨ 功能特性

### 已实现功能

- 📊 **实时基金数据展示**
  - 从天天基金网获取实时估值数据
  - 基金净值、涨跌幅、更新时间
  - 分时走势图（Lightweight Charts）

- 💼 **用户持仓管理**（SQLite存储）
  - 添加/删除持仓
  - 实时计算盈亏
  - 持仓列表展示

- ⭐ **自选基金**
  - 添加/移除自选
  - 自选列表实时更新

- 📈 **大盘指数**
  - 上证指数、深证成指、创业板指
  - 实时行情展示

- 💸 **资金流向**
  - 板块资金流向展示
  - 超大单/大单/中单/小单分析

## 🛠️ 技术栈

### 前端
| 技术 | 版本 | 说明 |
|------|------|------|
| [Next.js](https://nextjs.org/) | 16.1.6 | React 框架 |
| [React](https://react.dev/) | 19.2.3 | UI 库 |
| [TypeScript](https://www.typescriptlang.org/) | 5.x | 类型安全 |
| [Tailwind CSS](https://tailwindcss.com/) | 4.x | 样式框架 |
| [Lightweight Charts](https://tradingview.github.io/lightweight-charts/) | 5.1.0 | 图表库 |
| [Lucide React](https://lucide.dev/) | 0.563.0 | 图标库 |
| [SWR](https://swr.vercel.app/) | 2.3.8 | 数据获取 |

### 后端
| 技术 | 版本 | 说明 |
|------|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.115.0 | Web 框架 |
| [Python](https://www.python.org/) | 3.11+ | 编程语言 |
| [Uvicorn](https://www.uvicorn.org/) | 0.32.0 | ASGI 服务器 |
| [Pydantic](https://docs.pydantic.dev/) | 2.9.0 | 数据验证 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0.36 | ORM |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | 0.20.0 | 异步 SQLite |
| [HTTPX](https://www.python-httpx.org/) | 0.27.0 | HTTP 客户端 |
| [APScheduler](https://apscheduler.readthedocs.io/) | 3.10.4 | 任务调度 |

### 数据源
- **基金实时数据**: [天天基金网](https://fund.eastmoney.com/) 开放 API
- **大盘指数**: [东方财富](https://www.eastmoney.com/) API

## 📁 项目结构

```
fund-flow-dashboard/
├── 📁 frontend/              # Next.js 前端
│   ├── 📁 src/
│   │   ├── 📁 app/          # App Router 页面
│   │   ├── 📁 components/   # React 组件
│   │   │   ├── 📁 layout/   # 布局组件 (Header, Sidebar)
│   │   │   ├── 📁 dashboard/# 仪表盘组件
│   │   │   └── 📁 charts/   # 图表组件
│   │   └── 📁 lib/          # 工具函数 / API 客户端
│   ├── 📄 package.json
│   └── 📄 next.config.ts
│
├── 📁 backend/              # FastAPI 后端
│   ├── 📁 app/
│   │   ├── 📁 api/          # API 路由
│   │   ├── 📁 models/       # Pydantic 模型
│   │   ├── 📁 services/     # 业务逻辑
│   │   │   ├── 📄 fund_api.py    # 天天基金 API 服务
│   │   │   └── 📄 database.py    # SQLite 数据库服务
│   │   └── 📄 main.py       # FastAPI 应用入口
│   ├── 📁 data/             # SQLite 数据库文件
│   └── 📄 requirements.txt
│
└── 📄 README.md
```

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Python 3.11+

### 1. 克隆项目

```bash
git clone https://github.com/FantasyStarry/fund-flow-dashboard.git
cd fund-flow-dashboard
```

### 2. 启动后端服务

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python run.py
```

后端服务将在 http://localhost:8000 启动

- API 文档: http://localhost:8000/docs
- 替代文档: http://localhost:8000/redoc

### 3. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 📡 API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/funds/hot` | 热门基金列表 |
| GET | `/api/funds/search` | 搜索基金 |
| GET | `/api/funds/{code}` | 基金详情 |
| GET | `/api/funds/{code}/chart` | 走势图数据 |
| GET | `/api/funds/{code}/flow` | 资金流向 |
| GET | `/api/funds/user/holdings` | 用户持仓 |
| POST | `/api/funds/user/holdings` | 添加持仓 |
| DELETE | `/api/funds/user/holdings/{code}` | 删除持仓 |
| GET | `/api/funds/user/favorites` | 自选列表 |
| POST | `/api/funds/user/favorites` | 添加自选 |
| DELETE | `/api/funds/user/favorites/{code}` | 移除自选 |
| GET | `/api/market/indices` | 大盘指数 |
| GET | `/api/market/status` | 市场状态 |

## 💾 数据存储方案

### 基金数据
- **来源**: 天天基金网开放 API
- **获取方式**: 实时 HTTP 请求
- **缓存策略**: 前端 30 秒自动刷新

### 用户数据
- **存储**: SQLite 数据库 (`backend/data/fundpro.db`)
- **数据表**:
  - `user_holdings`: 用户持仓（基金代码、份额、成本价）
  - `user_favorites`: 自选基金
  - `transactions`: 交易记录

### 数据库迁移
当前 SQLite 配置可无缝迁移到 PostgreSQL/MySQL:

1. 修改 `backend/app/services/database.py`
2. 更换数据库连接驱动 (aiosqlite → asyncpg/aiomysql)
3. 保持 SQLAlchemy 模型不变

## 🗺️ 开发计划

- [x] 项目架构搭建
- [x] 天天基金 API 集成
- [x] SQLite 数据库设计
- [x] 基础 API 开发
- [x] 前端布局组件
- [x] 图表组件集成
- [x] 持仓管理功能
- [ ] 用户认证系统
- [ ] 历史数据存储
- [ ] 数据分析报表
- [ ] 移动端适配优化

## ⚠️ 注意事项

1. **API 限制**: 天天基金网 API 有访问频率限制，请合理控制请求频率
2. **数据准确性**: 实时估值仅供参考，实际净值以基金公司公布为准
3. **投资有风险**: 本系统仅供学习研究，不构成投资建议

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证开源。

## 🙏 致谢

- [天天基金网](https://fund.eastmoney.com/) 提供基金数据 API
- [TradingView](https://www.tradingview.com/) 提供 Lightweight Charts

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/FantasyStarry">FantasyStarry</a>
</p>
