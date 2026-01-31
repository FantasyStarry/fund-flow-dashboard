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


# 全局数据库实例
_db: Optional[DatabaseService] = None


async def get_db() -> DatabaseService:
    """获取数据库实例（单例模式）"""
    global _db
    if _db is None:
        _db = DatabaseService()
        await _db.connect()
    return _db
