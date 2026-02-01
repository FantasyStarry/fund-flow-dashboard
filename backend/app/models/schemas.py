"""
Pydantic模型定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ========== 基金相关模型 ==========

class FundBase(BaseModel):
    """基金基础信息"""
    code: str = Field(..., description="基金代码")
    name: str = Field(..., description="基金名称")


class FundPrice(BaseModel):
    """基金价格数据"""
    current: float = Field(..., description="当前净值/估值")
    previous_close: float = Field(..., description="昨日收盘")
    change: float = Field(..., description="涨跌额")
    change_percent: float = Field(..., description="涨跌幅%")
    update_time: str = Field(..., description="更新时间")


class Fund(FundBase):
    """基金完整信息（从API获取）"""
    current: float
    previous_close: float
    change: float
    change_percent: float
    update_time: str
    net_value_date: Optional[str] = None


class FundSearchResult(FundBase):
    """基金搜索结果"""
    pinyin: str
    category: str


# ========== 用户持仓模型 ==========

class HoldingBase(BaseModel):
    """持仓基础"""
    fund_code: str
    fund_name: str
    shares: float = Field(..., ge=0, description="持有份额")
    cost_price: float = Field(..., ge=0, description="成本价")
    amount: float = Field(..., ge=0, description="投资金额")


class HoldingCreate(BaseModel):
    """创建持仓"""
    fund_code: str
    fund_name: str
    shares: float = Field(..., gt=0)
    cost_price: float = Field(..., gt=0)


class HoldingUpdate(BaseModel):
    """更新持仓"""
    shares: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)


class Holding(HoldingBase):
    """持仓完整信息"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 实时计算字段
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class HoldingWithFund(Holding):
    """持仓带基金信息"""
    fund: Optional[Fund] = None


# ========== 自选模型 ==========

class FavoriteBase(FundBase):
    """自选基础"""
    pass


class FavoriteCreate(FundBase):
    """创建自选"""
    pass


class Favorite(FavoriteBase):
    """自选完整信息"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteWithFund(Favorite):
    """自选带基金信息"""
    fund: Optional[Fund] = None


# ========== 交易记录模型 ==========

class TransactionType(str, Enum):
    """交易类型"""
    BUY = "BUY"
    SELL = "SELL"


class TransactionBase(BaseModel):
    """交易基础"""
    fund_code: str
    type: TransactionType
    shares: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    fee: float = Field(default=0, ge=0)


class TransactionCreate(TransactionBase):
    """创建交易"""
    pass


class Transaction(TransactionBase):
    """交易完整信息"""
    id: int
    transaction_date: datetime
    
    class Config:
        from_attributes = True


# ========== 图表数据模型 ==========

class ChartPoint(BaseModel):
    """图表数据点"""
    time: str
    value: float


class FundChart(BaseModel):
    """基金走势图"""
    fund_code: str
    period: str = Field(..., description="1d, 1w, 1m, 3m, 1y")
    data: List[ChartPoint]
    previous_close: float


# ========== 资金流向模型 ==========

class FlowItem(BaseModel):
    """资金流向项"""
    label: str
    value: float


class FundFlow(BaseModel):
    """资金流向"""
    fund_code: str
    sector: str
    inflow_percent: float
    outflow_percent: float
    details: List[FlowItem]


# ========== 大盘指数模型 ==========

class MarketIndex(BaseModel):
    """大盘指数"""
    name: str
    symbol: str
    value: float
    change: float
    change_percent: float


# ========== 响应模型 ==========

class APIResponse(BaseModel):
    """统一API响应"""
    success: bool = True
    message: str = "success"
    data: Optional[dict] = None


class ListResponse(BaseModel):
    """列表响应"""
    success: bool = True
    message: str = "success"
    data: List = []
    total: int = 0


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
