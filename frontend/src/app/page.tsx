'use client';

import { useEffect, useState } from 'react';
import FundHeaderCard from '@/components/dashboard/FundHeaderCard';
import HoldingsCard from '@/components/dashboard/HoldingsCard';
import FlowCard from '@/components/dashboard/FlowCard';
import IntradayChart from '@/components/charts/IntradayChart';
import { Fund, FundChart, FundFlow, getFundDetail, getFundChart, getFundFlow } from '@/lib/api';

// 周期配置 - value必须是后端支持的英文代码
const PERIODS = [
  { label: '分时', value: '1d' },
  { label: '日K', value: '1m' },
  { label: '周K', value: '3m' },
  { label: '月K', value: '1y' },
] as const;

// 有效的周期值类型
type PeriodValue = typeof PERIODS[number]['value'];

export default function HomePage() {
  const [fund, setFund] = useState<Fund | null>(null);
  const [chartData, setChartData] = useState<FundChart | null>(null);
  const [flowData, setFlowData] = useState<FundFlow | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartPeriod, setChartPeriodState] = useState<PeriodValue>('1d');

  // 包装setChartPeriod以确保只接受有效值
  const setChartPeriod = (value: string) => {
    const validValue = PERIODS.find(p => p.value === value)?.value;
    if (validValue) {
      setChartPeriodState(validValue);
    } else {
      console.error('Invalid period value:', value);
    }
  };

  // 默认展示招商中证白酒
  const defaultFundCode = '161725';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // 并行获取数据
        const [fundRes, chartRes, flowRes] = await Promise.all([
          getFundDetail(defaultFundCode),
          getFundChart(defaultFundCode, chartPeriod),
          getFundFlow(defaultFundCode),
        ]);

        if (fundRes.success) {
          setFund(fundRes.data);
        }
        if (chartRes.success) {
          setChartData(chartRes.data);
        }
        if (flowRes.success) {
          setFlowData(flowRes.data);
        }
      } catch (error) {
        console.error('获取数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // 定时刷新（每30秒，仅开盘时）
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [chartPeriod]);

  const currentPeriodLabel = PERIODS.find(p => p.value === chartPeriod)?.label || '分时';

  return (
    <div className="space-y-6">
      {/* 基金头部信息 */}
      <FundHeaderCard fund={fund} />

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
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
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
          <IntradayChart data={chartData} height={380} />
        </div>

        {/* 持仓 */}
        <div className="lg:col-span-1">
          <HoldingsCard />
        </div>
      </div>

      {/* 资金流向 */}
      <FlowCard flow={flowData} />
    </div>
  );
}
