/**
 * 骨架屏组件
 * 用于数据加载时的占位显示
 */

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-slate-800/50 rounded',
        className
      )}
    />
  );
}

/**
 * 基金头部骨架屏
 */
export function FundHeaderSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
        <div className="text-right space-y-2">
          <Skeleton className="h-8 w-24 ml-auto" />
          <Skeleton className="h-4 w-16 ml-auto" />
        </div>
      </div>
      <div className="mt-4 flex gap-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
}

/**
 * 图表骨架屏
 */
export function ChartSkeleton({ height = 380 }: { height?: number }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-8 w-48" />
      </div>
      <Skeleton className="w-full" style={{ height }} />
    </div>
  );
}

/**
 * 持仓卡片骨架屏
 */
export function HoldingsCardSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <Skeleton className="h-6 w-24 mb-4" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-lg" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-3 w-12" />
              </div>
            </div>
            <Skeleton className="h-4 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 资金流向骨架屏
 */
export function FlowCardSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <div className="space-y-4">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-32 w-full rounded-lg" />
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-16 w-full rounded-lg" />
          <Skeleton className="h-16 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}

/**
 * 基金持仓骨架屏
 */
export function FundHoldingsSkeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <Skeleton className="h-6 w-24 mb-4" />
      <div className="space-y-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between py-2">
            <div className="flex items-center gap-3">
              <Skeleton className="h-6 w-12 rounded" />
              <Skeleton className="h-4 w-20" />
            </div>
            <div className="flex items-center gap-4">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 数据更新指示器
 */
export function DataUpdateIndicator({ isUpdating }: { isUpdating: boolean }) {
  if (!isUpdating) return null;
  
  return (
    <div className="fixed top-4 right-4 z-50 flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-xs text-blue-400">
      <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
      数据更新中
    </div>
  );
}

/**
 * 缓存数据提示
 */
export function CacheDataBadge({ timestamp }: { timestamp?: number }) {
  if (!timestamp) return null;
  
  const date = new Date(timestamp);
  const timeStr = date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  return (
    <span className="text-xs text-slate-500 ml-2">
      (缓存于 {timeStr})
    </span>
  );
}
