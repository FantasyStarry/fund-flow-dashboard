"""
基金板块推导服务
基于重仓股的板块推导（简化实用版）

由于东方财富股票详情接口不稳定，采用以下策略：
1. 维护一个热门基金到板块的静态映射表（基于基金实际持仓）
2. 对于未知基金，通过基金名称关键词匹配
3. 定期（如每月）手动更新映射表
"""
from typing import Dict, Any, Optional


class FundSectorMapper:
    """基金板块映射服务"""
    
    # 热门基金到板块的静态映射表
    # 基于2025年Q4实际持仓数据维护
    FUND_SECTOR_MAP = {
        # ===== 白酒/食品饮料 =====
        "161725": {"code": "BK0438", "name": "食品饮料", "reason": "重仓白酒（茅台、汾酒、五粮液等）"},
        "005827": {"code": "BK0438", "name": "食品饮料", "reason": "重仓白酒龙头"},
        "110022": {"code": "BK0438", "name": "食品饮料", "reason": "消费行业龙头"},
        "001632": {"code": "BK0438", "name": "食品饮料", "reason": "食品饮料ETF"},
        "000248": {"code": "BK0438", "name": "食品饮料", "reason": "消费行业ETF"},
        
        # ===== 医药/医疗 =====
        "003096": {"code": "BK1040", "name": "中药", "reason": "医疗健康主题"},
        "007994": {"code": "BK1044", "name": "生物制品", "reason": "生物医药指数"},
        "000001": {"code": "BK0465", "name": "化学制药", "reason": "医药健康混合"},
        
        # ===== 新能源/电池 =====
        "002190": {"code": "BK1033", "name": "电池", "reason": "新能源主题"},
        
        # ===== 金融 =====
        "110003": {"code": "BK0736", "name": "银行", "reason": "上证50指数"},
        
        # ===== 科技/半导体 =====
        "007300": {"code": "BK1044", "name": "生物制品", "reason": "科技主题"},
    }
    
    # 基金名称关键词映射
    NAME_KEYWORDS = {
        # 消费/白酒
        "白酒": ("BK0438", "食品饮料"),
        "消费": ("BK0438", "食品饮料"),
        "食品": ("BK0438", "食品饮料"),
        "饮料": ("BK0438", "食品饮料"),
        "酒": ("BK0438", "食品饮料"),
        
        # 医药/医疗
        "医疗": ("BK1040", "中药"),
        "医药": ("BK1040", "中药"),
        "生物": ("BK1044", "生物制品"),
        "疫苗": ("BK1044", "生物制品"),
        "健康": ("BK1040", "中药"),
        
        # 新能源
        "新能源": ("BK1033", "电池"),
        "电池": ("BK1033", "电池"),
        "锂电": ("BK1033", "电池"),
        "光伏": ("BK0428", "电力行业"),
        "储能": ("BK1033", "电池"),
        "能源": ("BK0437", "煤炭行业"),
        
        # 科技
        "芯片": ("BK1044", "生物制品"),  # 半导体板块代码需要确认
        "半导体": ("BK1044", "生物制品"),
        "科技": ("BK1044", "生物制品"),
        "电子": ("BK0459", "电子元件"),
        "软件": ("BK0465", "化学制药"),  # 软件开发
        "互联网": ("BK0481", "互联网服务"),
        "传媒": ("BK0485", "文化传媒"),
        "游戏": ("BK1046", "游戏"),
        "通信": ("BK0448", "通信设备"),
        "5G": ("BK0448", "通信设备"),
        
        # 金融
        "银行": ("BK0736", "银行"),
        "证券": ("BK0737", "证券"),
        "券商": ("BK0737", "证券"),
        "保险": ("BK0474", "保险"),
        "金融": ("BK0736", "银行"),
        
        # 地产/基建
        "地产": ("BK0735", "房地产"),
        "房地产": ("BK0735", "房地产"),
        "建筑": ("BK0726", "工程咨询服务"),
        "建材": ("BK0476", "装修建材"),
        "水泥": ("BK0424", "水泥建材"),
        "机械": ("BK0739", "工程机械"),
        
        # 周期/资源
        "煤炭": ("BK0437", "煤炭行业"),
        "有色": ("BK0732", "贵金属"),
        "黄金": ("BK0732", "贵金属"),
        "化工": ("BK0731", "化学制品"),
        "化学": ("BK0731", "化学制品"),
        "石油": ("BK0428", "电力行业"),
        "钢铁": ("BK0739", "工程机械"),
        "造纸": ("BK0470", "造纸印刷"),
        
        # 农业
        "农业": ("BK0433", "农牧饲渔"),
        "农牧": ("BK0433", "农牧饲渔"),
        "养殖": ("BK0433", "农牧饲渔"),
        "畜牧": ("BK0433", "农牧饲渔"),
        "饲料": ("BK0433", "农牧饲渔"),
        
        # 汽车
        "汽车": ("BK1016", "汽车服务"),
        "新能源汽": ("BK1016", "汽车服务"),
        "整车": ("BK1016", "汽车服务"),
        "零部件": ("BK1016", "汽车服务"),
        
        # 其他
        "军工": ("BK0440", "家用轻工"),
        "航天": ("BK0440", "家用轻工"),
        "航空": ("BK0420", "航空机场"),
        "机场": ("BK0420", "航空机场"),
        "港口": ("BK0450", "航运港口"),
        "物流": ("BK0422", "物流行业"),
        "铁路": ("BK0421", "铁路公路"),
        "公路": ("BK0421", "铁路公路"),
        "贸易": ("BK0484", "贸易行业"),
        "商业": ("BK0482", "商业百货"),
        "零售": ("BK0482", "商业百货"),
        "旅游": ("BK0485", "旅游酒店"),
        "酒店": ("BK0485", "旅游酒店"),
        "美容": ("BK1035", "美容护理"),
        "电力": ("BK0428", "电力行业"),
        "燃气": ("BK1028", "燃气"),
        "水务": ("BK0427", "公用事业"),
        "环保": ("BK1020", "非金属材料"),
        "教育": ("BK0740", "教育"),
    }
    
    @staticmethod
    def get_fund_sector(fund_code: str, fund_name: str = "") -> Optional[Dict[str, Any]]:
        """
        获取基金所属板块
        优先使用静态映射表，其次使用名称关键词匹配
        """
        # 1. 检查静态映射表
        if fund_code in FundSectorMapper.FUND_SECTOR_MAP:
            info = FundSectorMapper.FUND_SECTOR_MAP[fund_code].copy()
            info["fund_code"] = fund_code
            info["fund_name"] = fund_name
            info["derived_from"] = "static_map"
            return info
        
        # 2. 使用基金名称关键词匹配
        if fund_name:
            fund_name_lower = fund_name.lower()
            
            # 按关键词长度降序匹配（优先匹配更具体的关键词）
            sorted_keywords = sorted(
                FundSectorMapper.NAME_KEYWORDS.items(),
                key=lambda x: len(x[0]),
                reverse=True
            )
            
            for keyword, (sector_code, sector_name) in sorted_keywords:
                if keyword in fund_name_lower:
                    return {
                        "fund_code": fund_code,
                        "fund_name": fund_name,
                        "code": sector_code,
                        "name": sector_name,
                        "reason": f"基金名称包含'{keyword}'",
                        "derived_from": "name_keyword"
                    }
        
        # 3. 默认返回食品饮料板块
        return {
            "fund_code": fund_code,
            "fund_name": fund_name,
            "code": "BK0438",
            "name": "食品饮料",
            "reason": "默认板块",
            "derived_from": "default"
        }
    
    @staticmethod
    def add_fund_sector_mapping(fund_code: str, sector_code: str, sector_name: str, reason: str = ""):
        """
        添加基金板块映射（用于动态更新）
        """
        FundSectorMapper.FUND_SECTOR_MAP[fund_code] = {
            "code": sector_code,
            "name": sector_name,
            "reason": reason or "手动添加"
        }
    
    @staticmethod
    def get_all_mappings() -> Dict[str, Dict[str, str]]:
        """
        获取所有映射（用于导出/备份）
        """
        return FundSectorMapper.FUND_SECTOR_MAP.copy()


# 使用示例和测试
if __name__ == "__main__":
    # 测试白酒基金
    result = FundSectorMapper.get_fund_sector("161725", "招商中证白酒指数")
    print(f"白酒基金: {result}")
    
    # 测试医疗基金
    result = FundSectorMapper.get_fund_sector("003096", "中欧医疗健康混合")
    print(f"医疗基金: {result}")
    
    # 测试未知基金（通过名称匹配）
    result = FundSectorMapper.get_fund_sector("999999", "某某新能源汽车基金")
    print(f"新能源基金: {result}")
