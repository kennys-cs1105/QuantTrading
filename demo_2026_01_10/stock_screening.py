"""
股票量化策略筛选程序

根据以下条件筛选个股：
1. 最近10日内，某一日（D1）出现上涨，第二天（D2）出现大于等于三倍D1成交量的放量上涨
2. D2放量阳线出现上影线
3. D2阳线突破前期趋势
"""

import baostock as bs
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


def get_main_board_and_chinext_stocks() -> pd.DataFrame:
    """
    获取沪深主板和创业板所有股票列表
    
    Returns:
        DataFrame: 包含股票代码和名称的DataFrame
    """
    lg = bs.login()
    if lg.error_code != '0':
        raise Exception(f'登录失败，错误代码：{lg.error_code}, 错误信息：{lg.error_msg}')
    
    try:
        # 尝试获取所有股票列表（不指定日期，获取最新的）
        # 如果失败，尝试向前查找最近10天的交易日
        stock_list = []
        max_retry_days = 10
        
        for day_offset in range(max_retry_days):
            target_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            rs = bs.query_all_stock(day=target_date)
            
            if rs.error_code != '0':
                if day_offset < max_retry_days - 1:
                    continue  # 继续尝试下一天
                else:
                    raise Exception(f'查询股票列表失败，错误代码：{rs.error_code}, 错误信息：{rs.error_msg}')
            
            # 保存成DataFrame
            stock_list = []
            while rs.next():
                stock_list.append(rs.get_row_data())
            
            if stock_list:
                print(f"成功从 {target_date} 获取股票列表，共 {len(stock_list)} 只")
                break
            elif day_offset < max_retry_days - 1:
                print(f"日期 {target_date} 无数据，尝试前一个交易日...")
                continue
        
        if not stock_list:
            # 如果还是空，尝试不传日期参数
            print("尝试获取最新股票列表（不指定日期）...")
            rs = bs.query_all_stock()
            if rs.error_code != '0':
                raise Exception(f'查询股票列表失败，错误代码：{rs.error_code}, 错误信息：{rs.error_msg}')
            
            stock_list = []
            while rs.next():
                stock_list.append(rs.get_row_data())
            
            if stock_list:
                print(f"成功获取股票列表，共 {len(stock_list)} 只")
            else:
                raise Exception('无法获取股票列表，请检查网络连接或数据源')
        
        df_all_stocks = pd.DataFrame(stock_list, columns=rs.fields)
        
        # 打印调试信息
        print(f"原始数据包含 {len(df_all_stocks)} 只股票")
        if len(df_all_stocks) > 0:
            print(f"股票代码示例（前5个）: {df_all_stocks['code'].head().tolist()}")
        
        # 筛选沪深主板和创业板股票
        # 上海主板：sh.600, sh.601, sh.603, sh.605
        # 深圳主板：sz.000
        # 创业板：sz.300
        df_main_board = df_all_stocks[
            (df_all_stocks['code'].str.startswith('sh.600') | 
             df_all_stocks['code'].str.startswith('sh.601') |
             df_all_stocks['code'].str.startswith('sh.603') |
             df_all_stocks['code'].str.startswith('sh.605')) |  # 上海主板
            (df_all_stocks['code'].str.startswith('sz.000')) |  # 深圳主板
            (df_all_stocks['code'].str.startswith('sz.300'))    # 创业板
        ]
        
        print(f"筛选后的主板和创业板股票：{len(df_main_board)} 只")
        
        if len(df_main_board) == 0 and len(df_all_stocks) > 0:
            # 如果筛选后为空，打印一些示例看看实际的数据格式
            print("警告：筛选后为空，原始数据示例：")
            print(df_all_stocks[['code', 'code_name']].head(10))
        
        return df_main_board[['code', 'code_name']].copy()
    
    finally:
        bs.logout()


