'use client';

import { useState, useEffect } from 'react';
import { Menu, Search, Bell } from 'lucide-react';
import { getMarketIndices, getMarketStatus, MarketIndex } from '@/lib/api';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [isTrading, setIsTrading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // 获取大盘指数
    const fetchIndices = async () => {
      try {
        const response = await getMarketIndices();
        if (response.success) {
          setIndices(response.data.slice(0, 1)); // 只显示上证指数
        }
      } catch (error) {
        console.error('获取指数失败:', error);
      }
    };

    // 获取市场状态
    const fetchStatus = async () => {
      try {
        const response = await getMarketStatus();
        if (response.success) {
          setIsTrading(response.data.is_trading);
        }
      } catch (error) {
        console.error('获取市场状态失败:', error);
      }
    };

    fetchIndices();
    fetchStatus();

    // 定时刷新
    const interval = setInterval(() => {
      fetchIndices();
      fetchStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatChange = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}`;
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
      {/* 左侧 */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <Menu className="w-6 h-6 text-slate-300" />
        </button>

        {/* 市场状态 */}
        <div className={`
          flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
          ${isTrading
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            : 'bg-slate-700/50 text-slate-400 border border-slate-600/50'
          }
        `}>
          <span className={`
            w-2 h-2 rounded-full animate-pulse
            ${isTrading ? 'bg-emerald-400' : 'bg-slate-500'}
          `} />
          {isTrading ? '交易中' : '已休市'}
        </div>

        {/* 大盘指数 */}
        {indices.map((index) => (
          <div key={index.symbol} className="hidden md:flex items-center gap-2 text-sm">
            <span className="text-slate-400">{index.name}:</span>
            <span className="font-mono font-medium text-slate-200">
              {index.value.toFixed(2)}
            </span>
            <span className={`font-mono ${index.change >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
              {formatChange(index.change_percent)}%
            </span>
          </div>
        ))}
      </div>

      {/* 右侧 */}
      <div className="flex items-center gap-4">
        {/* 搜索框 */}
        <div className="hidden md:flex items-center bg-slate-800/50 rounded-xl px-4 py-2 border border-slate-700/50 focus-within:border-blue-500/50 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
          <Search className="w-4 h-4 text-slate-400 mr-2" />
          <input
            type="text"
            placeholder="输入代码/拼音搜索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none w-48"
          />
        </div>

        {/* 通知 */}
        <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors relative">
          <Bell className="w-5 h-5 text-slate-400" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* 用户头像 */}
        <button className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm hover:shadow-lg hover:shadow-blue-500/25 transition-all">
          U
        </button>
      </div>
    </header>
  );
}
