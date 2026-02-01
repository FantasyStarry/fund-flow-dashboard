"""
SQLite数据库服务
存储用户数据：持仓、自选、交易记录等
"""
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


class DatabaseService:
    """异步SQLite数据库服务"""
    
    def __init__(self, db_path: str = "data/fundpro.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """建立数据库连接"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._init_tables()
        return self._connection
    
    async def close(self):
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _init_tables(self):
        """初始化数据表"""
        async with self._connection.execute("""
            CREATE TABLE IF NOT EXISTS user_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT NOT NULL,
                shares REAL DEFAULT 0,           -- 持有份额
                cost_price REAL DEFAULT 0,       -- 成本价
                amount REAL DEFAULT 0,           -- 投资金额
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code)
            )
        """):
            pass
        
        async with self._connection.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code)
            )
        """):
            pass
        
        async with self._connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                type TEXT NOT NULL,              -- BUY/SELL
                shares REAL NOT NULL,            -- 份额
                price REAL NOT NULL,             -- 成交价格
                amount REAL NOT NULL,            -- 成交金额
                fee REAL DEFAULT 0,              -- 手续费
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """):
            pass
        
        # 基金持仓数据表（用于存储基金的重仓股信息）
        async with self._connection.execute("""
            CREATE TABLE IF NOT EXISTS fund_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                stock_code TEXT NOT NULL,        -- 股票代码
                stock_name TEXT NOT NULL,        -- 股票名称
                weight REAL DEFAULT 0,           -- 持仓权重(%)
                quarter TEXT NOT NULL,           -- 季度 (如: 2024年1季度)
                rank INTEGER DEFAULT 0,          -- 持仓排名
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, stock_code, quarter)
            )
        """):
            pass
        
        # 基金板块映射表（基于持仓分析）
        async with self._connection.execute("""
            CREATE TABLE IF NOT EXISTS fund_sector_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL UNIQUE,
                sector_code TEXT NOT NULL,       -- 板块代码 (如: BK0438)
                sector_name TEXT NOT NULL,       -- 板块名称
                confidence REAL DEFAULT 0,       -- 置信度 (0-100)
                match_reason TEXT,               -- 匹配原因
                derived_from TEXT,               -- 来源: holdings/name/static
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """):
            pass
        
        await self._connection.commit()
    
    # ========== 持仓操作 ==========
    
    async def add_holding(self, fund_code: str, fund_name: str, 
                          shares: float, cost_price: float, amount: float) -> bool:
        """添加/更新持仓"""
        try:
            conn = await self.connect()
            
            # 检查是否已存在
            async with conn.execute(
                "SELECT id, shares, amount FROM user_holdings WHERE fund_code = ?",
                (fund_code,)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                # 更新现有持仓（加仓）
                new_shares = row["shares"] + shares
                new_amount = row["amount"] + amount
                new_cost = new_amount / new_shares if new_shares > 0 else 0
                
                await conn.execute(
                    """UPDATE user_holdings 
                       SET shares = ?, cost_price = ?, amount = ?, updated_at = ?
                       WHERE fund_code = ?""",
                    (new_shares, new_cost, new_amount, datetime.now(), fund_code)
                )
            else:
                # 新建持仓
                await conn.execute(
                    """INSERT INTO user_holdings 
                       (fund_code, fund_name, shares, cost_price, amount)
                       VALUES (?, ?, ?, ?, ?)""",
                    (fund_code, fund_name, shares, cost_price, amount)
                )
            
            await conn.commit()
            return True
            
        except Exception as e:
            print(f"添加持仓失败: {e}")
            return False
    
    async def get_holding(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """获取单个持仓"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT * FROM user_holdings WHERE fund_code = ?",
                (fund_code,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"获取持仓失败: {e}")
            return None
    
    async def get_all_holdings(self) -> List[Dict[str, Any]]:
        """获取所有持仓"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT * FROM user_holdings ORDER BY updated_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取持仓列表失败: {e}")
            return []
    
    async def update_holding(self, fund_code: str, 
                             shares: Optional[float] = None,
                             cost_price: Optional[float] = None) -> bool:
        """更新持仓信息"""
        try:
            conn = await self.connect()
            
            updates = []
            params = []
            
            if shares is not None:
                updates.append("shares = ?")
                params.append(shares)
            if cost_price is not None:
                updates.append("cost_price = ?")
                params.append(cost_price)
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now())
                params.append(fund_code)
                
                await conn.execute(
                    f"UPDATE user_holdings SET {', '.join(updates)} WHERE fund_code = ?",
                    params
                )
                await conn.commit()
            
            return True
            
        except Exception as e:
            print(f"更新持仓失败: {e}")
            return False
    
    async def delete_holding(self, fund_code: str) -> bool:
        """删除持仓"""
        try:
            conn = await self.connect()
            await conn.execute(
                "DELETE FROM user_holdings WHERE fund_code = ?",
                (fund_code,)
            )
            await conn.commit()
            return True
        except Exception as e:
            print(f"删除持仓失败: {e}")
            return False
    
    # ========== 自选操作 ==========
    
    async def add_favorite(self, fund_code: str, fund_name: str) -> bool:
        """添加自选"""
        try:
            conn = await self.connect()
            await conn.execute(
                "INSERT OR IGNORE INTO user_favorites (fund_code, fund_name) VALUES (?, ?)",
                (fund_code, fund_name)
            )
            await conn.commit()
            return True
        except Exception as e:
            print(f"添加自选失败: {e}")
            return False
    
    async def remove_favorite(self, fund_code: str) -> bool:
        """移除自选"""
        try:
            conn = await self.connect()
            await conn.execute(
                "DELETE FROM user_favorites WHERE fund_code = ?",
                (fund_code,)
            )
            await conn.commit()
            return True
        except Exception as e:
            print(f"移除自选失败: {e}")
            return False
    
    async def get_favorites(self) -> List[Dict[str, Any]]:
        """获取所有自选"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT * FROM user_favorites ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取自选列表失败: {e}")
            return []
    
    async def is_favorite(self, fund_code: str) -> bool:
        """检查是否已自选"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT 1 FROM user_favorites WHERE fund_code = ?",
                (fund_code,)
            ) as cursor:
                return await cursor.fetchone() is not None
        except Exception as e:
            print(f"检查自选状态失败: {e}")
            return False
    
    # ========== 交易记录 ==========
    
    async def add_transaction(self, fund_code: str, type_: str, 
                              shares: float, price: float, 
                              amount: float, fee: float = 0) -> bool:
        """添加交易记录"""
        try:
            conn = await self.connect()
            await conn.execute(
                """INSERT INTO transactions 
                   (fund_code, type, shares, price, amount, fee)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (fund_code, type_, shares, price, amount, fee)
            )
            await conn.commit()
            return True
        except Exception as e:
            print(f"添加交易记录失败: {e}")
            return False
    
    async def get_transactions(self, fund_code: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易记录"""
        try:
            conn = await self.connect()
            
            if fund_code:
                async with conn.execute(
                    """SELECT * FROM transactions 
                       WHERE fund_code = ? 
                       ORDER BY transaction_date DESC 
                       LIMIT ?""",
                    (fund_code, limit)
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                async with conn.execute(
                    """SELECT * FROM transactions 
                       ORDER BY transaction_date DESC 
                       LIMIT ?""",
                    (limit,)
                ) as cursor:
                    rows = await cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取交易记录失败: {e}")
            return []
    
    # ========== 基金持仓数据操作 ==========
    
    async def save_fund_holdings(self, fund_code: str, holdings: List[Dict[str, Any]], quarter: str) -> bool:
        """保存基金持仓数据"""
        try:
            conn = await self.connect()
            
            # 先删除该季度旧数据
            await conn.execute(
                "DELETE FROM fund_holdings WHERE fund_code = ? AND quarter = ?",
                (fund_code, quarter)
            )
            
            # 插入新数据
            for i, holding in enumerate(holdings):
                await conn.execute(
                    """INSERT INTO fund_holdings 
                       (fund_code, stock_code, stock_name, weight, quarter, rank, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        fund_code,
                        holding.get('stock_code', ''),
                        holding.get('stock_name', ''),
                        holding.get('weight', 0),
                        quarter,
                        i + 1,
                        datetime.now()
                    )
                )
            
            await conn.commit()
            return True
            
        except Exception as e:
            print(f"保存基金持仓失败: {e}")
            return False
    
    async def get_fund_holdings(self, fund_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取基金最新持仓数据"""
        try:
            conn = await self.connect()
            
            # 获取最新季度
            async with conn.execute(
                "SELECT DISTINCT quarter FROM fund_holdings WHERE fund_code = ? ORDER BY quarter DESC LIMIT 1",
                (fund_code,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return []
                latest_quarter = row['quarter']
            
            # 获取该季度的持仓
            async with conn.execute(
                """SELECT * FROM fund_holdings 
                   WHERE fund_code = ? AND quarter = ?
                   ORDER BY rank ASC LIMIT ?""",
                (fund_code, latest_quarter, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"获取基金持仓失败: {e}")
            return []
    
    async def get_fund_holdings_by_quarter(self, fund_code: str, quarter: str) -> List[Dict[str, Any]]:
        """获取基金指定季度的持仓数据"""
        try:
            conn = await self.connect()
            async with conn.execute(
                """SELECT * FROM fund_holdings 
                   WHERE fund_code = ? AND quarter = ?
                   ORDER BY rank ASC""",
                (fund_code, quarter)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"获取基金持仓失败: {e}")
            return []
    
    async def get_all_fund_holdings_summary(self) -> List[Dict[str, Any]]:
        """获取所有基金的持仓摘要（用于管理）"""
        try:
            conn = await self.connect()
            async with conn.execute(
                """SELECT fund_code, quarter, COUNT(*) as stock_count, MAX(updated_at) as last_update
                   FROM fund_holdings 
                   GROUP BY fund_code, quarter
                   ORDER BY last_update DESC"""
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"获取持仓摘要失败: {e}")
            return []
    
    # ========== 基金板块映射操作 ==========
    
    async def save_fund_sector_mapping(self, fund_code: str, sector_code: str, 
                                       sector_name: str, confidence: float = 0,
                                       match_reason: str = "", derived_from: str = "") -> bool:
        """保存基金板块映射"""
        try:
            conn = await self.connect()
            await conn.execute(
                """INSERT OR REPLACE INTO fund_sector_mapping 
                   (fund_code, sector_code, sector_name, confidence, match_reason, derived_from, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fund_code, sector_code, sector_name, confidence, match_reason, derived_from, datetime.now())
            )
            await conn.commit()
            return True
            
        except Exception as e:
            print(f"保存板块映射失败: {e}")
            return False
    
    async def get_fund_sector_mapping(self, fund_code: str) -> Optional[Dict[str, Any]]:
        """获取基金板块映射"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT * FROM fund_sector_mapping WHERE fund_code = ?",
                (fund_code,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            print(f"获取板块映射失败: {e}")
            return None
    
    async def get_all_sector_mappings(self) -> List[Dict[str, Any]]:
        """获取所有板块映射"""
        try:
            conn = await self.connect()
            async with conn.execute(
                "SELECT * FROM fund_sector_mapping ORDER BY updated_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            print(f"获取板块映射列表失败: {e}")
            return []
    
    async def delete_fund_sector_mapping(self, fund_code: str) -> bool:
        """删除基金板块映射"""
        try:
            conn = await self.connect()
            await conn.execute(
                "DELETE FROM fund_sector_mapping WHERE fund_code = ?",
                (fund_code,)
            )
            await conn.commit()
            return True
            
        except Exception as e:
            print(f"删除板块映射失败: {e}")
            return False


# 全局数据库实例
_db: Optional[DatabaseService] = None


async def get_db() -> DatabaseService:
    """获取数据库实例（单例模式）"""
    global _db
    if _db is None:
        _db = DatabaseService()
        await _db.connect()
    return _db
