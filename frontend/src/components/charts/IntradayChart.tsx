'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, AreaSeries, LineSeries, CandlestickSeries } from 'lightweight-charts';
import { FundChart } from '@/lib/api';

interface IntradayChartProps {
  data: FundChart | null;
  height?: number;
}

// 中国A股颜色规范：红色涨，绿色跌
const COLORS = {
  up: {
    line: '#ef4444',      // red-500
    top: 'rgba(239, 68, 68, 0.3)',
    bottom: 'rgba(239, 68, 68, 0.02)',
    text: 'text-red-400',
    candle: '#ef4444',
    wick: '#ef4444',
  },
  down: {
    line: '#22c55e',      // green-500
    top: 'rgba(34, 197, 94, 0.3)',
    bottom: 'rgba(34, 197, 94, 0.02)',
    text: 'text-emerald-400',
    candle: '#22c55e',
    wick: '#22c55e',
  },
};

// 判断是否为K线数据（有open/high/low/close字段）
const isCandleData = (point: any): boolean => {
  return point && typeof point.open === 'number' && typeof point.close === 'number';
};

export default function IntradayChart({ data, height = 400 }: IntradayChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [isUp, setIsUp] = useState(true);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.data.length === 0) return;

    // 判断数据类型
    const isKline = isCandleData(data.data[0]);
    const isIntraday = data.period === '1d';

    // 判断涨跌（相对于昨收）
    let lastPrice = 0;
    if (isKline) {
      lastPrice = data.data[data.data.length - 1]?.close || 0;
    } else {
      lastPrice = data.data[data.data.length - 1]?.value || 0;
    }
    const isRising = lastPrice >= data.previous_close;
    setIsUp(isRising);

    const colors = isRising ? COLORS.up : COLORS.down;

    // 创建图表
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b', style: 2 },
        horzLines: { color: '#1e293b', style: 2 },
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: '#475569',
          width: 1,
          style: 2,
        },
        horzLine: {
          color: '#475569',
          width: 1,
          style: 2,
        },
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: isIntraday,
        secondsVisible: false,
      },
      handleScroll: {
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: false,
      },
    });

    chartRef.current = chart;

    if (isKline) {
      // K线图
      const candleSeries = chart.addSeries(CandlestickSeries, {
        upColor: COLORS.up.candle,
        downColor: COLORS.down.candle,
        borderUpColor: COLORS.up.candle,
        borderDownColor: COLORS.down.candle,
        wickUpColor: COLORS.up.wick,
        wickDownColor: COLORS.down.wick,
      });

      const candleData = data.data.map((point) => ({
        time: point.time,
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
      }));

      candleSeries.setData(candleData);
    } else {
      // 折线图/面积图
      const areaSeries = chart.addSeries(AreaSeries, {
        lineColor: colors.line,
        topColor: colors.top,
        bottomColor: colors.bottom,
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      // 转换数据格式
      const chartData = data.data.map((point) => {
        if (isIntraday) {
          // 分时数据: 将 "09:30" 转换为时间戳
          const [hours, minutes] = point.time.split(':').map(Number);
          const date = new Date();
          date.setHours(hours, minutes, 0, 0);
          return {
            time: date.getTime() / 1000 as unknown as number,
            value: point.value,
          };
        } else {
          // 日K数据: 使用 yyyy-mm-dd 格式
          return {
            time: point.time,
            value: point.value,
          };
        }
      });

      areaSeries.setData(chartData);

      // 添加基准线（昨收/前收）
      if (data.previous_close > 0) {
        const baselineSeries = chart.addSeries(LineSeries, {
          color: '#64748b',
          lineWidth: 1,
          lineStyle: 2,
          lastValueVisible: false,
          priceLineVisible: false,
        });

        baselineSeries.setData(
          chartData.map((d) => ({
            time: d.time,
            value: data.previous_close,
          }))
        );
      }
    }

    // 设置价格范围
    chart.priceScale('right').applyOptions({
      autoScale: false,
      scaleMargins: {
        top: 0.1,
        bottom: 0.1,
      },
    });

    chart.timeScale().fitContent();

    // 响应式处理
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: height,
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, height]);

  // 休市状态
  if (data?.market_closed) {
    return (
      <div
        className="flex flex-col items-center justify-center bg-slate-900/30 rounded-xl border border-slate-800/50"
        style={{ height }}
      >
        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="text-slate-300 font-medium mb-1">市场休市</div>
        <div className="text-slate-500 text-sm">交易时间：周一至周五 9:30-11:30, 13:00-15:00</div>
      </div>
    );
  }

  // 无数据状态
  if (!data || data.data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-900/30 rounded-xl border border-slate-800/50"
        style={{ height }}
      >
        <div className="text-slate-500">暂无数据</div>
      </div>
    );
  }

  const isKline = isCandleData(data.data[0]);
  const colors = isUp ? COLORS.up : COLORS.down;
  
  let lastPrice = 0;
  let highPrice = 0;
  let lowPrice = 0;
  let openPrice = 0;
  
  if (isKline) {
    const lastPoint = data.data[data.data.length - 1];
    lastPrice = lastPoint?.close || 0;
    highPrice = lastPoint?.high || 0;
    lowPrice = lastPoint?.low || 0;
    openPrice = lastPoint?.open || 0;
  } else {
    lastPrice = data.data[data.data.length - 1]?.value || 0;
  }
  
  const change = lastPrice - data.previous_close;
  const changePercent = data.previous_close > 0 ? (change / data.previous_close) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* 价格信息卡片 - 放在图表上方 */}
      <div className="flex items-center gap-6 flex-wrap">
        <div>
          <div className="text-sm text-slate-400 mb-1">
            {isKline ? '最新收盘' : '最新净值'}
          </div>
          <div className={`text-2xl font-mono font-bold ${colors.text}`}>
            {lastPrice.toFixed(4)}
          </div>
        </div>
        <div className="h-10 w-px bg-slate-700" />
        <div>
          <div className="text-sm text-slate-400 mb-1">涨跌幅</div>
          <div className={`text-lg font-mono font-medium ${colors.text}`}>
            {change >= 0 ? '+' : ''}{change.toFixed(4)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
          </div>
        </div>
        <div className="h-10 w-px bg-slate-700" />
        <div>
          <div className="text-sm text-slate-400 mb-1">昨收/前收</div>
          <div className="text-lg font-mono font-medium text-slate-300">
            {data.previous_close.toFixed(4)}
          </div>
        </div>
        {isKline && (
          <>
            <div className="h-10 w-px bg-slate-700 hidden md:block" />
            <div className="hidden md:block">
              <div className="text-sm text-slate-400 mb-1">最高</div>
              <div className="text-lg font-mono font-medium text-red-400">
                {highPrice.toFixed(4)}
              </div>
            </div>
            <div className="h-10 w-px bg-slate-700 hidden md:block" />
            <div className="hidden md:block">
              <div className="text-sm text-slate-400 mb-1">最低</div>
              <div className="text-lg font-mono font-medium text-emerald-400">
                {lowPrice.toFixed(4)}
              </div>
            </div>
          </>
        )}
      </div>

      {/* 图表 */}
      <div ref={chartContainerRef} className="w-full" style={{ height: height - 80 }} />
    </div>
  );
}