def get_stock_history_data(stock_code: str, days: int = 30, session_logged_in: bool = False) -> Optional[pd.DataFrame]:
    """
    获取单只股票最近N天的历史数据
    
    Args:
        stock_code: 股票代码，如 'sh.600000'
        days: 获取最近多少天的数据，默认30天
        session_logged_in: 是否已经登录，如果True则不会登出
    
    Returns:
        DataFrame: 包含股票历史数据的DataFrame，如果获取失败返回None
    """
    should_logout = False
    if not session_logged_in:
        lg = bs.login()
        if lg.error_code != '0':
            print(f'登录失败，错误代码：{lg.error_code}, 错误信息：{lg.error_msg}')
            return None
        should_logout = True
    
    try:
        # 计算开始日期
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime('%Y-%m-%d')  # 多取10天作为缓冲
        
        # 获取日K线数据
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,code,open,high,low,close,preclose,volume,amount,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 前复权
        )
        
        if rs.error_code != '0':
            if should_logout:
                print(f'查询股票 {stock_code} 数据失败，错误代码：{rs.error_code}, 错误信息：{rs.error_msg}')
            return None
        
        # 保存数据
        stock_data = []
        while rs.next():
            stock_data.append(rs.get_row_data())
        
        if not stock_data:
            return None
        
        df_stock = pd.DataFrame(stock_data, columns=rs.fields)
        
        # 转换数据类型
        numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn']
        for col in numeric_cols:
            df_stock[col] = pd.to_numeric(df_stock[col], errors='coerce')
        
        df_stock['date'] = pd.to_datetime(df_stock['date'])
        df_stock = df_stock.sort_values('date').reset_index(drop=True)
        
        # 只保留最近30天
        if len(df_stock) > days:
            df_stock = df_stock.tail(days).reset_index(drop=True)
        
        return df_stock
    
    finally:
        if should_logout:
            bs.logout()


def is_price_up(close: float, preclose: float) -> bool:
    """
    判断当日是否上涨
    
    Args:
        close: 收盘价
        preclose: 前收盘价
    
    Returns:
        bool: 是否上涨
    """
    return close > preclose


def has_shadow_upper(df_day: pd.Series) -> bool:
    """
    判断K线是否有上影线
    
    Args:
        df_day: 单日K线数据（Series）
    
    Returns:
        bool: 是否有上影线
    """
    high = df_day['high']
    close = df_day['close']
    open_price = df_day['open']
    # 上影线 = 最高价 - max(收盘价, 开盘价)
    shadow_upper = high - max(close, open_price)
    # 上影线长度需要大于0.01（避免因精度问题导致的误判）
    return shadow_upper > 0.01


def check_breakout(df: pd.DataFrame, d2_idx: int, lookback_period: int = 20) -> bool:
    """
    判断D2阳线是否突破前期趋势
    
    Args:
        df: 股票历史数据DataFrame
        d2_idx: D2在DataFrame中的索引
        lookback_period: 向前看的天数，用于判断前期趋势，默认20天
    
    Returns:
        bool: 是否突破前期趋势
    """
    if d2_idx < lookback_period:
        # 数据不足，无法判断
        return False
    
    # 获取D2的数据
    d2_data = df.iloc[d2_idx]
    d2_close = d2_data['close']
    
    # 获取前lookback_period天的最高价（排除D2当天）
    prior_data = df.iloc[max(0, d2_idx - lookback_period):d2_idx]
    if len(prior_data) == 0:
        return False
    
    # 前期最高价
    prior_high = prior_data['high'].max()
    
    # 判断D2收盘价是否突破前期最高价
    # 这里也可以使用其他判断方法，比如突破前期20日均线等
    # 为了更严格，我们要求D2的最高价突破前期最高价
    d2_high = d2_data['high']
    
    return d2_high > prior_high


