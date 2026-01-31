'use client';

import { FundFlow } from '@/lib/api';
import { useEffect, useState } from 'react';

interface FlowCardProps {
  flow: FundFlow | null;
  onRefresh?: () => void;
}

// 格式化刷新间隔
function formatRefreshInterval(seconds: number): string {
  if (seconds >= 3600) {
    return `${Math.floor(seconds / 3600)}小时`;
  } else if (seconds >= 60) {
    return `${Math.floor(seconds / 60)}分钟`;
  }
  return `${seconds}秒`;
}

export default function FlowCard({ flow, onRefresh }: FlowCardProps) {
  const [countdown, setCountdown] = useState<number>(0);
  
  // 建议刷新间隔（默认15分钟）
  const refreshInterval = flow?.refresh_interval || 900;

  useEffect(() => {
    if (!flow) return;
    
    // 初始化倒计时
    setCountdown(refreshInterval);
    
    // 每秒更新倒计时
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          // 倒计时结束，可以触发刷新
          return refreshInterval;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [flow, refreshInterval]);

  if (!flow) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
        <div className="h-6 bg-slate-800 rounded w-1/3 mb-4" />
        <div className="h-8 bg-slate-800 rounded mb-4" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-slate-800 rounded" />
          ))}
        </div>
      </div>
    );
  }

  // 判断主力净流入方向（A股习惯：红色流入，绿色流出）
  const isMainInflow = (flow.main_net || 0) >= 0;
  
  // 格式化倒计时显示
  const formatCountdown = (sec: number): string => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">
            板块资金流向 ({flow.sector})
          </h3>
          {flow.match_reason && (
            <p className="text-xs text-slate-500 mt-1">
              关联原因：{flow.match_reason}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {flow.update_time && flow.update_time !== '--' && (
            <span className="text-xs text-slate-500">
              数据时间: {flow.update_time}
            </span>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-full">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>每{formatRefreshInterval(refreshInterval)}刷新</span>
            <span className="text-slate-500">({formatCountdown(countdown)})</span>
            {onRefresh && (
              <button 
                onClick={onRefresh}
                className="ml-1 text-blue-400 hover:text-blue-300 transition-colors"
                title="立即刷新"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 主力净流入金额 */}
      <div className="mb-6 p-4 bg-slate-800/30 rounded-xl">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm text-slate-400">主力净流入</span>
            <div className={`text-3xl font-bold font-mono mt-1 ${
              isMainInflow ? 'text-red-400' : 'text-emerald-400'
            }`}>
              {isMainInflow ? '+' : ''}{flow.main_net?.toFixed(2) || '0.00'}亿
            </div>
          </div>
          <div className={`px-4 py-2 rounded-lg ${
            isMainInflow ? 'bg-red-400/10 text-red-400' : 'bg-emerald-400/10 text-emerald-400'
          }`}>
            <div className="text-xs opacity-70">资金流向</div>
            <div className="font-semibold">{isMainInflow ? '流入' : '流出'}</div>
          </div>
        </div>
      </div>

      {/* 资金流向条形图 */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-slate-400 mb-2">
          <span>资金流入占比</span>
          <span>资金流出占比</span>
        </div>
        <div className="h-10 bg-slate-800 rounded-full overflow-hidden flex">
          <div
            className="bg-gradient-to-r from-red-500 to-red-400 flex items-center justify-center text-white text-sm font-semibold transition-all duration-500"
            style={{ width: `${flow.inflow_percent}%` }}
          >
            {flow.inflow_percent > 12 && `${flow.inflow_percent}%`}
          </div>
          <div
            className="bg-gradient-to-r from-emerald-400 to-emerald-500 flex items-center justify-center text-white text-sm font-semibold transition-all duration-500"
            style={{ width: `${flow.outflow_percent}%` }}
          >
            {flow.outflow_percent > 12 && `${flow.outflow_percent}%`}
          </div>
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-xs text-red-400">流入 {flow.inflow_percent}%</span>
          <span className="text-xs text-emerald-400">流出 {flow.outflow_percent}%</span>
        </div>
      </div>

      {/* 详细数据 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {flow.details.map((item) => (
          <div key={item.label} className="bg-slate-800/50 rounded-xl p-4">
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
              {item.label}
            </div>
            <div className={`font-mono font-semibold ${
              item.value >= 0 ? 'text-red-400' : 'text-emerald-400'
            }`}>
              {item.value >= 0 ? '+' : ''}{item.value.toFixed(2)}亿
            </div>
          </div>
        ))}
      </div>

      {/* 数据说明 */}
      <div className="mt-4 pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500">
          * 数据来源：东方财富网，数据每{formatRefreshInterval(refreshInterval)}自动刷新一次。
          超大单：单笔100万以上；大单：单笔20-100万；中单：单笔4-20万；小单：单笔4万以下。
        </p>
      </div>
    </div>
  );
}
