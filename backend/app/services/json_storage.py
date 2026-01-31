import json
import os
import fcntl
from typing import Any, Optional, List
from pathlib import Path
from datetime import datetime


class JSONStorage:
    """JSON文件存储服务 - 带文件锁确保并发安全"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据文件
        self._init_data_files()
    
    def _init_data_files(self):
        """初始化默认数据文件"""
        # 基金列表
        if not self._file_exists("funds.json"):
            self._write_json("funds.json", self._get_default_funds())
        
        # 持仓数据
        if not self._file_exists("holdings.json"):
            self._write_json("holdings.json", self._get_default_holdings())
        
        # 走势图数据
        if not self._file_exists("charts.json"):
            self._write_json("charts.json", self._get_default_charts())
        
        # 资金流向
        if not self._file_exists("flows.json"):
            self._write_json("flows.json", self._get_default_flows())
        
        # 大盘指数
        if not self._file_exists("indices.json"):
            self._write_json("indices.json", self._get_default_indices())
    
    def _file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        return (self.data_dir / filename).exists()
    
    def _get_file_path(self, filename: str) -> Path:
        """获取文件完整路径"""
        return self.data_dir / filename
    
    def _read_json(self, filename: str) -> Any:
        """读取JSON文件（带共享锁）"""
        filepath = self._get_file_path(filename)
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            # 获取共享锁
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _write_json(self, filename: str, data: Any):
        """写入JSON文件（带独占锁）"""
        filepath = self._get_file_path(filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 获取独占锁
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    # ========== 基金数据操作 ==========
    
    def get_all_funds(self) -> List[dict]:
        """获取所有基金列表"""
        return self._read_json("funds.json") or []
    
    def get_fund_by_code(self, code: str) -> Optional[dict]:
        """根据代码获取基金"""
        funds = self.get_all_funds()
        for fund in funds:
            if fund.get("code") == code:
                return fund
        return None
    
    def update_fund_price(self, code: str, price_data: dict) -> bool:
        """更新基金价格"""
        funds = self.get_all_funds()
        for fund in funds:
            if fund.get("code") == code:
                fund["price"] = {**fund.get("price", {}), **price_data}
                fund["price"]["update_time"] = datetime.now().isoformat()
                self._write_json("funds.json", funds)
                return True
        return False
    
    # ========== 持仓数据操作 ==========
    
    def get_holdings_by_fund(self, code: str) -> Optional[dict]:
        """获取基金持仓"""
        holdings = self._read_json("holdings.json") or {}
        return holdings.get(code)
    
    # ========== 走势图数据操作 ==========
    
    def get_chart_data(self, code: str, period: str = "1d") -> Optional[dict]:
        """获取走势图数据"""
        charts = self._read_json("charts.json") or {}
        fund_charts = charts.get(code, {})
        return fund_charts.get(period)
    
    # ========== 资金流向操作 ==========
    
    def get_flow_by_fund(self, code: str) -> Optional[dict]:
        """获取资金流向"""
        flows = self._read_json("flows.json") or {}
        return flows.get(code)
    
    # ========== 大盘指数操作 ==========
    
    def get_market_indices(self) -> List[dict]:
        """获取大盘指数"""
        return self._read_json("indices.json") or []
    
    # ========== 默认数据 ==========
    
    def _get_default_funds(self) -> List[dict]:
        """默认基金数据"""
        return [
            {
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
                    "update_time": datetime.now().isoformat()
                }
            },
            {
                "code": "000001",
                "name": "华夏成长混合",
                "type": "混合型",
                "risk_level": "中高风险",
                "scale": 120.50,
                "price": {
                    "current": 2.8560,
                    "previous_close": 2.8200,
                    "change": 0.0360,
                    "change_percent": 1.28,
                    "update_time": datetime.now().isoformat()
                }
            }
        ]
    
    def _get_default_holdings(self) -> dict:
        """默认持仓数据"""
        return {
            "161725": {
                "fund_code": "161725",
                "holdings": [
                    {"name": "贵州茅台", "price": 1780.50, "change": 1.2, "weight": 15, "contribution": 0.18},
                    {"name": "五粮液", "price": 155.20, "change": 0.8, "weight": 12, "contribution": 0.10},
                    {"name": "泸州老窖", "price": 210.30, "change": -0.5, "weight": 10, "contribution": -0.05},
                    {"name": "山西汾酒", "price": 260.00, "change": 2.1, "weight": 8, "contribution": 0.17},
                    {"name": "洋河股份", "price": 120.50, "change": -1.1, "weight": 6, "contribution": -0.07},
                    {"name": "古井贡酒", "price": 240.10, "change": 0.3, "weight": 5, "contribution": 0.02}
                ],
                "update_time": datetime.now().isoformat()
            }
        }
    
    def _get_default_charts(self) -> dict:
        """默认走势图数据"""
        import random
        
        # 生成模拟分时数据
        base_price = 1.2152
        data_points = []
        for i in range(240):  # 4小时交易时间，每分钟一个点
            base = data_points[-1]["value"] if data_points else base_price
            noise = (random.random() - 0.48) * 0.002
            value = base + noise
            hour = 9 + i // 60
            minute = (i % 60) + 30 if i < 30 else i % 60
            if i >= 120:  # 下午
                hour = 13 + (i - 120) // 60
                minute = (i - 120) % 60
            time_str = f"{hour:02d}:{minute:02d}"
            data_points.append({"time": time_str, "value": round(value, 4)})
        
        return {
            "161725": {
                "1d": {
                    "fund_code": "161725",
                    "period": "1d",
                    "data": data_points,
                    "previous_close": base_price
                }
            }
        }
    
    def _get_default_flows(self) -> dict:
        """默认资金流向数据"""
        return {
            "161725": {
                "fund_code": "161725",
                "sector": "白酒概念",
                "inflow_percent": 65,
                "outflow_percent": 35,
                "details": [
                    {"label": "超大单", "value": 2.5},
                    {"label": "大单", "value": -0.8},
                    {"label": "中单", "value": -1.2},
                    {"label": "小单", "value": -0.5}
                ],
                "update_time": datetime.now().isoformat()
            }
        }
    
    def _get_default_indices(self) -> List[dict]:
        """默认大盘指数"""
        return [
            {
                "name": "上证指数",
                "symbol": "000001",
                "value": 3285.42,
                "change": 16.43,
                "change_percent": 0.50
            },
            {
                "name": "深证成指",
                "symbol": "399001",
                "value": 10520.15,
                "change": 85.32,
                "change_percent": 0.82
            },
            {
                "name": "创业板指",
                "symbol": "399006",
                "value": 2156.78,
                "change": 12.56,
                "change_percent": 0.58
            }
        ]


# 全局存储实例
_storage: Optional[JSONStorage] = None


def get_storage() -> JSONStorage:
    """获取存储实例（单例模式）"""
    global _storage
    if _storage is None:
        _storage = JSONStorage()
    return _storage
