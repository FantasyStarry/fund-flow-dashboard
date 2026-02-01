'use client';

import { useFundHoldings } from '@/lib/useFundData';
import { FundHoldingsSkeleton } from '@/components/ui/Skeleton';

interface FundHoldingsCardProps {
  fundCode: string;
}

export default function FundHoldingsCard({ fundCode }: FundHoldingsCardProps) {
  const { holdingsData, isLoading, error } = useFundHoldings(fundCode);

  if (isLoading) {
    return <FundHoldingsSkeleton />;
  }

  if (error || !holdingsData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="text-sm text-slate-500 text-center py-4">
          {error ? '获取持仓数据失败' : '暂无数据'}
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
            {holdingsData.quarter} · 前5大持仓
          </p>
        </div>
        <div className="text-xs text-slate-500">
          更新: {holdingsData.update_time.split(' ')[1]}
        </div>
      </div>

      {/* 持仓列表 */}
      <div className="space-y-2">
        {holdingsData.holdings.map((holding, index) => (
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
