"""
市场行情API
"""
from fastapi import APIRouter
from datetime import datetime
import random

from app.models.schemas import MarketIndex, APIResponse, ListResponse
from app.services.sector_flow import SectorFlowService

router = APIRouter(prefix="/market", tags=["市场"])


@router.get("/indices", response_model=ListResponse)
async def get_market_indices():
    """获取大盘指数（模拟数据）"""
    # 生成随机波动的指数数据
    indices = [
        {
            "name": "上证指数",
            "symbol": "000001",
            "value": round(3285.42 + random.uniform(-10, 10), 2),
            "change": round(random.uniform(-15, 20), 2),
            "change_percent": round(random.uniform(-0.5, 0.8), 2)
        },
        {
            "name": "深证成指",
            "symbol": "399001",
            "value": round(10520.15 + random.uniform(-30, 40), 2),
            "change": round(random.uniform(-50, 60), 2),
            "change_percent": round(random.uniform(-0.6, 0.9), 2)
        },
        {
            "name": "创业板指",
            "symbol": "399006",
            "value": round(2156.78 + random.uniform(-10, 15), 2),
            "change": round(random.uniform(-12, 18), 2),
            "change_percent": round(random.uniform(-0.7, 1.0), 2)
        }
    ]
    
    return ListResponse(data=indices, total=len(indices))


@router.get("/status")
async def get_market_status():
    """获取市场状态"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    
    # 判断交易时间
    # 上午: 9:30 - 11:30
    # 下午: 13:00 - 15:00
    is_trading = (
        (hour == 9 and minute >= 30) or
        (hour == 10) or
        (hour == 11 and minute <= 30) or
        (hour == 13) or
        (hour == 14)
    )
    
    return APIResponse(data={
        "is_trading": is_trading,
        "status": "交易中" if is_trading else "已休市",
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S")
    })


@router.get("/sectors", response_model=ListResponse)
async def get_sector_flows():
    """获取板块资金流向列表（真实数据）"""
    sectors = await SectorFlowService.get_sector_list()
    return ListResponse(data=sectors, total=len(sectors))


@router.get("/sectors/top", response_model=ListResponse)
async def get_top_sector_flows(limit: int = 5):
    """获取资金净流入最多的板块（真实数据）"""
    sectors = await SectorFlowService.get_top_sectors(limit)
    return ListResponse(data=sectors, total=len(sectors))


@router.get("/sectors/{sector_code}", response_model=APIResponse)
async def get_sector_detail(sector_code: str):
    """获取单个板块的资金流向详情（真实数据）"""
    flow_data = await SectorFlowService.get_sector_flow_detail(sector_code)
    
    if not flow_data:
        return APIResponse(data={
            "sector_code": sector_code,
            "sector_name": "暂无数据",
            "inflow_percent": 0,
            "outflow_percent": 0,
            "main_net": 0,
            "details": [
                {"label": "超大单", "value": 0},
                {"label": "大单", "value": 0},
                {"label": "中单", "value": 0},
                {"label": "小单", "value": 0}
            ],
            "update_time": "--"
        })
    
    return APIResponse(data=flow_data)
