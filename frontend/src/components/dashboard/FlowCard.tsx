'use client';

import { FundFlow } from '@/lib/api';

interface FlowCardProps {
  flow: FundFlow | null;
}

export default function FlowCard({ flow }: FlowCardProps) {
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

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4">
        板块资金流向 ({flow.sector})
      </h3>

      {/* 资金流向条形图 */}
      <div className="h-10 bg-slate-800 rounded-full overflow-hidden flex mb-6">
        <div
          className="bg-gradient-to-r from-red-500 to-red-400 flex items-center justify-center text-white text-sm font-semibold"
          style={{ width: `${flow.inflow_percent}%` }}
        >
          流入 {flow.inflow_percent}%
        </div>
        <div
          className="bg-gradient-to-r from-emerald-400 to-emerald-500 flex items-center justify-center text-white text-sm font-semibold"
          style={{ width: `${flow.outflow_percent}%` }}
        >
          流出 {flow.outflow_percent}%
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
              {item.value >= 0 ? '+' : ''}{item.value.toFixed(1)}亿
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
