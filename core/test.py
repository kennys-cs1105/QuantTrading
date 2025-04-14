"""
# 需求

- 量化交易策略的制定
- python代码实现

## 输入数据

- 沪深300成分股的股票代码: df_hs300 (pd.DataFrame),列名为"code", "code_name"
- 沪深300所有成分股在2024-1到2025-2的所有股票数据(pd.DataFrame), stock_data_path= "/home/kennys/MineX/QuantTrading/dataset/沪深300-2024年1月至2025年2月数据.csv"
    - 列名包括"date", "code", "open", "close", "high", "low", "close", "preclose", "volume", "amount", "turn"

## 量化策略

- 核心思想为
```
保证趋势向上（股价保持在关键均线上方，比如20日均线、60日均线、10周线）。
等待短期超买指标回调（KDJ的J值进入负值区间）。
在回调后寻找短期反弹机会（统计日K阴线后的5天、10天、30天收益，验证超卖修正是否带来盈利）
```

- 请根据输入数据,计算20日均线,
- 当日K一直运行在20日线上方时,计算这些股票的KDJ指标
- 当这些筛选后的股票的KDJ指标的J值出现负值后, 统计后10天的收益
"""


import pandas as pd
from data_loader import DataLoader
from strategy import TradingStrategy
import os

def main():
    # data loader
    stock_data_path = "/home/kennys/MineX/QuantTrading/dataset/沪深300-2024年至今数据.csv"
    hs300_constituents_path="/home/kennys/MineX/QuantTrading/dataset/沪深300成分股.csv"
    data_loader = DataLoader(stock_data_path, hs300_constituents_path)
    
    stock_data = data_loader.load_stock_data()
    hs300_constituents = data_loader.load_hs300_constituents()
    
    stock_data = pd.merge(stock_data, hs300_constituents[['code', 'code_name']], on='code', how='inner')
    
    strategy = TradingStrategy()
    
    prepared_data = strategy.prepare_data(stock_data)
    
    signals = strategy.find_trading_signals(prepared_data)
    
    signals = pd.merge(signals, hs300_constituents[['code', 'code_name']], on='code', how='left')

    # 计算不同时间段的收益率
    returns_5 = strategy.calculate_returns(prepared_data, signals, days=5)
    returns_10 = strategy.calculate_returns(prepared_data, signals, days=10)
    returns_30 = strategy.calculate_returns(prepared_data, signals, days=30)
    
    print("\n=== 策略回测结果 ===")
    print(f"找到的交易信号总数: {len(signals)}")
    
    if len(signals) > 0:
        print("\n=== 交易信号明细 ===")
        
        # 将日期转换为字符串格式
        signals['信号日期_str'] = signals['信号日期'].dt.strftime('%Y-%m-%d')
        
        # 添加不同时间段的收益率到signals
        for days, returns in [(5, returns_5), (10, returns_10), (30, returns_30)]:
            # 将returns中的日期也转换为字符串格式
            returns['signal_date_str'] = returns['signal_date'].dt.strftime('%Y-%m-%d')
            signals = pd.merge(signals, returns[['code', 'signal_date_str', 'return']], 
                             left_on=['code', '信号日期_str'], 
                             right_on=['code', 'signal_date_str'], 
                             how='left')
            signals = signals.rename(columns={'return': f'{days}日收益率'})
            signals = signals.drop(['signal_date_str'], axis=1)
        
        # 删除临时列
        signals = signals.drop(['信号日期_str'], axis=1)
        
        # 格式化日期显示
        signals['信号日期'] = signals['信号日期'].dt.strftime('%Y-%m-%d')
        
        numeric_columns = ['当日收盘价', '5日均线', '20日均线', '60日均线', '当日J值', '前一日J值', '5日收益率', '10日收益率', '30日收益率']
        signals[numeric_columns] = signals[numeric_columns].round(2)
        
        display_columns = ['code', 'code_name', '信号日期', '当日收盘价', '5日均线', '20日均线', '60日均线', '当日J值', '前一日J值', '5日收益率', '10日收益率', '30日收益率']
        
        output_path = "ma60_up2now_info.csv"
        signals[display_columns].to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n交易信号明细已保存至: {os.path.abspath(output_path)}")
        
        print("\n每个交易信号的详细信息:")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print(signals[display_columns].to_string(index=False))
        
        if len(returns_30) > 0:
            print(f"\n=== 收益率统计 ===")
            print(f"5天平均收益率: {returns_5['return'].mean():.2f}%")
            print(f"5天收益率中位数: {returns_5['return'].median():.2f}%")
            print(f"5天胜率: {(returns_5['return'] > 0).mean() * 100:.2f}%")
            print(f"\n10天平均收益率: {returns_10['return'].mean():.2f}%")
            print(f"10天收益率中位数: {returns_10['return'].median():.2f}%")
            print(f"10天胜率: {(returns_10['return'] > 0).mean() * 100:.2f}%")
            print(f"\n30天平均收益率: {returns_30['return'].mean():.2f}%")
            print(f"30天收益率中位数: {returns_30['return'].median():.2f}%")
            print(f"30天胜率: {(returns_30['return'] > 0).mean() * 100:.2f}%")
            
            print(f"\n=== 信号时间分布 ===")
            signals_by_month = signals.groupby(pd.to_datetime(signals['信号日期']).dt.to_period('M')).size()
            print("\n每月信号数量:")
            print(signals_by_month)
    
if __name__ == "__main__":
    main()