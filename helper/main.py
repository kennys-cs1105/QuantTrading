import pandas as pd
from data_loader import DataLoader
from strategy import TradingStrategyA, TradingStrategyB, TradingStrategyC
import os


def get_strategy_columns(strategy_name):
    """根据策略类型返回需要显示的列"""
    base_columns = ['code', 'code_name', '信号日期']
    
    if strategy_name == 'A':
        return base_columns + [
            '当日收盘价', '5日均线', '20日均线', '60日均线', 
            '当日J值', '前一日J值',
            '5日收益率', '10日收益率', '30日收益率'
        ]
    elif strategy_name == 'B':
        return base_columns + [
            '当日收盘价', '5日均线', '10日均线', '60日均线', 
            '当日J值', '前一日J值',
            '5日收益率', '10日收益率', '30日收益率'
        ]
    elif strategy_name == 'C':
        return base_columns + [
            'D1收盘价', 'D2收盘价', 'D1-D2收益率',
            'D1_5日均线', 'D1_10日均线', 'D1_60日均线',
            'D1_J值', 'D2_J值', 'J值差值',
            'D1_WR14', 'D2_WR14', 'D1_WR28', 'D2_WR28',
            'D1_MACD_DIF', 'D1_MACD_DEA', 'D1_MACD',
            'D2_MACD_DIF', 'D2_MACD_DEA', 'D2_MACD',
            'D1_BOLL中轨', 'D1_BOLL上轨', 'D1_BOLL下轨',
            'D2_BOLL中轨', 'D2_BOLL上轨', 'D2_BOLL下轨',
            '持仓天数'
        ]


