"""
基金相关API路由
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.schemas import (
    Fund, FundSearchResult, FundChart, FundFlow, MarketIndex,
    Holding, HoldingCreate, HoldingUpdate,
    Favorite, FavoriteCreate,
    Transaction, TransactionCreate,
    APIResponse, ListResponse
)
from app.services.fund_api import FundAPIService, DEFAULT_FUND_CODES
from app.services.database import get_db, DatabaseService
from app.services.sector_flow import SectorFlowService
from app.services.fund_realtime_estimate import estimate_fund_realtime_value
from app.services.fund_holdings_sync import get_fund_holdings_with_quotes, sync_fund_holdings
from app.services.database import get_db

router = APIRouter(prefix="/funds", tags=["基金"])


# ========== 基金数据API（从外部API获取）==========

@router.get("/search", response_model=ListResponse)
async def search_funds(
    keyword: str = Query(..., min_length=1, description="搜索关键词")
):
    """搜索基金"""
    results = await FundAPIService.search_funds(keyword)
    return ListResponse(
        data=results,
        total=len(results)
    )


@router.get("/hot", response_model=ListResponse)
async def get_hot_funds():
    """获取热门基金列表"""
    funds = await FundAPIService.get_multiple_funds(DEFAULT_FUND_CODES)
    return ListResponse(
        data=funds,
        total=len(funds)
    )


@router.get("/{fund_code}", response_model=APIResponse)
async def get_fund_detail(fund_code: str):
    """获取基金详情"""
    fund = await FundAPIService.get_fund_realtime(fund_code)
    
    # 如果获取不到实时数据（休市或API失败），尝试获取最近一个交易日的数据
    if not fund:
        # 获取历史数据（最近1天）
        history = await FundAPIService.get_fund_history(fund_code, "1w")
        fund_info = FundAPIService.FUNDS_DB.get(fund_code)
        
        if history and history.get("data") and len(history["data"]) > 0:
            # 获取最近一个交易日的数据
            latest_data = history["data"][-1]
            previous_data = history["data"][-2] if len(history["data"]) > 1 else latest_data
            
            close_price = latest_data.get("close", 0)
            prev_close = previous_data.get("close", close_price)
            change = close_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            
            fund = {
                "code": fund_code,
                "name": fund_info["name"] if fund_info else "未知基金",
                "current": round(close_price, 4),
                "previous_close": round(prev_close, 4),
                "change": round(change, 4),
                "change_percent": round(change_percent, 2),
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "net_value_date": latest_data.get("time", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")),
                "market_closed": True  # 标记为休市状态
            }
        elif fund_info:
            # 没有历史数据，返回基本信息
            fund = {
                "code": fund_code,
                "name": fund_info["name"],
                "current": 0,
                "previous_close": 0,
                "change": 0,
                "change_percent": 0,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "net_value_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "market_closed": True
            }
        else:
            raise HTTPException(status_code=404, detail="基金不存在")
    
    return APIResponse(data=fund)


@router.get("/{fund_code}/chart", response_model=APIResponse)
async def get_fund_chart(
    fund_code: str,
    period: str = Query("1d", description="周期: 1d, 1w, 1m, 3m, 1y")
):
    """获取基金走势图"""
    chart_data = await FundAPIService.get_fund_history(fund_code, period)
    
    # 如果获取不到数据，返回空数据结构而不是404
    if not chart_data:
        chart_data = {
            "fund_code": fund_code,
            "period": period,
            "data": [],
            "previous_close": 0
        }
    
    return APIResponse(data=chart_data)


@router.get("/{fund_code}/holdings", response_model=APIResponse)
async def get_fund_holdings(fund_code: str):
    """
    获取基金重仓股及实时行情
    优先从数据库获取，如果没有则自动同步
    """
    try:
        data = await get_fund_holdings_with_quotes(fund_code)
        
        if not data:
            return APIResponse(
                code=404,
                message="无法获取基金持仓数据",
                data=None
            )
        
        return APIResponse(data=data)
        
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"获取持仓数据失败: {str(e)}",
            data=None
        )


@router.post("/{fund_code}/sync", response_model=APIResponse)
async def sync_fund_data(fund_code: str):
    """
    手动同步基金持仓数据
    用于管理员更新持仓信息
    """
    try:
        db = await get_db()
        success = await sync_fund_holdings(fund_code, db)
        
        if success:
            return APIResponse(message="同步成功")
        else:
            return APIResponse(
                code=400,
                message="同步失败",
                data=None
            )
            
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"同步失败: {str(e)}",
            data=None
        )


@router.get("/{fund_code}/estimate", response_model=APIResponse)
async def get_fund_realtime_estimate(fund_code: str):
    """
    获取基金实时估值（基于持仓股票实时计算）
    
    算法：
    1. 获取基金前10大重仓股及权重
    2. 获取这些股票的实时涨跌幅
    3. 加权计算估算涨跌幅
    4. 应用修正系数（前10大持仓通常占总仓位的60-80%）
    """
    try:
        estimate_data = await estimate_fund_realtime_value(fund_code)
        
        if not estimate_data:
            return APIResponse(
                code=404,
                message="无法获取基金估值数据",
                data=None
            )
        
        return APIResponse(data=estimate_data)
        
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"估值计算失败: {str(e)}",
            data=None
        )


@router.get("/{fund_code}/flow", response_model=APIResponse)
async def get_fund_flow(fund_code: str):
    """获取基金相关板块的资金流向（真实数据）"""
    # 获取基金信息以支持智能板块匹配
    fund_info = FundAPIService.FUNDS_DB.get(fund_code, {})
    fund_name = fund_info.get("name", "")
    
    flow_data = await SectorFlowService.get_sector_flow_by_fund(fund_code, fund_name)
    
    if not flow_data:
        # 如果获取失败，返回空数据结构
        return APIResponse(data={
            "fund_code": fund_code,
            "sector": "暂无数据",
            "sector_code": "",
            "inflow_percent": 0,
            "outflow_percent": 0,
            "main_net": 0,
            "details": [
                {"label": "超大单", "value": 0},
                {"label": "大单", "value": 0},
                {"label": "中单", "value": 0},
                {"label": "小单", "value": 0}
            ],
            "update_time": "--",
            "match_reason": ""
        })
    
    # 适配前端数据格式
    return APIResponse(data={
        "fund_code": fund_code,
        "sector": flow_data["sector_name"],
        "sector_code": flow_data["sector_code"],
        "inflow_percent": flow_data["inflow_percent"],
        "outflow_percent": flow_data["outflow_percent"],
        "main_net": flow_data["main_net"],
        "details": flow_data["details"],
        "update_time": flow_data["update_time"],
        "match_reason": flow_data.get("match_reason", ""),
        "refresh_interval": 900  # 建议刷新间隔：15分钟（秒）
    })


# ========== 用户持仓API（SQLite存储）==========

@router.get("/user/holdings", response_model=ListResponse)
async def get_user_holdings(db: DatabaseService = Depends(get_db)):
    """获取用户所有持仓"""
    holdings = await db.get_all_holdings()
    
    # 获取实时数据并合并
    if holdings:
        codes = [h["fund_code"] for h in holdings]
        funds = await FundAPIService.get_multiple_funds(codes)
        fund_map = {f["code"]: f for f in funds}
        
        for holding in holdings:
            fund = fund_map.get(holding["fund_code"])
            if fund:
                current_price = fund["current"]
                holding["current_price"] = current_price
                holding["market_value"] = round(holding["shares"] * current_price, 2)
                holding["profit_loss"] = round(
                    holding["market_value"] - holding["amount"], 2
                )
                holding["profit_loss_percent"] = round(
                    (holding["profit_loss"] / holding["amount"]) * 100, 2
                ) if holding["amount"] > 0 else 0
    
    return ListResponse(data=holdings, total=len(holdings))


@router.post("/user/holdings", response_model=APIResponse)
async def add_holding(
    holding: HoldingCreate,
    db: DatabaseService = Depends(get_db)
):
    """添加持仓"""
    # 计算金额
    amount = holding.shares * holding.cost_price
    
    success = await db.add_holding(
        fund_code=holding.fund_code,
        fund_name=holding.fund_name,
        shares=holding.shares,
        cost_price=holding.cost_price,
        amount=amount
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="添加持仓失败")
    
    # 添加交易记录
    await db.add_transaction(
        fund_code=holding.fund_code,
        type_="BUY",
        shares=holding.shares,
        price=holding.cost_price,
        amount=amount,
        fee=0
    )
    
    return APIResponse(message="持仓添加成功")


@router.put("/user/holdings/{fund_code}", response_model=APIResponse)
async def update_holding(
    fund_code: str,
    update: HoldingUpdate,
    db: DatabaseService = Depends(get_db)
):
    """更新持仓"""
    success = await db.update_holding(
        fund_code=fund_code,
        shares=update.shares,
        cost_price=update.cost_price
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="更新持仓失败")
    
    return APIResponse(message="持仓更新成功")


@router.delete("/user/holdings/{fund_code}", response_model=APIResponse)
async def delete_holding(
    fund_code: str,
    db: DatabaseService = Depends(get_db)
):
    """删除持仓"""
    success = await db.delete_holding(fund_code)
    
    if not success:
        raise HTTPException(status_code=400, detail="删除持仓失败")
    
    return APIResponse(message="持仓删除成功")


# ========== 自选基金API ==========

@router.get("/user/favorites", response_model=ListResponse)
async def get_user_favorites(db: DatabaseService = Depends(get_db)):
    """获取用户自选基金"""
    favorites = await db.get_favorites()
    
    # 获取实时数据并合并
    if favorites:
        codes = [f["fund_code"] for f in favorites]
        funds = await FundAPIService.get_multiple_funds(codes)
        fund_map = {f["code"]: f for f in funds}
        
        for favorite in favorites:
            favorite["fund"] = fund_map.get(favorite["fund_code"])
    
    return ListResponse(data=favorites, total=len(favorites))


@router.post("/user/favorites", response_model=APIResponse)
async def add_favorite(
    favorite: FavoriteCreate,
    db: DatabaseService = Depends(get_db)
):
    """添加自选"""
    success = await db.add_favorite(
        fund_code=favorite.code,
        fund_name=favorite.name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="添加自选失败")
    
    return APIResponse(message="添加自选成功")


@router.delete("/user/favorites/{fund_code}", response_model=APIResponse)
async def remove_favorite(
    fund_code: str,
    db: DatabaseService = Depends(get_db)
):
    """移除自选"""
    success = await db.remove_favorite(fund_code)
    
    if not success:
        raise HTTPException(status_code=400, detail="移除自选失败")
    
    return APIResponse(message="移除自选成功")


# ========== 交易记录API ==========

@router.get("/user/transactions", response_model=ListResponse)
async def get_transactions(
    fund_code: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: DatabaseService = Depends(get_db)
):
    """获取交易记录"""
    transactions = await db.get_transactions(fund_code, limit)
    return ListResponse(data=transactions, total=len(transactions))