def check_strategy_conditions(df: pd.DataFrame) -> List[pd.DataFrame]:
    """
    检查股票是否满足策略条件
    
    Args:
        df: 股票历史数据DataFrame（最近30天）
    
    Returns:
        List[pd.DataFrame]: 满足条件的日期数据列表，每个元素是D2当天的数据行
    """
    results = []
    
    if len(df) < 10:
        return results
    
    # 只检查最近10天的数据
    recent_data = df.tail(10).reset_index(drop=True)
    full_df = df.reset_index(drop=True)
    
    # 遍历最近10天的数据，寻找满足条件的D1和D2
    for i in range(len(recent_data) - 1):
        d1_idx_in_recent = i
        d2_idx_in_recent = i + 1
        
        # 计算在完整DataFrame中的索引
        d1_idx_in_full = len(df) - len(recent_data) + d1_idx_in_recent
        d2_idx_in_full = len(df) - len(recent_data) + d2_idx_in_recent
        
        d1_data = recent_data.iloc[d1_idx_in_recent]
        d2_data = recent_data.iloc[d2_idx_in_recent]
        
        # 条件1：D1上涨，D2放量上涨（成交量>=3倍D1）
        d1_up = is_price_up(d1_data['close'], d1_data['preclose'])
        d2_up = is_price_up(d2_data['close'], d2_data['preclose'])
        d1_volume = d1_data['volume']
        d2_volume = d2_data['volume']
        
        # 检查成交量是否为0或NaN
        if pd.isna(d1_volume) or pd.isna(d2_volume) or d1_volume == 0:
            continue
        
        volume_condition = d2_volume >= 3 * d1_volume
        
        if not (d1_up and d2_up and volume_condition):
            continue
        
        # 条件2：D2放量阳线出现上影线
        d2_is_positive = d2_data['close'] > d2_data['open']  # 阳线
        has_shadow = has_shadow_upper(d2_data)
        
        if not (d2_is_positive and has_shadow):
            continue
        
        # 条件3：D2阳线突破前期趋势
        breakout = check_breakout(full_df, d2_idx_in_full)
        
        if not breakout:
            continue
        
        # 所有条件都满足，添加到结果中
        results.append(d2_data.to_frame().T)
    
    return results


def screen_stocks() -> pd.DataFrame:
    """
    主函数：筛选满足策略条件的股票
    
    Returns:
        DataFrame: 包含满足条件的股票数据，字段包括date,code,open,high,low,close,preclose,volume,amount,turn
    """
    print("正在获取股票列表...")
    stock_list_df = get_main_board_and_chinext_stocks()
    print(f"共获取 {len(stock_list_df)} 只股票")
    
    # 登录baostock（整个筛选过程使用一次登录）
    lg = bs.login()
    if lg.error_code != '0':
        raise Exception(f'登录失败，错误代码：{lg.error_code}, 错误信息：{lg.error_msg}')
    
    try:
        all_results = []
        total_stocks = len(stock_list_df)
        
        print(f"\n开始筛选股票，共需要处理 {total_stocks} 只股票...")
        
        for idx, row in stock_list_df.iterrows():
            stock_code = row['code']
            stock_name = row['code_name']
            
            if (idx + 1) % 100 == 0:
                print(f"进度: {idx + 1}/{total_stocks}, 当前: {stock_code} {stock_name}")
            
            # 获取股票历史数据（使用已登录的会话）
            df_stock = get_stock_history_data(stock_code, days=30, session_logged_in=True)
            
            if df_stock is None or len(df_stock) == 0:
                continue
            
            # 检查策略条件
            matched_days = check_strategy_conditions(df_stock)
            
            if matched_days:
                for matched_day in matched_days:
                    all_results.append(matched_day)
                print(f"  ✓ {stock_code} {stock_name} 满足条件")
        
        if not all_results:
            print("\n未找到满足条件的股票")
            # 返回空的DataFrame，但包含所需的列
            return pd.DataFrame(columns=['date', 'code', 'open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn'])
        
        # 合并所有结果
        result_df = pd.concat(all_results, ignore_index=True)
        
        # 确保列的顺序正确
        required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn']
        result_df = result_df[required_columns]
        
        # 按日期排序
        result_df = result_df.sort_values(['date', 'code']).reset_index(drop=True)
        
        print(f"\n筛选完成！共找到 {len(result_df)} 条满足条件的记录")
        print(f"涉及 {result_df['code'].nunique()} 只股票")
        
        return result_df
    
    finally:
        bs.logout()


if __name__ == "__main__":
    # 执行筛选
    result = screen_stocks()
    
    # 显示结果
    if len(result) > 0:
        print("\n筛选结果:")
        print(result)
        
        # 保存结果到CSV文件
        output_file = "/home/kennys/workspace/MineX/QuantTrading/demo_2026_01_10/screened_stocks.csv"
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: {output_file}")
    else:
        print("\n未找到满足条件的股票")

