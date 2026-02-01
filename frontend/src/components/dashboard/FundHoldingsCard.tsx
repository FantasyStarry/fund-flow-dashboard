'use client';

import { useEffect, useState } from 'react';
import { fundAPI } from '@/lib/api';

interface Holding {
  stock_code: string;
  stock_name: string;
  weight: number;
  change_percent: number;
  current_price: number;
}

interface FundHoldingsData {
  fund_code: string;
  quarter: string;
  update_time: string;
  holdings: Holding[];
}

interface FundHoldingsCardProps {
  fundCode: string;
}

export default function FundHoldingsCard({ fundCode }: FundHoldingsCardProps) {
  const [data, setData] = useState<FundHoldingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHoldings = async () => {
      try {
        setLoading(true);
        const response = await fundAPI.getFundHoldings(fundCode);
        if (response.data) {
          setData(response.data);
        } else {
          setError('暂无持仓数据');
        }
      } catch (err) {
        setError('获取持仓数据失败');
      } finally {
        setLoading(false);
      }
    };

    fetchHoldings();
  }, [fundCode]);

  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
        <div className="h-5 bg-slate-800 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-slate-800 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="text-sm text-slate-500 text-center py-4">
          {error || '暂无数据'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">
            重仓股实时行情
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {data.quarter} · 前5大持仓
          </p>
        </div>
        <div className="text-xs text-slate-500">
          更新: {data.update_time.split(' ')[1]}
        </div>
      </div>

      {/* 持仓列表 */}
      <div className="space-y-2">
        {data.holdings.map((holding, index) => (
          <div
            key={holding.stock_code}
            className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl hover:bg-slate-800/50 transition-colors"
          >
            {/* 左侧：排名和名称 */}
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-slate-500 w-4">
                {index + 1}
              </span>
              <div>
                <div className="text-sm font-medium text-white">
                  {holding.stock_name}
                </div>
                <div className="text-xs text-slate-500 font-mono">
                  {holding.stock_code}
                </div>
              </div>
            </div>

            {/* 中间：权重 */}
            <div className="text-center">
              <div className="text-xs text-slate-500">权重</div>
              <div className="text-sm font-mono text-slate-300">
                {holding.weight.toFixed(2)}%
              </div>
            </div>

            {/* 右侧：涨跌幅 */}
            <div className="text-right">
              <div className={`text-sm font-mono font-semibold ${
                holding.change_percent > 0 
                  ? 'text-red-400' 
                  : holding.change_percent < 0 
                    ? 'text-emerald-400' 
                    : 'text-slate-400'
              }`}>
                {holding.change_percent > 0 ? '+' : ''}
                {holding.change_percent.toFixed(2)}%
              </div>
              <div className="text-xs text-slate-500 font-mono">
                ¥{holding.current_price.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 数据说明 */}
      <div className="mt-4 pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          * 数据基于基金最新季报持仓，实时行情每3秒更新。
          涨跌幅反映的是当前股价相对昨日收盘价的变化。
        </p>
      </div>
    </div>
  );
}
