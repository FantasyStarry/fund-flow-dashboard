from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM_LOW = "中低风险"
    MEDIUM = "中风险"
    MEDIUM_HIGH = "中高风险"
    HIGH = "高风险"


class FundType(str, Enum):
    """基金类型"""
    STOCK_INDEX = "指数型-股票"
    STOCK = "股票型"
    BOND = "债券型"
    HYBRID = "混合型"
    MONEY = "货币型"
    QDII = "QDII"


class FundBase(BaseModel):
    """基金基础模型"""
    code: str = Field(..., description="基金代码", min_length=6, max_length=6)
    name: str = Field(..., description="基金名称")
    type: FundType = Field(..., description="基金类型")
    risk_level: RiskLevel = Field(..., description="风险等级")
    scale: float = Field(..., description="基金规模(亿)", ge=0)


class FundPrice(BaseModel):
    """基金价格数据"""
    current: float = Field(..., description="当前净值")
    previous_close: float = Field(..., description="昨日收盘")
    change: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅(%)")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")


class Fund(FundBase):
    """基金完整模型"""
    price: FundPrice
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "161725",
                "name": "招商中证白酒指数(LOF)A",
                "type": "指数型-股票",
                "risk_level": "高风险",
                "scale": 485.23,
                "price": {
                    "current": 1.2450,
                    "previous_close": 1.2152,
                    "change": 0.0298,
                    "change_percent": 2.45,
                    "update_time": "2026-01-31T14:35:02"
                }
            }
        }


class StockHolding(BaseModel):
    """重仓股模型"""
    name: str = Field(..., description="股票名称")
    price: float = Field(..., description="当前价格", ge=0)
    change: float = Field(..., description="涨跌幅(%)")
    weight: float = Field(..., description="持仓权重(%)", ge=0, le=100)
    contribution: float = Field(..., description="对基金贡献度(%)")


class FundHoldings(BaseModel):
    """基金持仓模型"""
    fund_code: str
    holdings: List[StockHolding]
    update_time: datetime = Field(default_factory=datetime.now)


class ChartPoint(BaseModel):
    """图表数据点"""
    time: str = Field(..., description="时间")
    value: float = Field(..., description="数值")


class FundChart(BaseModel):
    """基金走势图数据"""
    fund_code: str
    period: str = Field(..., description="周期: 1d, 1w, 1m, 3m, 1y")
    data: List[ChartPoint]
    previous_close: float


class FlowItem(BaseModel):
    """资金流向项"""
    label: str
    value: float = Field(..., description="金额(亿)")


class FundFlow(BaseModel):
    """资金流向模型"""
    fund_code: str
    sector: str = Field(..., description="板块名称")
    inflow_percent: float = Field(..., ge=0, le=100)
    outflow_percent: float = Field(..., ge=0, le=100)
    details: List[FlowItem]
    update_time: datetime = Field(default_factory=datetime.now)


class MarketIndex(BaseModel):
    """大盘指数"""
    name: str = Field(..., description="指数名称")
    symbol: str = Field(..., description="指数代码")
    value: float = Field(..., description="当前点数")
    change: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅(%)")


class APIResponse(BaseModel):
    """API统一响应"""
    success: bool = True
    message: str = "success"
    data: Optional[dict] = None
