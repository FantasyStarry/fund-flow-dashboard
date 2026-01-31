"""
基金数据API服务
使用腾讯财经API获取真实数据
"""
import httpx
import re
import json
import random
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

from app.services.market_calendar import MarketCalendarService


class FundAPIService:
    """基金数据API服务 - 腾讯财经API"""
    
    # 腾讯财经API
    TENCENT_API = "http://qt.gtimg.cn/q="
    TENCENT_MINUTE_API = "http://web.ifzq.gtimg.cn/appstock/app/minute/query?code="
    TENCENT_KLINE_API = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    
    @staticmethod
    def is_market_open() -> bool:
        """
        检查市场是否开盘
        考虑交易日历（节假日、周末）和交易时间
        """
        return MarketCalendarService.is_market_open()
    
    # 基金基础数据
    FUNDS_DB = {
        "161725": {
            "code": "161725",
            "name": "招商中证白酒指数(LOF)A",
            "type": "指数型-股票",
            "risk_level": "高风险",
            "scale": 485.23,
        },
        "005827": {
            "code": "005827",
            "name": "易方达蓝筹精选混合",
            "type": "混合型",
            "risk_level": "中高风险",
            "scale": 562.15,
        },
        "000001": {
            "code": "000001",
            "name": "华夏成长混合",
            "type": "混合型",
            "risk_level": "中高风险",
            "scale": 120.50,
        },
        "110022": {
            "code": "110022",
            "name": "易方达消费行业股票",
            "type": "股票型",
            "risk_level": "高风险",
            "scale": 280.35,
        },
        "001632": {
            "code": "001632",
            "name": "天弘中证食品饮料ETF联接A",
            "type": "指数型-股票",
            "risk_level": "中高风险",
            "scale": 95.80,
        },
        "003096": {
            "code": "003096",
            "name": "中欧医疗健康混合A",
            "type": "混合型",
            "risk_level": "中高风险",
            "scale": 320.45,
        },
        "002190": {
            "code": "002190",
            "name": "农银新能源主题混合",
            "type": "混合型",
            "risk_level": "高风险",
            "scale": 180.25,
        },
        "007994": {
            "code": "007994",
            "name": "招商国证生物医药指数(LOF)A",
            "type": "指数型-股票",
            "risk_level": "高风险",
            "scale": 145.60,
        },
        "000248": {
            "code": "000248",
            "name": "汇添富中证主要消费ETF联接A",
            "type": "指数型-股票",
            "risk_level": "中高风险",
            "scale": 78.90,
        },
        "110003": {
            "code": "110003",
            "name": "易方达上证50指数A",
            "type": "指数型-股票",
            "risk_level": "中风险",
            "scale": 220.15,
        },
    }
    
    @staticmethod
    async def get_fund_realtime(fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金实时数据
        腾讯财经API: http://qt.gtimg.cn/q=f_161725
        休市时返回None，不展示模拟数据
        """
        # 检查是否开盘
        if not FundAPIService.is_market_open():
            return None
        
        try:
            # 基金代码前缀加 f_
            url = f"{FundAPIService.TENCENT_API}f_{fund_code}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.encoding = 'gbk'
                text = response.text
                
                # 解析返回数据
                # 格式: v_f_161725="1~基金名称~161725~当前净值~昨日净值~...";
                match = re.search(r'v_f_\d+="([^"]+)"', text)
                if match:
                    data = match.group(1).split('~')
                    if len(data) >= 5:
                        # 获取基金信息
                        fund_info = FundAPIService.FUNDS_DB.get(fund_code, {})
                        
                        current = float(data[3]) if data[3] else 0
                        previous = float(data[4]) if data[4] else 0
                        change = current - previous if current and previous else 0
                        change_percent = (change / previous * 100) if previous else 0
                        
                        return {
                            "code": fund_code,
                            "name": fund_info.get("name", data[1]),
                            "current": round(current, 4),
                            "previous_close": round(previous, 4),
                            "change": round(change, 4),
                            "change_percent": round(change_percent, 2),
                            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "net_value_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                        }
                
                # API返回数据无效，返回None
                return None
                
        except Exception as e:
            print(f"获取基金数据失败 {fund_code}: {e}")
            return None
    
    @staticmethod
    async def get_multiple_funds(fund_codes: List[str]) -> List[Dict[str, Any]]:
        """批量获取多个基金数据"""
        # 休市时返回空列表
        if not FundAPIService.is_market_open():
            return []
        
        # 批量查询腾讯API
        try:
            codes_str = ','.join([f"f_{code}" for code in fund_codes])
            url = f"{FundAPIService.TENCENT_API}{codes_str}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.encoding = 'gbk'
                text = response.text
                
                funds = []
                # 解析多行数据
                for line in text.strip().split(';'):
                    if not line.strip():
                        continue
                    match = re.search(r'v_f_(\d+)="([^"]+)"', line)
                    if match:
                        fund_code = match.group(1)
                        data = match.group(2).split('~')
                        if len(data) >= 5:
                            fund_info = FundAPIService.FUNDS_DB.get(fund_code, {})
                            
                            current = float(data[3]) if data[3] else 0
                            previous = float(data[4]) if data[4] else 0
                            change = current - previous if current and previous else 0
                            change_percent = (change / previous * 100) if previous else 0
                            
                            funds.append({
                                "code": fund_code,
                                "name": fund_info.get("name", data[1]),
                                "current": round(current, 4),
                                "previous_close": round(previous, 4),
                                "change": round(change, 4),
                                "change_percent": round(change_percent, 2),
                                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "net_value_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                            })
                
                return funds
                
        except Exception as e:
            print(f"批量获取基金数据失败: {e}")
            return []
    
    @staticmethod
    async def get_fund_history(fund_code: str, period: str = "1d") -> Optional[Dict]:
        """
        获取基金历史数据
        使用腾讯API获取历史净值数据
        """
        try:
            if period == "1d":
                # 开盘时间获取分时数据
                if FundAPIService.is_market_open():
                    return await FundAPIService._get_intraday_data(fund_code)
                else:
                    # 休市时返回空数据，不展示模拟走势
                    return {
                        "fund_code": fund_code,
                        "period": period,
                        "data": [],
                        "previous_close": 0,
                        "market_closed": True
                    }
            
            # 日K、周K、月K等长期数据 - 使用腾讯历史数据API
            return await FundAPIService._get_daily_history(fund_code, period)
            
        except Exception as e:
            print(f"获取基金历史数据失败 {fund_code}: {e}")
            return {
                "fund_code": fund_code,
                "period": period,
                "data": [],
                "previous_close": 0,
                "error": str(e)
            }
    
    @staticmethod
    async def _get_intraday_data(fund_code: str) -> Optional[Dict]:
        """获取分时数据（仅开盘时调用）"""
        try:
            url = f"{FundAPIService.TENCENT_MINUTE_API}f_{fund_code}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                data = response.json()
                
                # 解析分时数据
                fund_data = data.get("data", {}).get(f"f_{fund_code}", {})
                minute_data = fund_data.get("data", {}).get("data", [])
                
                if minute_data:
                    chart_points = []
                    for item in minute_data:
                        # 格式: "0930 1435.00 1770 253995000.00"
                        parts = item.split()
                        if len(parts) >= 2:
                            time_str = parts[0][:2] + ":" + parts[0][2:]  # 0930 -> 09:30
                            price = float(parts[1])
                            chart_points.append({
                                "time": time_str,
                                "value": round(price, 4)
                            })
                    
                    # 获取昨收价
                    previous_close = chart_points[0]["value"] if chart_points else 1.0
                    
                    return {
                        "fund_code": fund_code,
                        "period": "1d",
                        "data": chart_points,
                        "previous_close": previous_close
                    }
                
                return {"fund_code": fund_code, "period": "1d", "data": [], "previous_close": 0}
                
        except Exception as e:
            print(f"获取分时数据失败 {fund_code}: {e}")
            return {"fund_code": fund_code, "period": "1d", "data": [], "previous_close": 0}
    
    @staticmethod
    def _get_market_prefix(fund_code: str) -> str:
        """
        获取基金的市场前缀
        场内基金：15开头是深圳(sz)，50/51开头是上海(sh)
        """
        if fund_code.startswith('15') or fund_code.startswith('16'):
            return 'sz'
        elif fund_code.startswith('50') or fund_code.startswith('51') or fund_code.startswith('52'):
            return 'sh'
        else:
            return 'sz'  # 默认深圳
    
    @staticmethod
    async def _get_daily_history(fund_code: str, period: str) -> Optional[Dict]:
        """
        获取日K/周K/月K历史数据
        使用腾讯K线API: https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=code,period,,,count,qfq
        """
        try:
            # 周期映射
            period_map = {
                "1w": "day",      # 1周用日K显示
                "1m": "day",      # 1月用日K显示  
                "3m": "day",      # 3月用日K显示
                "6m": "day",      # 6月用日K显示
                "1y": "week",     # 1年用周K显示
                "3y": "month",    # 3年用月K显示
            }
            
            # 数据条数映射
            count_map = {
                "1w": 7,
                "1m": 30,
                "3m": 90,
                "6m": 180,
                "1y": 52,    # 52周
                "3y": 36,    # 36个月
            }
            
            kline_period = period_map.get(period, "day")
            count = count_map.get(period, 30)
            
            # 构建市场代码前缀
            market_prefix = FundAPIService._get_market_prefix(fund_code)
            full_code = f"{market_prefix}{fund_code}"
            
            # 腾讯K线API - 使用原型图中的格式
            url = f"{FundAPIService.TENCENT_KLINE_API}?param={full_code},{kline_period},,,{count},qfq"
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                data = response.json()
                
                if data.get("code") != 0:
                    print(f"API返回错误: {data.get('msg')}")
                    return {"fund_code": fund_code, "period": period, "data": [], "previous_close": 0}
                
                # 解析K线数据
                # 数据结构: {"data": {"sz161725": {"qfqday": [["2024-01-15", "开盘", "收盘", "最高", "最低", "成交量"], ...]}}}
                fund_data = data.get("data", {}).get(full_code, {})
                
                # 根据周期获取对应的数据键
                data_key = f"qfq{kline_period}"  # qfqday, qfqweek, qfqmonth
                kline_data = fund_data.get(data_key, [])
                
                if kline_data:
                    chart_points = []
                    for item in kline_data:
                        # 格式: ["2024-01-15", "开盘", "收盘", "最高", "最低", "成交量"]
                        # 注意：腾讯API返回的是 [日期, 开盘, 收盘, 最低, 最高, 成交量]
                        if len(item) >= 5:
                            date_str = item[0]
                            open_price = float(item[1])
                            close_price = float(item[2])
                            low_price = float(item[3])
                            high_price = float(item[4])
                            volume = float(item[5]) if len(item) > 5 else 0
                            
                            chart_points.append({
                                "time": date_str,
                                "open": round(open_price, 4),
                                "high": round(high_price, 4),
                                "low": round(low_price, 4),
                                "close": round(close_price, 4),
                                "volume": round(volume, 2)
                            })
                    
                    # 获取昨收价（最后一条数据的收盘价）
                    previous_close = chart_points[-1]["close"] if chart_points else 0
                    
                    return {
                        "fund_code": fund_code,
                        "period": period,
                        "data": chart_points,
                        "previous_close": previous_close
                    }
                
                # 如果API没有返回数据，返回空数组
                return {"fund_code": fund_code, "period": period, "data": [], "previous_close": 0}
                
        except Exception as e:
            print(f"获取K线数据失败 {fund_code}: {e}")
            return {"fund_code": fund_code, "period": period, "data": [], "previous_close": 0}
    
    @staticmethod
    async def search_funds(keyword: str) -> List[Dict[str, Any]]:
        """搜索基金"""
        results = []
        keyword_lower = keyword.lower()
        
        for code, fund in FundAPIService.FUNDS_DB.items():
            if (keyword_lower in code.lower() or 
                keyword_lower in fund["name"].lower()):
                results.append({
                    "code": code,
                    "name": fund["name"],
                    "pinyin": "",
                    "category": fund["type"]
                })
        
        return results[:20]
    
    @staticmethod
    def get_all_fund_codes() -> List[str]:
        """获取所有基金代码"""
        return list(FundAPIService.FUNDS_DB.keys())


# 常用基金代码列表
DEFAULT_FUND_CODES = FundAPIService.get_all_fund_codes()