def main():
    # data loader
    stock_data_path = "/home/kennys/experiment/QuantTrading/dataset/沪深300-2025年至今数据.csv"
    hs300_constituents_path="/home/kennys/experiment/QuantTrading/dataset/沪深300成分股.csv"
    data_loader = DataLoader(stock_data_path=stock_data_path, hs300_constituents_path=hs300_constituents_path)
    
    stock_data = data_loader.load_stock_data()
    hs300_constituents = data_loader.load_hs300_constituents()
    
    stock_data = pd.merge(stock_data, hs300_constituents[['code', 'code_name']], on='code', how='inner')
    
    # 选择策略
    strategy_name = input("请选择策略 (A/B/C): ").upper()
    if strategy_name == 'A':
        strategy = TradingStrategyA()
        date_col = '信号日期'
    elif strategy_name == 'B':
        strategy = TradingStrategyB()
        date_col = 'D1日期'  # 策略B使用'D1日期'作为日期列
    elif strategy_name == 'C':
        strategy = TradingStrategyC(j_diff_threshold=20)
        date_col = 'D1日期'
    else:
        print("无效的策略选择")
        return
    
    prepared_data = strategy.prepare_data(stock_data)
    signals = strategy.find_trading_signals(prepared_data, ma_type="ma20")
    
    # 打印策略返回的数据框的列名
    print("\n策略返回的数据框列名:")
    print(signals.columns.tolist())
    
    signals = pd.merge(signals, hs300_constituents[['code', 'code_name']], on='code', how='left')

    # 计算不同时间段的收益率
    returns_5 = strategy.calculate_returns(prepared_data, signals, days=5)
    returns_10 = strategy.calculate_returns(prepared_data, signals, days=10)
    returns_30 = strategy.calculate_returns(prepared_data, signals, days=30)
    
    print("\n=== 策略回测结果 ===")
    print(f"找到的交易信号总数: {len(signals)}")
    
    if len(signals) == 0:
        print("\n无交易信号")
        return
    
    print("\n=== 交易信号明细 ===")
    
    # 将日期转换为字符串格式
    signals[f'{date_col}_str'] = pd.to_datetime(signals[date_col]).dt.strftime('%Y-%m-%d')
    
    # 添加不同时间段的收益率到signals
    for days, returns in [(5, returns_5), (10, returns_10), (30, returns_30)]:
        if not returns.empty:
            # 将returns中的日期也转换为字符串格式
            returns['signal_date_str'] = returns['signal_date'].dt.strftime('%Y-%m-%d')
            signals = pd.merge(signals, returns[['code', 'signal_date_str', 'return']], 
                             left_on=['code', f'{date_col}_str'], 
                             right_on=['code', 'signal_date_str'], 
                             how='left')
            signals = signals.rename(columns={'return': f'{days}日收益率'})
            signals = signals.drop(['signal_date_str'], axis=1)
        else:
            signals[f'{days}日收益率'] = None
    
    # 删除临时列
    signals = signals.drop([f'{date_col}_str'], axis=1)
    
    # 格式化日期显示
    signals[date_col] = pd.to_datetime(signals[date_col]).dt.strftime('%Y-%m-%d')
    
    # 获取需要显示的列
    if strategy_name == 'A':
        display_columns = [
            'code', 'code_name', '信号日期', 
            '当日收盘价', '5日均线', '20日均线', '60日均线', 
            '当日J值', '前一日J值',
            '5日收益率', '10日收益率', '30日收益率'
        ]
    elif strategy_name == 'B':
        display_columns = [
            'code', 'code_name', 'D1日期', 'D2日期',
            'D1收盘价', 'D2收盘价', 'D1-D2收益率',
            'D1_5日均线', 'D1_20日均线', 'D1_60日均线',
            'D1_J值', 'D2_J值',
            'D1_WR14', 'D2_WR14', 'D1_WR28', 'D2_WR28',
            'D1_MACD_DIF', 'D1_MACD_DEA', 'D1_MACD',
            'D2_MACD_DIF', 'D2_MACD_DEA', 'D2_MACD',
            'D1_BOLL中轨', 'D1_BOLL上轨', 'D1_BOLL下轨',
            'D2_BOLL中轨', 'D2_BOLL上轨', 'D2_BOLL下轨',
            '持仓天数'
        ]
    else:  # 策略C
        display_columns = [
            'code', 'code_name', 'D1日期', 'D2日期',
            'D1收盘价', 'D2收盘价', 'D1-D2收益率',
            'D1_5日均线', 'D1_20日均线', 'D1_60日均线',
            'D1_J值', 'D2_J值', 'J值差值',
            'D1_WR14', 'D2_WR14', 'D1_WR28', 'D2_WR28',
            'D1_MACD_DIF', 'D1_MACD_DEA', 'D1_MACD',
            'D2_MACD_DIF', 'D2_MACD_DEA', 'D2_MACD',
            'D1_BOLL中轨', 'D1_BOLL上轨', 'D1_BOLL下轨',
            'D2_BOLL中轨', 'D2_BOLL上轨', 'D2_BOLL下轨',
            '持仓天数'
        ]
    
    # 对数值列进行四舍五入
    numeric_columns = [col for col in signals.columns if col not in ['code', 'code_name', date_col]]
    signals[numeric_columns] = signals[numeric_columns].round(2)
    
    # output_path = f"strategy_{strategy_name}-20250427.csv"
    # signals[display_columns].to_csv(output_path, index=False, encoding='utf-8-sig')
    # print(f"\n交易信号明细已保存至: {os.path.abspath(output_path)}")
    
    print("\n每个交易信号的详细信息:")
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    print(signals[display_columns].to_string(index=False))
    
    # 打印收益率统计信息
    print(f"\n=== 收益率统计 ===")
    for days, returns in [(5, returns_5), (10, returns_10), (30, returns_30)]:
        if not returns.empty:
            print(f"\n{days}天平均收益率: {returns['return'].mean():.2f}%")
            print(f"{days}天收益率中位数: {returns['return'].median():.2f}%")
            print(f"{days}天胜率: {(returns['return'] > 0).mean() * 100:.2f}%")
        else:
            print(f"\n{days}天收益率数据不足")
        
    print(f"\n=== 信号时间分布 ===")
    signals_by_month = signals.groupby(pd.to_datetime(signals[date_col]).dt.to_period('M')).size()
    print("\n每月信号数量:")
    print(signals_by_month)
    
if __name__ == "__main__":
    main()