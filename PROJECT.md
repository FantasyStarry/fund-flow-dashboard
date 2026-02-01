# FundFlow Live - 基金数据仪表盘

## 项目概述

一个全栈基金数据展示平台，提供基金实时估值、重仓股行情、板块资金流向等功能。

## 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite (aiosqlite)
- **数据源**: 
  - AkShare (基金持仓数据)
  - 东方财富 (实时股价、板块资金流向)
- **关键依赖**: httpx, akshare, aiosqlite, uvicorn

### 前端
- **框架**: Next.js 16 + React 19 + TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts
- **图标**: Lucide React

## 项目结构

```
Found_Flow_Live/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由
│   │   │   ├── funds.py   # 基金相关API
│   │   │   └── market.py  # 市场数据API
│   │   ├── models/        # 数据模型
│   │   │   └── schemas.py # Pydantic模型
│   │   ├── services/      # 业务逻辑
│   │   │   ├── database.py           # SQLite数据库服务
│   │   │   ├── fund_api.py           # 基金API封装
│   │   │   ├── fund_holdings_sync.py # 持仓同步服务
│   │   │   ├── fund_realtime_estimate.py # 实时估值服务
│   │   │   ├── fund_sector_mapper.py # 板块映射服务
│   │   │   └── sector_flow.py        # 板块资金流向
│   │   └── main.py        # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js页面
│   │   │   └── page.tsx   # 主页面
│   │   ├── components/    # React组件
│   │   │   ├── charts/    # 图表组件
│   │   │   └── dashboard/ # 仪表盘组件
│   │   └── lib/
│   │       └── api.ts     # API客户端
│   └── package.json
└── data/                  # 数据目录
    └── fundpro.db         # SQLite数据库
```

## 核心功能

### 1. 基金实时估值
- **接口**: `GET /api/funds/{code}/estimate`
- **算法**: 基于前10大重仓股的实时股价加权计算
- **修正系数**: 1.2 (前10大持仓通常占60-80%)

### 2. 基金持仓数据
- **接口**: `GET /api/funds/{code}/holdings`
- **数据源**: AkShare (每30天同步一次)
- **存储**: SQLite本地缓存

### 3. 板块资金流向
- **接口**: `GET /api/funds/{code}/flow`
- **数据源**: 东方财富
- **刷新间隔**: 15分钟

### 4. 用户持仓管理
- **接口**: 
  - `GET /api/funds/user/holdings`
  - `POST /api/funds/user/holdings`
  - `DELETE /api/funds/user/holdings/{code}`

## 数据库表结构

### user_holdings (用户持仓)
```sql
fund_code TEXT PRIMARY KEY
fund_name TEXT
shares REAL
cost_price REAL
amount REAL
created_at TIMESTAMP
updated_at TIMESTAMP
```

### fund_holdings (基金持仓)
```sql
fund_code TEXT
stock_code TEXT
stock_name TEXT
weight REAL
quarter TEXT
rank INTEGER
```

### fund_sector_mapping (板块映射)
```sql
fund_code TEXT PRIMARY KEY
sector_code TEXT
sector_name TEXT
confidence REAL
match_reason TEXT
derived_from TEXT
```

## API端点汇总

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/funds/hot | GET | 热门基金 |
| /api/funds/search | GET | 搜索基金 |
| /api/funds/{code} | GET | 基金详情 |
| /api/funds/{code}/chart | GET | 走势图 |
| /api/funds/{code}/holdings | GET | 重仓股 |
| /api/funds/{code}/estimate | GET | 实时估值 |
| /api/funds/{code}/flow | GET | 资金流向 |
| /api/funds/{code}/sync | POST | 同步持仓 |
| /api/funds/user/holdings | GET/POST | 用户持仓 |
| /api/funds/user/favorites | GET/POST | 自选基金 |
| /api/market/indices | GET | 大盘指数 |
| /api/market/sectors | GET | 板块列表 |

## 启动命令

### 后端
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm run dev
```

## 配置文件

### 后端配置 (app/core/config.py)
- 数据库路径: `data/fundpro.db`
- API前缀: `/api`
- CORS允许来源: `http://localhost:3000`

### 前端配置 (next.config.ts)
- API代理: `http://localhost:8000/api`
- 端口: 3000

## 开发注意事项

1. **持仓数据同步**: 每30天自动同步，可手动触发 `/api/funds/{code}/sync`
2. **实时数据**: 股价和资金流向实时获取，不缓存
3. **A股颜色规范**: 红色=涨/流入，绿色=跌/流出
4. **错误处理**: API返回统一格式 `{success, message, data}`

## 最近更新

- 添加基金持仓数据持久化 (SQLite)
- 实现基于持仓的板块自动匹配
- 添加重仓股实时行情展示
- 修复前端 holdings.map 错误
