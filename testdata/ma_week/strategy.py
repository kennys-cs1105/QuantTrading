import pandas as pd
import numpy as np
from technical_analysis import TechnicalAnalysis

class TradingStrategy:
    def __init__(self):
        self.ta = TechnicalAnalysis()

    def convert_to_weekly(self, df):
        df['week'] = pd.to_datetime(df['date']).dt.to_period('W').dt.start_time
        df_weekly = df.groupby(['code', 'week']).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).reset_index().rename(columns={'week': 'date'})
        return df_weekly

    def prepare_data(self, df):
        df = self.convert_to_weekly(df)
        df['ma5'] = self.ta.calculate_ma(df, window=5)
        df['ma20'] = self.ta.calculate_ma(df, window=20)
        df['ma60'] = self.ta.calculate_ma(df, window=60)
        df = self.ta.calculate_kdj(df)
        return df

    def find_trading_signals(self, df):
        df = df.copy()
        df['above_ma20'] = df['close'] > df['ma20']
        df['prev_j'] = df.groupby('code')['kdj_j'].shift(1)
        df['j_turns_negative'] = (df['kdj_j'] < 0) & (df['prev_j'] >= 0)

        signals = df[df['above_ma20'] & df['j_turns_negative']].copy()
        results = []

        for _, signal in signals.iterrows():
            code = signal['code']
            d1_date = signal['date']

            future_data = df[(df['code'] == code) & (df['date'] > d1_date)].copy()
            future_data['j_turns_positive'] = (future_data['kdj_j'] >= 0) & (future_data['prev_j'] < 0)
            d2_data = future_data[future_data['j_turns_positive']]

            if not d2_data.empty:
                d2 = d2_data.iloc[0]
                result = {
                    'code': code,
                    'D1日期': d1_date,
                    'D2日期': d2['date'],
                    'D1收盘价': signal['close'],
                    'D2收盘价': d2['close'],
                    'D1-D2收益率': (d2['close'] / signal['close'] - 1) * 100,
                    'D1_5周均线': signal['ma5'],
                    'D1_20周均线': signal['ma20'],
                    'D1_60周均线': signal['ma60'],
                    'D1_J值': signal['kdj_j'],
                    'D2_J值': d2['kdj_j'],
                    '持仓周数': (d2['date'] - d1_date).days // 7
                }
                results.append(result)

        return pd.DataFrame(results) if results else pd.DataFrame()