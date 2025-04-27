import pandas as pd
import numpy as np
from .technical_analysis import TechnicalAnalysis


class TradingStrategyA:
    def __init__(self):
        self.ta = TechnicalAnalysis()
        
    def prepare_data(self, df):
        """Prepare data by calculating necessary indicators"""
        df = df.copy()
        # Calculate MA5
        df['ma5'] = self.ta.calculate_ma(df, window=5)
        # Calculate MA20
        df['ma20'] = self.ta.calculate_ma(df, window=20)
        # Calculate MA60
        df['ma60'] = self.ta.calculate_ma(df, window=60)
        # Calculate KDJ
        df = self.ta.calculate_kdj(df)

        df = self.ta.calculate_wr(df, period=14)  # 14日WR
        df = self.ta.calculate_wr(df, period=28)  # 28日WR
        # Calculate MACD
        df = self.ta.calculate_macd(df)
        # Calculate BOLL
        df = self.ta.calculate_boll(df)
        return df
        
    def find_trading_signals(self, df, ma_type):
        """
        Find trading signals based on strategy rules:
        1. Price above MA20
        2. KDJ J-value turns negative
        """
        df = df.copy()
        
        # Check if price is above MA20
        df[f'above_{ma_type}'] = df['close'] > df[f'{ma_type}']
        
        # Find where J value turns negative (current J < 0 and previous J >= 0)
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)
        
        # Create trading signals with selected columns
        signals = df[df[f'above_{ma_type}'] & df['j_turns_negative']].copy()
        # signals = df[df['j_turns_negative']].copy()
        
        # Select and rename columns for better readability
        selected_signals = signals[[
            'code', 
            'date', 
            'close',
            'ma5',
            'ma20',
            'ma60',
            'kdj_j',
            'prev_j',
            'macd_dif',
            'macd_dea',
            'macd',
            'boll_mid_20',
            'boll_upper_20',
            'boll_lower_20',
            'wr_14',
            'wr_28'
        ]].copy()
        
        selected_signals = selected_signals.rename(columns={
            'close': '当日收盘价',
            'ma5': '5日均线',
            'ma20': '20日均线',
            'ma60': '60日均线',
            'kdj_j': '当日J值',
            'prev_j': '前一日J值',
            'date': '信号日期',
            'macd_dif': 'MACD_DIF',
            'macd_dea': 'MACD_DEA',
            'macd': 'MACD',
            'boll_mid_20': 'BOLL中轨',
            'boll_upper_20': 'BOLL上轨',
            'boll_lower_20': 'BOLL下轨',
            'wr_14': 'WR14',
            'wr_28': 'WR28'
        })
        
        # Sort by date
        selected_signals = selected_signals.sort_values(['信号日期', 'code'])
        
        return selected_signals
        
    def calculate_returns(self, df, signals, days=10):
        """Calculate returns for the specified number of days after signal"""
        results = []
        
        for _, signal in signals.iterrows():
            code = signal['code']
            signal_date = signal['信号日期']
            signal_price = df[
                (df['code'] == code) & 
                (df['date'] == signal_date)
            ]['close'].iloc[0]
            
            # Find future prices
            future_data = df[
                (df['code'] == code) & 
                (df['date'] > signal_date)
            ].head(days)
            
            if len(future_data) == days:
                future_return = (future_data.iloc[-1]['close'] / signal_price - 1) * 100
                
                results.append({
                    'code': code,
                    'signal_date': signal_date,
                    'return': future_return,
                    'macd_dif': signal['MACD_DIF'],
                    'macd_dea': signal['MACD_DEA'],
                    'macd': signal['MACD'],
                    'boll_mid': signal['BOLL中轨'],
                    'boll_upper': signal['BOLL上轨'],
                    'boll_lower': signal['BOLL下轨'],
                    'wr_14': signal['WR14'],
                    'wr_28': signal['WR28']
                })
                
        return pd.DataFrame(results)  
    

