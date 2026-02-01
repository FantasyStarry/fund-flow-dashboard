"""
板块资金流向服务
从东方财富网获取真实板块资金流向数据
"""
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.services.fund_sector_mapper import FundSectorMapper


class SectorFlowService:
    """板块资金流向服务 - 东方财富API"""
    
    # 东方财富API
    SECTOR_LIST_API = "https://push2.eastmoney.com/api/qt/clist/get"
    SECTOR_DETAIL_API = "https://push2.eastmoney.com/api/qt/stock/get"
    
    # 板块代码映射（常用板块）
    SECTOR_MAP = {
        "BK0477": "白酒",
        "BK0433": "农牧饲渔",
        "BK1033": "电池",
        "BK0428": "新能源",
        "BK0484": "贸易行业",
        "BK0730": "农药兽药",
        "BK0474": "保险",
        "BK0733": "包装材料",
        "BK0546": "玻璃玻纤",
        "BK1016": "汽车服务",
        "BK0427": "公用事业",
        "BK0739": "工程机械",
        "BK0726": "工程咨询服务",
        "BK0421": "铁路公路",
        "BK0440": "家用轻工",
        "BK0420": "航空机场",
        "BK1035": "美容护理",
        "BK0448": "通信设备",
        "BK1046": "游戏",
        "BK0437": "煤炭行业",
        "BK0470": "造纸印刷",
        "BK0731": "化学制品",
        "BK0732": "化学原料",
        "BK1015": "医疗器械",
        "BK1044": "半导体",
        "BK0459": "电子元件",
        "BK0465": "软件开发",
        "BK0481": "互联网服务",
        "BK0485": "文化传媒",
        "BK0735": "房地产",
        "BK0736": "银行",
        "BK0737": "证券",
    }
    
    # 基金与板块映射关系（根据基金名称/类型智能匹配）
    # 注意：使用实际可获取的行业板块代码
    FUND_SECTOR_MAP = {
        # 白酒/消费类基金 -> 食品饮料板块
        "161725": {"code": "BK0438", "name": "食品饮料", "reason": "重仓白酒股"},
        "005827": {"code": "BK0438", "name": "食品饮料", "reason": "重仓白酒龙头"},
        "110022": {"code": "BK0438", "name": "食品饮料", "reason": "消费行业龙头"},
        "001632": {"code": "BK0438", "name": "食品饮料", "reason": "食品饮料ETF"},
        "000248": {"code": "BK0438", "name": "食品饮料", "reason": "消费行业ETF"},
        
        # 医疗/医药类基金 -> 中药/生物制品/化学制药板块
        "003096": {"code": "BK1040", "name": "中药", "reason": "医疗健康主题"},
        "007994": {"code": "BK1044", "name": "生物制品", "reason": "生物医药指数"},
        
        # 新能源/电池类基金
        "002190": {"code": "BK1033", "name": "电池", "reason": "新能源主题"},
        
        # 科技/半导体类基金
        "000001": {"code": "BK1044", "name": "半导体", "reason": "科技成长混合"},
        
        # 金融类基金
        "110003": {"code": "BK0736", "name": "银行", "reason": "上证50指数"},
    }
    
    @staticmethod
    def format_money_yi(value: float) -> float:
        """
        将金额转换为亿为单位
        """
        return round(value / 100000000, 2)
    
    @staticmethod
    async def get_sector_list() -> List[Dict[str, Any]]:
        """
        获取板块列表及资金流向（行业板块）
        """
        try:
            params = {
                "fid": "f62",  # 按主力净流入排序
                "po": 1,       # 排序方向
                "pz": 50,      # 每页数量
                "pn": 1,       # 页码
                "np": 1,
                "fltt": 2,
                "invt": 2,
                "fs": "m:90+t:2",  # 行业板块
                "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124"
            }
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(SectorFlowService.SECTOR_LIST_API, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("rc") != 0:
                    print(f"获取板块列表失败: {data}")
                    return []
                
                sectors = []
                diff = data.get("data", {}).get("diff", [])
                
                for item in diff:
                    sector_code = item.get("f12", "")
                    sector_name = item.get("f14", "")
                    main_inflow = item.get("f62", 0) or 0  # 主力净流入（元）
                    
                    if sector_code and sector_name:
                        # 转换为亿
                        main_inflow_yi = SectorFlowService.format_money_yi(main_inflow)
                        super_large = item.get("f66", 0) or 0
                        large = item.get("f72", 0) or 0
                        medium = item.get("f78", 0) or 0
                        small = item.get("f84", 0) or 0
                        
                        sectors.append({
                            "code": sector_code,
                            "name": sector_name,
                            "price": item.get("f2", 0),
                            "change_percent": item.get("f3", 0),
                            "main_inflow": main_inflow_yi,
                            "main_inflow_percent": item.get("f184", 0),
                            "super_large_inflow": SectorFlowService.format_money_yi(super_large),
                            "super_large_percent": item.get("f69", 0),
                            "large_inflow": SectorFlowService.format_money_yi(large),
                            "large_percent": item.get("f75", 0),
                            "medium_inflow": SectorFlowService.format_money_yi(medium),
                            "medium_percent": item.get("f81", 0),
                            "small_inflow": SectorFlowService.format_money_yi(small),
                            "small_percent": item.get("f87", 0),
                        })
                
                return sectors
                
        except Exception as e:
            print(f"获取板块列表异常: {e}")
            return []
    
    @staticmethod
    async def get_sector_detail(sector_code: str = "BK0477") -> Optional[Dict[str, Any]]:
        """
        获取单个板块的详细信息
        """
        try:
            params = {
                "secid": f"90.{sector_code}",
                "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f59,f60,f62,f71,f78,f80"
            }
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(SectorFlowService.SECTOR_DETAIL_API, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("rc") != 0:
                    print(f"获取板块详情失败: {data}")
                    return None
                
                d = data.get("data", {})
                
                return {
                    "code": sector_code,
                    "name": d.get("f58", SectorFlowService.SECTOR_MAP.get(sector_code, "未知板块")),
                    "price": d.get("f43", 0),
                    "change": d.get("f44", 0),
                    "change_percent": d.get("f45", 0),
                }
                
        except Exception as e:
            print(f"获取板块详情异常: {e}")
            return None
    
    @staticmethod
    async def get_sector_flow_detail(sector_code: str = "BK0477") -> Optional[Dict[str, Any]]:
        """
        获取单个板块的详细资金流向
        使用板块列表接口获取（分时接口不可用）
        """
        try:
            # 获取所有板块列表，然后筛选出目标板块
            sectors = await SectorFlowService.get_sector_list()
            
            target_sector = None
            for sector in sectors:
                if sector["code"] == sector_code:
                    target_sector = sector
                    break
            
            if not target_sector:
                print(f"未找到板块: {sector_code}")
                return None
            
            # 计算流入流出比例
            main_inflow = target_sector["main_inflow"]
            super_large = target_sector["super_large_inflow"]
            large = target_sector["large_inflow"]
            medium = target_sector["medium_inflow"]
            small = target_sector["small_inflow"]
            
            # 计算流入流出比例（基于主力净流入）
            if main_inflow >= 0:
                inflow_percent = min(100, max(50, 50 + abs(main_inflow) * 2))
                outflow_percent = 100 - inflow_percent
            else:
                outflow_percent = min(100, max(50, 50 + abs(main_inflow) * 2))
                inflow_percent = 100 - outflow_percent
            
            return {
                "sector_code": sector_code,
                "sector_name": target_sector["name"],
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "inflow_percent": round(inflow_percent, 1),
                "outflow_percent": round(outflow_percent, 1),
                "main_net": main_inflow,
                "details": [
                    {"label": "超大单", "value": super_large},
                    {"label": "大单", "value": large},
                    {"label": "中单", "value": medium},
                    {"label": "小单", "value": small},
                ]
            }
                
        except Exception as e:
            print(f"获取板块资金流向异常: {e}")
            return None
    
    @staticmethod
    async def get_sector_flow_by_fund(fund_code: str, fund_name: str = "") -> Optional[Dict[str, Any]]:
        """
        根据基金代码获取相关板块的资金流向
        使用基金板块映射服务（静态映射表 + 名称关键词匹配）
        """
        # 获取基金所属板块
        sector_info = FundSectorMapper.get_fund_sector(fund_code, fund_name)
        
        if not sector_info:
            # 默认使用食品饮料板块
            sector_info = {
                "code": "BK0438",
                "name": "食品饮料",
                "reason": "默认板块",
                "derived_from": "default"
            }
        
        sector_code = sector_info["code"]
        
        # 获取板块资金流向
        flow_data = await SectorFlowService.get_sector_flow_detail(sector_code)
        
        if flow_data:
            flow_data["match_reason"] = sector_info.get("reason", "")
            flow_data["fund_sector_name"] = sector_info.get("name", "")
            flow_data["derived_from"] = sector_info.get("derived_from", "unknown")
        
        return flow_data
    
    @staticmethod
    async def get_top_sectors(limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取资金净流入/流出最多的板块
        """
        sectors = await SectorFlowService.get_sector_list()
        
        # 按主力净流入排序（正数流入，负数流出）
        sectors.sort(key=lambda x: x["main_inflow"], reverse=True)
        
        return sectors[:limit]
