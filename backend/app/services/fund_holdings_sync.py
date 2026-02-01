"""
基金持仓数据同步服务
定期从AkShare获取基金持仓并存储到SQLite
"""
import akshare as ak
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from app.services.database import DatabaseService, get_db


class FundHoldingsSyncService:
    """基金持仓同步服务"""
    
    # 同步间隔（默认30天）
    SYNC_INTERVAL_DAYS = 30
    
    def __init__(self, db: DatabaseService = None):
        self.db = db
    
    async def sync_fund_holdings(self, fund_code: str) -> bool:
        """
        同步单个基金的持仓数据
        从AkShare获取并存储到数据库
        """
        try:
            # 检查是否需要同步（基于上次更新时间）
            existing = await self.db.get_fund_holdings(fund_code, limit=1)
            if existing:
                last_update = existing[0].get('updated_at', '')
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    if datetime.now() - last_update_time < timedelta(days=self.SYNC_INTERVAL_DAYS):
                        print(f"基金 {fund_code} 持仓数据较新，跳过同步")
                        return True
            
            print(f"正在同步基金 {fund_code} 的持仓数据...")
            
            # 从AkShare获取持仓数据
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date="2024")
            
            if df.empty:
                print(f"基金 {fund_code} 无持仓数据")
                return False
            
            # 获取最新季度
            latest_quarter = df.iloc[0]['季度']
            latest_df = df[df['季度'] == latest_quarter]
            
            # 转换为存储格式
            holdings = []
            for _, row in latest_df.iterrows():
                holdings.append({
                    'stock_code': str(row['股票代码']).zfill(6),
                    'stock_name': row['股票名称'],
                    'weight': float(row['占净值比例'])
                })
            
            # 保存到数据库
            success = await self.db.save_fund_holdings(fund_code, holdings, latest_quarter)
            
            if success:
                print(f"基金 {fund_code} 持仓数据同步成功，共 {len(holdings)} 只股票，季度: {latest_quarter}")
            else:
                print(f"基金 {fund_code} 持仓数据已存在或保存失败")
            
            # 分析板块映射（无论保存是否成功都执行，因为数据可能已经存在）
            await self._analyze_and_save_sector_mapping(fund_code, holdings)
            
            return True  # 只要获取到数据就算成功
            
        except Exception as e:
            print(f"同步基金 {fund_code} 持仓失败: {e}")
            return False
    
    async def sync_multiple_funds(self, fund_codes: List[str]) -> Dict[str, bool]:
        """
        批量同步多个基金的持仓数据
        """
        results = {}
        
        for fund_code in fund_codes:
            success = await self.sync_fund_holdings(fund_code)
            results[fund_code] = success
            
            # 添加延迟避免请求过快
            await asyncio.sleep(0.5)
        
        return results
    
    async def _analyze_and_save_sector_mapping(self, fund_code: str, holdings: List[Dict[str, Any]]):
        """
        分析基金持仓并保存板块映射
        基于股票代码前缀和行业特征进行简单映射
        """
        try:
            # 简单的板块映射规则（基于股票代码和行业）
            sector_keywords = {
                'BK0438': {  # 食品饮料
                    'keywords': ['酒', '饮料', '食品', '乳业', '牧原', '温氏'],
                    'codes': ['600519', '000858', '002304', '600809', '000568', '600887']
                },
                'BK1040': {  # 中药
                    'keywords': ['医药', '医疗', '药业', '生物', '复星', '恒瑞'],
                    'codes': ['600276', '600196', '000538', '600332']
                },
                'BK1033': {  # 电池
                    'keywords': ['锂', '电池', '新能源', '光伏', '宁德', '比亚迪'],
                    'codes': ['300750', '002594', '601012', '600438']
                },
                'BK1044': {  # 生物制品
                    'keywords': ['芯片', '半导体', '电子', '中芯', '韦尔'],
                    'codes': ['688981', '603501', '002371']
                },
                'BK0736': {  # 银行
                    'keywords': ['银行', '招商', '平安', '兴业'],
                    'codes': ['600036', '000001', '601166']
                },
                'BK0737': {  # 证券
                    'keywords': ['证券', '中信', '华泰', '东方财富'],
                    'codes': ['600030', '601688', '300059']
                }
            }
            
            # 统计各板块匹配度
            sector_scores = {}
            
            for holding in holdings:
                stock_code = holding['stock_code']
                stock_name = holding['stock_name']
                weight = holding['weight']
                
                for sector_code, sector_info in sector_keywords.items():
                    # 检查股票代码匹配
                    if any(code in stock_code for code in sector_info['codes']):
                        sector_scores[sector_code] = sector_scores.get(sector_code, 0) + weight
                    
                    # 检查名称关键词匹配
                    if any(keyword in stock_name for keyword in sector_info['keywords']):
                        sector_scores[sector_code] = sector_scores.get(sector_code, 0) + weight * 0.5
            
            # 找出得分最高的板块
            if sector_scores:
                best_sector = max(sector_scores.items(), key=lambda x: x[1])
                sector_code = best_sector[0]
                score = best_sector[1]
                
                # 板块名称映射
                sector_names = {
                    'BK0438': '食品饮料',
                    'BK1040': '中药',
                    'BK1033': '电池',
                    'BK1044': '生物制品',
                    'BK0736': '银行',
                    'BK0737': '证券'
                }
                
                sector_name = sector_names.get(sector_code, '其他')
                confidence = min(95, max(60, score * 1.2))
                
                # 保存板块映射
                await self.db.save_fund_sector_mapping(
                    fund_code=fund_code,
                    sector_code=sector_code,
                    sector_name=sector_name,
                    confidence=confidence,
                    match_reason=f"基于持仓分析，前10大持仓中{score:.1f}%匹配该板块",
                    derived_from='holdings'
                )
                
                print(f"基金 {fund_code} 板块映射: {sector_name} (置信度: {confidence:.1f}%)")
            
        except Exception as e:
            print(f"分析基金 {fund_code} 板块映射失败: {e}")
    
    async def get_holdings_with_quotes(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """
        获取基金持仓及实时行情
        优先从数据库获取持仓，然后获取实时股价
        """
        from app.services.fund_realtime_estimate import FundRealtimeEstimateService
        
        # 1. 从数据库获取持仓
        holdings = await self.db.get_fund_holdings(fund_code, limit=5)
        
        if not holdings:
            # 数据库中没有，尝试同步
            success = await self.sync_fund_holdings(fund_code)
            if success:
                holdings = await self.db.get_fund_holdings(fund_code, limit=5)
        
        if not holdings:
            return None
        
        # 2. 获取实时行情
        service = FundRealtimeEstimateService()
        stock_codes = [h['stock_code'] for h in holdings]
        quotes = await service.get_stock_quotes(stock_codes)
        
        # 3. 合并数据
        result_holdings = []
        for holding in holdings:
            quote = quotes.get(holding['stock_code'])
            result_holdings.append({
                'stock_code': holding['stock_code'],
                'stock_name': holding['stock_name'],
                'weight': holding['weight'],
                'change_percent': quote.change_percent if quote else 0,
                'current_price': quote.current_price if quote else 0
            })
        
        return {
            'fund_code': fund_code,
            'quarter': holdings[0].get('quarter', ''),
            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'holdings': result_holdings
        }


# 便捷函数
async def sync_fund_holdings(fund_code: str, db: DatabaseService = None) -> bool:
    """同步单个基金持仓"""
    if db is None:
        db = await get_db()
    service = FundHoldingsSyncService(db)
    return await service.sync_fund_holdings(fund_code)


async def get_fund_holdings_with_quotes(fund_code: str, db: DatabaseService = None) -> Optional[Dict[str, Any]]:
    """获取基金持仓及实时行情"""
    if db is None:
        db = await get_db()
    service = FundHoldingsSyncService(db)
    return await service.get_holdings_with_quotes(fund_code)


# 测试
if __name__ == "__main__":
    async def test():
        db = await get_db()
        service = FundHoldingsSyncService(db)
        
        # 测试同步白酒基金
        print("=" * 50)
        print("测试同步基金: 161725 (招商中证白酒)")
        print("=" * 50)
        
        # 同步持仓
        success = await service.sync_fund_holdings("161725")
        print(f"\n同步结果: {'成功' if success else '失败'}")
        
        # 获取持仓及行情
        result = await service.get_holdings_with_quotes("161725")
        if result:
            print(f"\n持仓季度: {result['quarter']}")
            print(f"\n前5大重仓股实时行情:")
            for h in result['holdings']:
                change = h['change_percent']
                symbol = "📈" if change > 0 else "📉" if change < 0 else "➖"
                print(f"  {symbol} {h['stock_name']}: {change:+.2f}% (权重{h['weight']}%)")
        
        await db.close()
    
    asyncio.run(test())
