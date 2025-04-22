import pandas as pd
import numpy as np

class TechnicalAnalysis:
    @staticmethod
    def calculate_ma(df, window=20):
        """Calculate Moving Average for each stock"""
        return df.groupby('code')['close'].transform(lambda x: x.rolling(window=window).mean())
    
    @staticmethod
    def calculate_kdj(df, n=9, m1=3, m2=3, period='daily'):
        """
        Calculate KDJ indicator
        n: RSV period
        m1: K period
        m2: D period
        period: 'daily' or 'weekly'
        """
        df = df.copy()
        
        # Group by code to calculate KDJ for each stock
        for code in df['code'].unique():
            mask = df['code'] == code
            df_stock = df[mask].copy()
            
            if period == 'weekly':
                # Convert to weekly data
                df_stock = df_stock.set_index('date')
                df_weekly = df_stock.resample('W').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).reset_index()
                
                # Calculate KDJ for weekly data
                df_weekly = df_weekly.reset_index(drop=True)
                
                # Calculate RSV
                low_list = df_weekly['low'].rolling(window=n, min_periods=1).min()
                high_list = df_weekly['high'].rolling(window=n, min_periods=1).max()
                rsv = (df_weekly['close'] - low_list) / (high_list - low_list) * 100
                
                # Initialize K, D, J arrays
                k = np.zeros(len(df_weekly))
                d = np.zeros(len(df_weekly))
                
                # Calculate K and D
                for i in range(len(df_weekly)):
                    if i == 0:
                        k[i] = 50
                        d[i] = 50
                    else:
                        k[i] = (m1 - 1) * k[i-1] / m1 + rsv[i] / m1
                        d[i] = (m2 - 1) * d[i-1] / m2 + k[i] / m2
                
                # Calculate J
                j = 3 * k - 2 * d
                
                # Create weekly KDJ DataFrame
                df_weekly_kdj = pd.DataFrame({
                    'date': df_weekly['date'],
                    'kdj_k': k,
                    'kdj_d': d,
                    'kdj_j': j
                })
                
                # Merge weekly KDJ back to daily data
                df_stock = df_stock.reset_index()
                df_stock['week_start'] = df_stock['date'].dt.to_period('W').dt.start_time
                df_weekly_kdj['week_start'] = df_weekly_kdj['date'].dt.to_period('W').dt.start_time
                
                # Merge and fill forward
                df_stock = pd.merge(df_stock, df_weekly_kdj[['week_start', 'kdj_k', 'kdj_d', 'kdj_j']], 
                                  on='week_start', how='left')
                
                # Fill forward any missing values
                df_stock['kdj_k'] = df_stock['kdj_k'].fillna(method='ffill')
                df_stock['kdj_d'] = df_stock['kdj_d'].fillna(method='ffill')
                df_stock['kdj_j'] = df_stock['kdj_j'].fillna(method='ffill')
                
                # Update the original DataFrame
                df.loc[mask, 'kdj_k'] = df_stock['kdj_k'].values
                df.loc[mask, 'kdj_d'] = df_stock['kdj_d'].values
                df.loc[mask, 'kdj_j'] = df_stock['kdj_j'].values
                
            else:
                # Daily KDJ calculation
                df_stock = df_stock.reset_index(drop=True)
                
                # Calculate RSV
                low_list = df_stock['low'].rolling(window=n, min_periods=1).min()
                high_list = df_stock['high'].rolling(window=n, min_periods=1).max()
                rsv = (df_stock['close'] - low_list) / (high_list - low_list) * 100
                
                # Initialize K, D, J arrays
                k = np.zeros(len(df_stock))
                d = np.zeros(len(df_stock))
                
                # Calculate K and D
                for i in range(len(df_stock)):
                    if i == 0:
                        k[i] = 50
                        d[i] = 50
                    else:
                        k[i] = (m1 - 1) * k[i-1] / m1 + rsv[i] / m1
                        d[i] = (m2 - 1) * d[i-1] / m2 + k[i] / m2
                
                # Calculate J
                j = 3 * k - 2 * d
                
                df.loc[mask, 'kdj_k'] = k
                df.loc[mask, 'kdj_d'] = d
                df.loc[mask, 'kdj_j'] = j
            
        return df 