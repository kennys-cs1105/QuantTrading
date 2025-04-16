import pandas as pd
import numpy as np
from technical_analysis import TechnicalAnalysis

class TradingStrategy:
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
        return df
        
    def find_trading_signals(self, df):
        """
        Find trading signals based on strategy rules:
        1. Price above MA20
        2. Find where J turns negative (D1) and then turns positive (D2)
        """
        df = df.copy()
        
        # Check if price is above MA10
        df['above_ma20'] = df['close'] > df['ma20']
        
        # Find where J value turns negative and then positive
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)
        
        # Create initial signals when J turns negative (D1)
        signals = df[df['above_ma20'] & df['j_turns_negative']].copy()
        
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