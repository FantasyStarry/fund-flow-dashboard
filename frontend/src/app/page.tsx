'use client';

import { useState, useCallback } from 'react';
import FundHeaderCard from '@/components/dashboard/FundHeaderCard';
import HoldingsCard from '@/components/dashboard/HoldingsCard';
import FundHoldingsCard from '@/components/dashboard/FundHoldingsCard';
import FlowCard from '@/components/dashboard/FlowCard';
import IntradayChart from '@/components/charts/IntradayChart';
import { useFundDetail, useFundChart, useFundFlow, useUserHoldings } from '@/lib/useFundData';
import { 
  FundHeaderSkeleton, 
  ChartSkeleton, 
  HoldingsCardSkeleton,
  FlowCardSkeleton,
  DataUpdateIndicator 
} from '@/components/ui/Skeleton';
import { RefreshCw } from 'lucide-react';

// 周期配置 - value必须是后端支持的英文代码
const PERIODS = [
  { label: '分时', value: '1d' },
  { label: '日K', value: '1m' },
  { label: '周K', value: '3m' },
  { label: '月K', value: '1y' },
] as const;

// 有效的周期值类型
type PeriodValue = typeof PERIODS[number]['value'];

// 默认基金代码
const DEFAULT_FUND_CODE = '161725';

export default function HomePage() {
  const [chartPeriod, setChartPeriod] = useState<PeriodValue>('1d');

  // 使用 SWR 缓存的数据获取
  const { 
    fund, 
    isLoading: isFundLoading, 
    isValidating: isFundValidating,
    mutate: refreshFund 
  } = useFundDetail(DEFAULT_FUND_CODE);
  
  const { 
    chartData, 
    isLoading: isChartLoading, 
    isValidating: isChartValidating,
    mutate: refreshChart 
  } = useFundChart(DEFAULT_FUND_CODE, chartPeriod);
  
  const { 
    flowData, 
    isLoading: isFlowLoading, 
    isValidating: isFlowValidating,
    mutate: refreshFlow 
  } = useFundFlow(DEFAULT_FUND_CODE);

  // 用户持仓数据
  const {
    isLoading: isHoldingsLoading,
    isValidating: isHoldingsValidating,
  } = useUserHoldings();

  // 是否正在后台更新任何数据
  const isUpdating = isFundValidating || isChartValidating || isFlowValidating || isHoldingsValidating;

  // 手动刷新所有数据
  const handleRefreshAll = useCallback(() => {
    refreshFund();
    refreshChart();
    refreshFlow();
  }, [refreshFund, refreshChart, refreshFlow]);

  const currentPeriodLabel = PERIODS.find(p => p.value === chartPeriod)?.label || '分时';

  return (
    <div className="space-y-6 relative">
      {/* 数据更新指示器 */}
      <DataUpdateIndicator isUpdating={isUpdating} />

      {/* 刷新按钮 */}
      <div className="flex justify-end">
        <button
          onClick={handleRefreshAll}
          disabled={isUpdating}
          className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${isUpdating ? 'animate-spin' : ''}`} />
          {isUpdating ? '更新中...' : '刷新数据'}
        </button>
      </div>

      {/* 基金头部信息 */}
      {isFundLoading ? (
        <FundHeaderSkeleton />
      ) : (
        <FundHeaderCard fund={fund} />
      )}

      {/* 图表和持仓 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 走势图 */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">
              {currentPeriodLabel}走势
            </h3>
            <div className="flex gap-1 p-1 bg-slate-800/50 rounded-lg">
              {PERIODS.map((period) => (
                <button
                  key={period.value}
                  onClick={() => setChartPeriod(period.value)}
                  disabled={isChartLoading}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    chartPeriod === period.value
                      ? 'bg-slate-700 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
          {isChartLoading ? (
            <ChartSkeleton height={380} />
          ) : (
            <IntradayChart data={chartData} height={380} />
          )}
        </div>

        {/* 持仓 */}
        <div className="lg:col-span-1">
          {isHoldingsLoading ? (
            <HoldingsCardSkeleton />
          ) : (
            <HoldingsCard />
          )}
        </div>
      </div>

      {/* 资金流向和重仓股 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {isFlowLoading ? (
          <FlowCardSkeleton />
        ) : (
          <FlowCard 
            flow={flowData} 
            onRefresh={refreshFlow}
          />
        )}
        <FundHoldingsCard fundCode={DEFAULT_FUND_CODE} />
      </div>
    </div>
  );
}
