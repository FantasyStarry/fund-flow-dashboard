'use client';

import { useEffect, useState } from 'react';
import { getHoldings, Holding } from '@/lib/api';
import { TrendingUp, TrendingDown, Trash2 } from 'lucide-react';

export default function HoldingsCard() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        const response = await getHoldings();
        if (response.success) {
          setHoldings(response.data);
        }
      } catch (error) {
        console.error('获取持仓失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHoldings();
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-slate-800 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (holdings.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">我的持仓</h3>
        <div className="text-center py-8 text-slate-500">
          暂无持仓，快去添加吧
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">我的持仓</h3>
        <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
          查看全部
        </button>
      </div>

      <div className="space-y-4">
        {holdings.map((holding) => {
          const profit = holding.profit_loss || 0;
          const profitPercent = holding.profit_loss_percent || 0;
          const isProfit = profit >= 0;

          return (
            <div
              key={holding.fund_code}
              className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <div className="flex-1">
                <div className="font-medium text-white">{holding.fund_name}</div>
                <div className="text-sm text-slate-500 mt-1">
                  持有 {holding.shares.toFixed(2)} 份 · 成本 {holding.cost_price.toFixed(4)}
                </div>
              </div>

              <div className="text-right mr-4">
                <div className="font-mono text-white">
                  ¥{(holding.market_value || 0).toFixed(2)}
                </div>
                <div className={`flex items-center gap-1 text-sm ${isProfit ? 'text-red-400' : 'text-emerald-400'}`}>
                  {isProfit ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {isProfit ? '+' : ''}{profitPercent.toFixed(2)}%
                </div>
              </div>

              <button
                className="p-2 text-slate-500 hover:text-red-400 transition-colors"
                title="删除持仓"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>

      {/* 汇总 */}
      <div className="mt-6 pt-4 border-t border-slate-800">
        <div className="flex justify-between text-sm">
          <span className="text-slate-500">总市值</span>
          <span className="font-mono text-white">
            ¥{holdings.reduce((sum, h) => sum + (h.market_value || 0), 0).toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between text-sm mt-2">
          <span className="text-slate-500">总盈亏</span>
          <span className={`font-mono ${
            holdings.reduce((sum, h) => sum + (h.profit_loss || 0), 0) >= 0
              ? 'text-red-400'
              : 'text-emerald-400'
          }`}>
            {holdings.reduce((sum, h) => sum + (h.profit_loss || 0), 0) >= 0 ? '+' : ''}
            ¥{holdings.reduce((sum, h) => sum + (h.profit_loss || 0), 0).toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}
