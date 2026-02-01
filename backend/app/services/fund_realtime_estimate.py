"""
基金实时估值服务
基于持仓数据和实时股价计算基金实时涨跌幅
"""
import httpx
import akshare as ak
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache


@dataclass
class StockHolding:
    """股票持仓"""
    code: str  # 股票代码
    name: str  # 股票名称
    weight: float  # 持仓权重（占净值比例）


@dataclass
class StockQuote:
    """股票实时行情"""
    code: str
    name: str
    current_price: float
    change_percent: float  # 涨跌幅
    update_time: str


class FundRealtimeEstimateService:
    """基金实时估值服务"""
    
    # 缓存配置
    CACHE_DURATION = timedelta(minutes=5)  # 持仓数据缓存5分钟
    
    def __init__(self):
        self._holdings_cache: Dict[str, tuple] = {}  # fund_code -> (holdings, cache_time)
    
    def _get_cached_holdings(self, fund_code: str) -> Optional[List[StockHolding]]:
        """获取缓存的持仓数据"""
        if fund_code in self._holdings_cache:
            holdings, cache_time = self._holdings_cache[fund_code]
            if datetime.now() - cache_time < self.CACHE_DURATION:
                return holdings
        return None
    
    def _set_cached_holdings(self, fund_code: str, holdings: List[StockHolding]):
        """设置持仓数据缓存"""
        self._holdings_cache[fund_code] = (holdings, datetime.now())
    
    def get_fund_holdings(self, fund_code: str, top_n: int = 10) -> List[StockHolding]:
        """
        获取基金前N大重仓股
        使用AkShare获取，带缓存
        """
        # 检查缓存
        cached = self._get_cached_holdings(fund_code)
        if cached:
            return cached[:top_n]
        
        try:
            # 获取基金持仓数据
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date="2024")
            
            if df.empty:
                return []
            
            # 取最新季度的数据
            latest_quarter = df.iloc[0]['季度']
            latest_df = df[df['季度'] == latest_quarter].head(top_n)
            
            holdings = []
            for _, row in latest_df.iterrows():
                holdings.append(StockHolding(
                    code=str(row['股票代码']).zfill(6),
                    name=row['股票名称'],
                    weight=float(row['占净值比例'])
                ))
            
            # 缓存数据
            self._set_cached_holdings(fund_code, holdings)
            
            return holdings
            
        except Exception as e:
            print(f"获取基金持仓失败 {fund_code}: {e}")
            return []
    
    async def get_stock_quotes(self, stock_codes: List[str]) -> Dict[str, StockQuote]:
        """
        批量获取股票实时行情
        使用东方财富接口
        """
        if not stock_codes:
            return {}
        
        try:
            # 构建股票代码列表（带市场标识）
            code_list = []
            for code in stock_codes:
                if code.startswith('6'):
                    code_list.append(f"1.{code}")  # 上海
                else:
                    code_list.append(f"0.{code}")  # 深圳
            
            codes_str = ','.join(code_list)
            
            url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {
                "fltt": 2,
                "invt": 2,
                "fields": "f12,f14,f2,f3",
                "secids": codes_str
            }
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                quotes = {}
                if data.get("rc") == 0:
                    diff = data.get("data", {}).get("diff", [])
                    for item in diff:
                        code = item.get("f12", "")
                        name = item.get("f14", "")
                        price = item.get("f2", 0)
                        change = item.get("f3", 0)
                        
                        if code:
                            quotes[code] = StockQuote(
                                code=code,
                                name=name,
                                current_price=price,
                                change_percent=change,
                                update_time=datetime.now().strftime("%H:%M:%S")
                            )
                
                return quotes
                
        except Exception as e:
            print(f"获取股票行情失败: {e}")
            return {}
    
    async def estimate_fund_value(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        计算基金实时估值
        
        算法：
        1. 获取基金前10大重仓股及权重
        2. 获取这些股票的实时涨跌幅
        3. 加权计算估算涨跌幅
        4. 应用修正系数（前10大持仓通常占总仓位的60-80%）
        
        公式：
        estimated_change = Σ(stock_change * stock_weight) / total_weight * adjustment_factor
        """
        # 1. 获取持仓
        holdings = self.get_fund_holdings(fund_code, top_n=10)
        
        if not holdings:
            return None
        
        # 2. 获取实时行情
        stock_codes = [h.code for h in holdings]
        quotes = await self.get_stock_quotes(stock_codes)
        
        if not quotes:
            return None
        
        # 3. 计算加权涨跌幅
        weighted_change = 0.0
        total_weight = 0.0
        stock_details = []
        
        for holding in holdings:
            quote = quotes.get(holding.code)
            if quote:
                # 该股票对基金涨跌幅的贡献 = 股票涨跌幅 * 持仓权重
                contribution = quote.change_percent * holding.weight / 100
                weighted_change += contribution
                total_weight += holding.weight
                
                stock_details.append({
                    "code": holding.code,
                    "name": holding.name,
                    "weight": holding.weight,
                    "change_percent": quote.change_percent,
                    "contribution": round(contribution, 4)
                })
        
        if total_weight == 0:
            return None
        
        # 4. 应用修正系数
        # 前10大持仓通常占总仓位的60-80%，需要放大估算值
        # 假设前10大持仓占总仓位的70%，则修正系数约为 1 / 0.7 ≈ 1.43
        # 但为了避免过度放大误差，我们使用更保守的系数 1.2
        adjustment_factor = 1.2
        
        # 基础估算值（仅基于前10大持仓）
        base_estimate = weighted_change
        
        # 修正后的估算值
        adjusted_estimate = base_estimate * adjustment_factor
        
        # 估算置信度（基于持仓集中度）
        # 前10大持仓占比越高，置信度越高
        confidence = min(95, max(60, total_weight * 1.2))
        
        return {
            "fund_code": fund_code,
            "estimate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "estimated_change_percent": round(adjusted_estimate, 2),
            "base_change_percent": round(base_estimate, 2),
            "confidence": round(confidence, 1),
            "top10_weight": round(total_weight, 2),
            "adjustment_factor": adjustment_factor,
            "holdings_count": len(stock_details),
            "stock_details": stock_details[:5]  # 只返回前5只的详情
        }
    
    async def batch_estimate(self, fund_codes: List[str]) -> Dict[str, Any]:
        """
        批量估算多个基金
        """
        results = {}
        
        # 并发获取所有基金的估算
        tasks = [self.estimate_fund_value(code) for code in fund_codes]
        estimates = await asyncio.gather(*tasks, return_exceptions=True)
        
        for code, estimate in zip(fund_codes, estimates):
            if isinstance(estimate, Exception):
                results[code] = {
                    "error": str(estimate),
                    "estimated_change_percent": 0
                }
            elif estimate:
                results[code] = estimate
            else:
                results[code] = {
                    "error": "无法获取数据",
                    "estimated_change_percent": 0
                }
        
        return results


# 单例实例
_fund_estimate_service: Optional[FundRealtimeEstimateService] = None


def get_fund_estimate_service() -> FundRealtimeEstimateService:
    """获取基金估值服务单例"""
    global _fund_estimate_service
    if _fund_estimate_service is None:
        _fund_estimate_service = FundRealtimeEstimateService()
    return _fund_estimate_service


# 便捷函数
async def estimate_fund_realtime_value(fund_code: str) -> Optional[Dict[str, Any]]:
    """
    估算基金实时涨跌幅
    """
    service = get_fund_estimate_service()
    return await service.estimate_fund_value(fund_code)


# 测试
if __name__ == "__main__":
    async def test():
        service = FundRealtimeEstimateService()
        
        # 测试白酒基金
        print("=" * 50)
        print("测试基金: 161725 (招商中证白酒)")
        print("=" * 50)
        
        result = await service.estimate_fund_value("161725")
        if result:
            print(f"\n估算时间: {result['estimate_time']}")
            print(f"估算涨跌幅: {result['estimated_change_percent']:.2f}%")
            print(f"基础涨跌幅: {result['base_change_percent']:.2f}%")
            print(f"置信度: {result['confidence']}%")
            print(f"前10大持仓占比: {result['top10_weight']}%")
            print(f"\n主要持仓贡献:")
            for stock in result['stock_details']:
                print(f"  {stock['name']}: {stock['change_percent']:+.2f}% (权重{stock['weight']}%, 贡献{stock['contribution']:+.4f})")
        else:
            print("获取失败")
    
    asyncio.run(test())
