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
    
    if len(signals) > 0:
        # 添加股票名称
        signals = pd.merge(signals, hs300_constituents[['code', 'code_name']], on='code', how='left')
        
        # 格式化日期
        signals['D1日期'] = signals['D1日期'].dt.strftime('%Y-%m-%d')
        signals['D2日期'] = signals['D2日期'].dt.strftime('%Y-%m-%d')
        
        # 格式化数值列
        numeric_columns = ['D1收盘价', 'D2收盘价', 'D1-D2收益率', 
                         'D1_5日均线', 'D1_20日均线', 'D1_60日均线',
                         'D1_J值', 'D2_J值', 'D1_WR14', 'D2_WR14',
                         'D1_WR28', 'D2_WR28']
        signals[numeric_columns] = signals[numeric_columns].round(2)
        
        # 设置显示列顺序
        display_columns = ['code', 'code_name', 'D1日期', 'D2日期', 
                         'D1收盘价', 'D2收盘价', 'D1-D2收益率', 
                         'D1_5日均线', 'D1_20日均线', 'D1_60日均线',
                         'D1_J值', 'D2_J值', 'D1_WR14', 'D2_WR14',
                         'D1_WR28', 'D2_WR28', '持仓天数']
        
        # 保存结果到CSV
        # output_path = "trading_signals_ma20.csv"
        # signals[display_columns].to_csv(output_path, index=False, encoding='utf-8-sig')
        # print(f"\n交易信号明细已保存至: {os.path.abspath(output_path)}")
        
        # 打印统计信息
        print("\n=== 策略回测结果 ===")
        print(f"找到的交易信号总数: {len(signals)}")
        
        print("\n=== 收益率统计 ===")
        print(f"平均收益率: {signals['D1-D2收益率'].mean():.2f}%")
        print(f"收益率中位数: {signals['D1-D2收益率'].median():.2f}%")
        print(f"胜率: {(signals['D1-D2收益率'] > 0).mean() * 100:.2f}%")
        print(f"平均持仓天数: {signals['持仓天数'].mean():.1f}天")
        
        print("\n=== 信号时间分布 ===")
        signals_by_month = signals.groupby(pd.to_datetime(signals['D1日期']).dt.to_period('M')).size()
        print("\n每月信号数量:")
        print(signals_by_month)
        
        print("\n每个交易信号的详细信息:")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print(signals[display_columns].to_string(index=False))
    else:
        print("\n未找到符合条件的交易信号")
    
if __name__ == "__main__":
    main() 