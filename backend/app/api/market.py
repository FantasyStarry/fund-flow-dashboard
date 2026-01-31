"""
市场行情API - 模拟数据
"""
from fastapi import APIRouter
from datetime import datetime
import random

from app.models.schemas import MarketIndex, APIResponse, ListResponse

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
