'use client';

import { Fund } from '@/lib/api';

interface FundHeaderCardProps {
  fund: Fund | null;
}

export default function FundHeaderCard({ fund }: FundHeaderCardProps) {
  if (!fund) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
        <div className="h-8 bg-slate-800 rounded w-1/3 mb-4" />
        <div className="h-6 bg-slate-800 rounded w-1/4" />
      </div>
    );
  }

  // 休市状态（有数据但市场关闭）
  const isMarketClosed = fund.market_closed && fund.current > 0;
  // 无数据状态
  const hasNoData = fund.current === 0;

  const isUp = fund.change >= 0;
  const colorClass = isUp ? 'text-red-400' : 'text-emerald-400';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* 基金信息 */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-xl md:text-2xl font-bold text-white">{fund.name}</h1>
            <span className="px-2 py-1 bg-slate-800 rounded-lg text-sm font-mono text-slate-400">
              {fund.code}
            </span>
            {isMarketClosed && (
              <span className="px-2 py-1 bg-slate-700/50 rounded-lg text-sm text-slate-400 border border-slate-600/50 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                休市
              </span>
            )}
          </div>
          <div className="text-sm text-slate-500">
            指数型-股票 · 高风险 · 规模 485.23亿
          </div>
        </div>

        {/* 价格信息 */}
        <div className="text-left md:text-right">
          {hasNoData ? (
            <div className="text-3xl md:text-4xl font-bold font-mono text-slate-500">
              --
            </div>
          ) : (
            <>
              <div className={`text-3xl md:text-4xl font-bold font-mono ${colorClass}`}>
                {fund.current.toFixed(4)}
              </div>
              <div className="flex items-center gap-2 mt-1 md:justify-end">
                <span className={`text-lg font-semibold ${colorClass}`}>
                  {isUp ? '+' : ''}{fund.change_percent.toFixed(2)}%
                </span>
                <span className={`text-sm ${colorClass}`}>
                  ({isUp ? '+' : ''}{fund.change.toFixed(4)})
                </span>
              </div>
            </>
          )}
          <div className="text-xs text-slate-500 mt-1">
            {isMarketClosed 
              ? `上个交易日: ${fund.net_value_date}` 
              : hasNoData 
                ? '市场休市' 
                : `估值时间: ${fund.update_time}`
            }
          </div>
        </div>
      </div>
    </div>
  );
}
