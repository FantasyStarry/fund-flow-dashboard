"""
中国股市交易日历服务
使用 chinese_calendar 库判断节假日
"""
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Tuple
import chinese_calendar as cc


class MarketCalendarService:
    """中国股市交易日历服务 - 基于 chinese_calendar 库"""
    
    @classmethod
    def is_trading_day(cls, check_date: Optional[date] = None) -> bool:
        """
        判断是否为A股交易日
        
        逻辑：
        1. 如果是法定节假日（如春节、国庆），肯定不开市
        2. 如果是周六或周日，股市不开市（即使调休上班）
        3. 只有周一到周五的非节假日才是交易日
        
        注意：chinese_calendar 的 is_workday 包含了"周末因调休而上班"的日子，
        但股市在调休的周末通常是不开市的。
        
        Args:
            check_date: 要检查的日期，默认为今天
            
        Returns:
            是否为交易日
        """
        if check_date is None:
            check_date = date.today()
        
        # 1. 基础判断：如果是法定节假日，肯定不开市
        if cc.is_holiday(check_date):
            return False
        
        # 2. 周末判断：如果是周六或周日，股市不开市
        # weekday() 返回 0-6，5是周六，6是周日
        if check_date.weekday() >= 5:
            return False
        
        # 3. 剩下的周一到周五非节假日就是交易日
        return True
    
    @classmethod
    def get_trading_day_info(cls, check_date: Optional[date] = None) -> Tuple[bool, str]:
        """
        判断是否为交易日，并返回详细信息
        
        Args:
            check_date: 要检查的日期，默认为今天
            
        Returns:
            (是否为交易日, 说明)
        """
        if check_date is None:
            check_date = date.today()
        
        # 1. 法定节假日判断
        if cc.is_holiday(check_date):
            return False, "法定节假日"
        
        # 2. 周末判断
        if check_date.weekday() >= 5:
            return False, "周末休市"
        
        return True, "交易日"
    
    @classmethod
    def is_market_open(cls, check_datetime: Optional[datetime] = None) -> bool:
        """
        判断市场是否开盘（考虑交易日和交易时间）
        
        Args:
            check_datetime: 要检查的日期时间，默认为现在
            
        Returns:
            市场是否开盘
        """
        if check_datetime is None:
            check_datetime = datetime.now()
        
        # 首先检查是否为交易日
        if not cls.is_trading_day(check_datetime.date()):
            return False
        
        # 检查交易时间
        hour = check_datetime.hour
        minute = check_datetime.minute
        time_in_minutes = hour * 60 + minute
        
        # 上午 9:30-11:30 (570-690分钟)
        morning_session = 570 <= time_in_minutes <= 690
        # 下午 13:00-15:00 (780-900分钟)
        afternoon_session = 780 <= time_in_minutes <= 900
        
        return morning_session or afternoon_session
    
    @classmethod
    def get_last_trading_day(cls, check_date: Optional[date] = None) -> date:
        """
        获取最近一个交易日
        
        Args:
            check_date: 参考日期，默认为今天
            
        Returns:
            最近一个交易日
        """
        if check_date is None:
            check_date = date.today()
        
        # 向前查找最近一个交易日
        current = check_date - timedelta(days=1)
        while not cls.is_trading_day(current):
            current -= timedelta(days=1)
        
        return current
    
    @classmethod
    def get_next_trading_day(cls, check_date: Optional[date] = None) -> date:
        """
        获取下一个交易日
        
        Args:
            check_date: 参考日期，默认为今天
            
        Returns:
            下一个交易日
        """
        if check_date is None:
            check_date = date.today()
        
        # 向后查找下一个交易日
        current = check_date + timedelta(days=1)
        while not cls.is_trading_day(current):
            current += timedelta(days=1)
        
        return current
    
    @classmethod
    def get_market_status(cls, check_datetime: Optional[datetime] = None) -> Dict:
        """
        获取市场状态详情
        
        Args:
            check_datetime: 要检查的日期时间，默认为现在
            
        Returns:
            市场状态信息
        """
        if check_datetime is None:
            check_datetime = datetime.now()
        
        is_open = cls.is_market_open(check_datetime)
        is_trading, reason = cls.get_trading_day_info(check_datetime.date())
        
        status = {
            "is_open": is_open,
            "is_trading_day": is_trading,
            "current_time": check_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        if not is_trading:
            status["reason"] = reason
            status["last_trading_day"] = cls.get_last_trading_day(check_datetime.date()).isoformat()
            status["next_trading_day"] = cls.get_next_trading_day(check_datetime.date()).isoformat()
        elif not is_open:
            status["reason"] = "非交易时间"
            status["trading_hours"] = "9:30-11:30, 13:00-15:00"
        else:
            status["trading_hours"] = "9:30-11:30, 13:00-15:00"
        
        return status


# 便捷函数
def is_market_open() -> bool:
    """判断市场是否开盘"""
    return MarketCalendarService.is_market_open()


def is_trading_day(check_date: Optional[date] = None) -> bool:
    """判断是否为交易日"""
    return MarketCalendarService.is_trading_day(check_date)


def get_market_status() -> Dict:
    """获取市场状态详情"""
    return MarketCalendarService.get_market_status()
