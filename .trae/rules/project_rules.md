# FundFlow Live - AI助手规则

## 项目上下文

这是一个基金数据仪表盘全栈项目，技术栈为 FastAPI + Next.js + SQLite。

## 快速参考

### 核心文件位置
- **项目说明**: `/PROJECT.md`
- **后端API**: `backend/app/api/funds.py`, `market.py`
- **后端服务**: `backend/app/services/`
- **前端页面**: `frontend/src/app/page.tsx`
- **前端组件**: `frontend/src/components/dashboard/`
- **API客户端**: `frontend/src/lib/api.ts`
- **数据模型**: `backend/app/models/schemas.py`

### 关键服务
| 服务 | 文件 | 功能 |
|------|------|------|
| DatabaseService | `services/database.py` | SQLite操作 |
| FundHoldingsSyncService | `services/fund_holdings_sync.py` | 持仓同步 |
| FundRealtimeEstimateService | `services/fund_realtime_estimate.py` | 实时估值 |
| SectorFlowService | `services/sector_flow.py` | 板块资金流向 |
| FundSectorMapper | `services/fund_sector_mapper.py` | 板块映射 |

### API端点
- 基金详情: `GET /api/funds/{code}`
- 重仓股: `GET /api/funds/{code}/holdings`
- 实时估值: `GET /api/funds/{code}/estimate`
- 资金流向: `GET /api/funds/{code}/flow`
- 同步持仓: `POST /api/funds/{code}/sync`
- 用户持仓: `GET/POST /api/funds/user/holdings`

### 数据库表
- `user_holdings` - 用户持仓
- `user_favorites` - 自选基金
- `transactions` - 交易记录
- `fund_holdings` - 基金重仓股
- `fund_sector_mapping` - 板块映射

## 开发规范

### 颜色规范 (A股习惯)
- 红色 = 涨 / 资金流入
- 绿色 = 跌 / 资金流出

### API响应格式
```typescript
{
  success: boolean,
  message: string,
  data: any
}
```

### 错误处理
- 后端: 返回 `{success: false, message: "错误信息"}`
- 前端: 检查 `response.success` 和 `Array.isArray(response.data)`

### 数据刷新策略
- 持仓数据: 30天同步一次 (AkShare)
- 实时股价: 每次请求获取 (东方财富)
- 资金流向: 15分钟刷新

## 常用命令

### 启动后端
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 启动前端
```bash
cd frontend
npm run dev
```

### 安装依赖
```bash
# 后端
pip install -r requirements.txt

# 前端
npm install
```

## 注意事项

1. **持仓同步**: 使用 `FundHoldingsSyncService.sync_fund_holdings(code)`
2. **板块匹配**: 基于持仓分析自动推导，结果存于 `fund_sector_mapping` 表
3. **实时估值**: 算法 = Σ(股票涨跌幅 × 持仓权重) × 1.2
4. **前端安全**: 始终检查 `Array.isArray(data)` 再使用 `.map()`

## 最近修改

- 添加持仓数据持久化
- 实现板块自动匹配
- 添加重仓股实时行情展示
- 修复 holdings.map 错误
