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
        # Calculate MA20
        df['ma20'] = self.ta.calculate_ma(df, window=20)
        # Calculate MA60
        df['ma60'] = self.ta.calculate_ma(df, window=60)
        # Calculate KDJ
        df = self.ta.calculate_kdj(df)
        return df
        
    def find_trading_signals(self, df):
        """
        Find trading signals based on strategy rules:
        1. Price above MA20
        2. KDJ J-value turns negative
        """
        df = df.copy()
        
        # Check if price is above MA20
        df['above_ma60'] = df['close'] > df['ma60']
        
        # Find where J value turns negative (current J < 0 and previous J >= 0)
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)
        
        # Create trading signals with selected columns
        signals = df[df['above_ma60'] & df['j_turns_negative']].copy()
        
        # Select and rename columns for better readability
        selected_signals = signals[[
            'code', 
            'date', 
            'close',
            'ma5',
            'ma20',
            'ma60',
            'kdj_j',
            'prev_j'
        ]].copy()
        
        selected_signals = selected_signals.rename(columns={
            'close': '当日收盘价',
            'ma5': '5日均线',
            'ma20': '20日均线',
            'ma60': '60日均线',
            'kdj_j': '当日J值',
            'prev_j': '前一日J值',
            'date': '信号日期'
        })
        
        # Sort by date
        selected_signals = selected_signals.sort_values(['信号日期', 'code'])
        
        return selected_signals
        
    def calculate_returns(self, df, signals, days=10):
        """Calculate returns for the specified number of days after signal"""
        results = []
        
        for _, signal in signals.iterrows():
            code = signal['code']
            signal_date = signal['信号日期']  # Updated to match the new column name
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
                    'entry_price': signal_price,
                    'exit_price': future_data.iloc[-1]['close'],
                    'return': future_return
                })
                
        return pd.DataFrame(results)  