class TradingStrategyB:
    def __init__(self):
        self.ta = TechnicalAnalysis()
        
    def prepare_data(self, df):
        """Prepare data by calculating necessary indicators"""
        df = df.copy()
        # Calculate MA5
        df['ma5'] = self.ta.calculate_ma(df, window=5)
        # Calculate MA10
        df['ma20'] = self.ta.calculate_ma(df, window=20)
        # df['ma10'] = self.ta.calculate_ma(df, window=10)
        # Calculate MA60
        df['ma60'] = self.ta.calculate_ma(df, window=60)
        # Calculate KDJ
        df = self.ta.calculate_kdj(df)
        # Calculate WR
        df = self.ta.calculate_wr(df, period=14)  # 14日WR
        df = self.ta.calculate_wr(df, period=28)  # 28日WR
        # Calculate MACD
        df = self.ta.calculate_macd(df)
        # Calculate BOLL
        df = self.ta.calculate_boll(df)
        return df
        
    def find_trading_signals(self, df, ma_type):
        """
        Find trading signals based on strategy rules:
        1. Price above MA20
        2. Find where J turns negative (D1) and then turns positive (D2)
        """
        df = df.copy()
        
        # Check if price is above MA10
        df[f'above_{ma_type}'] = df['close'] > df[f'{ma_type}']
        
        # Find where J value turns negative and then positive
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)
        
        # Create initial signals when J turns negative (D1)
        signals = df[df[f'above_{ma_type}'] & df['j_turns_negative']].copy()
        
        # For each D1 signal, find the corresponding D2 (when J turns positive)
        results = []
        for _, signal in signals.iterrows():
            code = signal['code']
            d1_date = signal['date']
            
            # Find the next date when J turns positive after D1
            future_data = df[
                (df['code'] == code) & 
                (df['date'] > d1_date)
            ].copy()
            
            future_data['j_turns_positive'] = (future_data['kdj_j'] >= 0) & (future_data['prev_j'] < 0)
            d2_data = future_data[future_data['j_turns_positive']]
            
            if len(d2_data) > 0:
                d2_date = d2_data.iloc[0]['date']
                d2_price = d2_data.iloc[0]['close']
                period_return = (d2_price / signal['close'] - 1) * 100
                
                result = {
                    'code': code,
                    'D1日期': d1_date,
                    'D2日期': d2_date,
                    'D1收盘价': signal['close'],
                    'D2收盘价': d2_price,
                    'D1-D2收益率': period_return,
                    'D1_5日均线': signal['ma5'],
                    'D1_20日均线': signal['ma20'],
                    'D1_60日均线': signal['ma60'],
                    'D1_J值': signal['kdj_j'],
                    'D2_J值': d2_data.iloc[0]['kdj_j'],
                    'D1_WR14': signal['wr_14'],
                    'D2_WR14': d2_data.iloc[0]['wr_14'],
                    'D1_WR28': signal['wr_28'],
                    'D2_WR28': d2_data.iloc[0]['wr_28'],
                    'D1_MACD_DIF': signal['macd_dif'],
                    'D1_MACD_DEA': signal['macd_dea'],
                    'D1_MACD': signal['macd'],
                    'D2_MACD_DIF': d2_data.iloc[0]['macd_dif'],
                    'D2_MACD_DEA': d2_data.iloc[0]['macd_dea'],
                    'D2_MACD': d2_data.iloc[0]['macd'],
                    'D1_BOLL中轨': signal['boll_mid_20'],
                    'D1_BOLL上轨': signal['boll_upper_20'],
                    'D1_BOLL下轨': signal['boll_lower_20'],
                    'D2_BOLL中轨': d2_data.iloc[0]['boll_mid_20'],
                    'D2_BOLL上轨': d2_data.iloc[0]['boll_upper_20'],
                    'D2_BOLL下轨': d2_data.iloc[0]['boll_lower_20'],
                    '持仓天数': (d2_date - d1_date).days
                }
                results.append(result)
        
        if not results:
            return pd.DataFrame()
            
        results_df = pd.DataFrame(results)
        return results_df
        
    def calculate_returns(self, df, signals, days=10):
        """This method is kept for backward compatibility but not used in the new strategy"""
        return pd.DataFrame() 
    

class TradingStrategyC:
    def __init__(self, j_diff_threshold):
        self.ta = TechnicalAnalysis()
        self.j_diff_threshold = j_diff_threshold
        
    def prepare_data(self, df):
        """Prepare data by calculating necessary indicators"""
        df = df.copy()
        # Calculate MA5
        df['ma5'] = self.ta.calculate_ma(df, window=5)
        # Calculate MA20
        df['ma20'] = self.ta.calculate_ma(df, window=20)
        # Calculate MA60
        df['ma60'] = self.ta.calculate_ma(df, window=60)
        # Calculate KDJ
        df = self.ta.calculate_kdj(df)
        # Calculate WR
        df = self.ta.calculate_wr(df, period=14)  # 14日WR
        df = self.ta.calculate_wr(df, period=28)  # 28日WR
        # Calculate MACD
        df = self.ta.calculate_macd(df)
        # Calculate BOLL
        df = self.ta.calculate_boll(df)
        return df
        
    def find_trading_signals(self, df, ma_type):
        """
        Find trading signals based on strategy rules:
        1. Price above MA20
        2. Find where J turns negative (D1) and then turns positive (D2)
        3. Only keep signals where J(D2) - J(D1) > 30
        """
        df = df.copy()
        
        # Check if price is above MA20
        df[f'above_{ma_type}'] = df['close'] > df[f'{ma_type}']
        
        # Find where J value turns negative and then positive
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)
        
        # Create initial signals when J turns negative (D1)
        signals = df[df[f'above_{ma_type}'] & df['j_turns_negative']].copy()
        
        # print("\n=== 策略C调试信息 ===")
        # print(f"初始信号数量: {len(signals)}")
        # if len(signals) > 0:
        #     print("\n初始信号示例:")
        #     print(signals[['code', 'date', 'close', 'kdj_j', 'prev_j']].head())
        
        # For each D1 signal, find the corresponding D2 (when J turns positive)
        results = []
        for _, signal in signals.iterrows():
            code = signal['code']
            d1_date = signal['date']
            d1_j = signal['kdj_j']
            
            # Find the next date when J turns positive after D1
            future_data = df[
                (df['code'] == code) & 
                (df['date'] > d1_date)
            ].copy()
            
            future_data['j_turns_positive'] = (future_data['kdj_j'] >= 0) & (future_data['prev_j'] < 0)
            d2_data = future_data[future_data['j_turns_positive']]
            
            if len(d2_data) > 0:
                d2_date = d2_data.iloc[0]['date']
                d2_price = d2_data.iloc[0]['close']
                d2_j = d2_data.iloc[0]['kdj_j']
                
                # Calculate J value difference
                j_diff = d2_j - d1_j
                
                print(f"\n股票 {code} 的J值变化:")
                print(f"D1日期: {d1_date}, D1_J值: {d1_j:.2f}")
                print(f"D2日期: {d2_date}, D2_J值: {d2_j:.2f}")
                print(f"J值差值: {j_diff:.2f}")
                
                # Only keep signals where J(D2) - J(D1) > 30
                if j_diff > self.j_diff_threshold:
                    period_return = (d2_price / signal['close'] - 1) * 100
                    
                    result = {
                        'code': code,
                        'D1日期': d1_date,
                        'D2日期': d2_date,
                        'D1收盘价': signal['close'],
                        'D2收盘价': d2_price,
                        'D1-D2收益率': period_return,
                        'D1_5日均线': signal['ma5'],
                        'D1_20日均线': signal['ma20'],
                        'D1_60日均线': signal['ma60'],
                        'D1_J值': d1_j,
                        'D2_J值': d2_j,
                        'J值差值': j_diff,
                        'D1_WR14': signal['wr_14'],
                        'D2_WR14': d2_data.iloc[0]['wr_14'],
                        'D1_WR28': signal['wr_28'],
                        'D2_WR28': d2_data.iloc[0]['wr_28'],
                        'D1_MACD_DIF': signal['macd_dif'],
                        'D1_MACD_DEA': signal['macd_dea'],
                        'D1_MACD': signal['macd'],
                        'D2_MACD_DIF': d2_data.iloc[0]['macd_dif'],
                        'D2_MACD_DEA': d2_data.iloc[0]['macd_dea'],
                        'D2_MACD': d2_data.iloc[0]['macd'],
                        'D1_BOLL中轨': signal['boll_mid_20'],
                        'D1_BOLL上轨': signal['boll_upper_20'],
                        'D1_BOLL下轨': signal['boll_lower_20'],
                        'D2_BOLL中轨': d2_data.iloc[0]['boll_mid_20'],
                        'D2_BOLL上轨': d2_data.iloc[0]['boll_upper_20'],
                        'D2_BOLL下轨': d2_data.iloc[0]['boll_lower_20'],
                        '持仓天数': (d2_date - d1_date).days
                    }
                    results.append(result)
        
        print(f"\n最终信号数量: {len(results)}")
        if len(results) > 0:
            print("\n最终信号示例:")
            print(pd.DataFrame(results).head())
        
        if not results:
            return pd.DataFrame()
            
        results_df = pd.DataFrame(results)
        return results_df
        
    def calculate_returns(self, df, signals, days=10):
        """This method is kept for backward compatibility but not used in the new strategy"""
        return pd.DataFrame() 