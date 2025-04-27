import numpy as np

class TechnicalAnalysis:
    @staticmethod
    def calculate_ma(df, window=20):
        """Calculate Moving Average for each stock"""
        return df.groupby('code')['close'].transform(lambda x: x.rolling(window=window).mean())
    
    @staticmethod
    def calculate_kdj(df, n=9, m1=3, m2=3):
        """
        Calculate KDJ indicator
        n: RSV period
        m1: K period
        m2: D period
        """
        df = df.copy()
        
        # Group by code to calculate KDJ for each stock
        for code in df['code'].unique():
            mask = df['code'] == code
            df_stock = df[mask].copy()
            
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

    @staticmethod
    def calculate_wr(df, period=14):
        """
        Calculate Williams %R indicator
        period: lookback period, typically 14 days
        Formula: WR = (Highest High - Close)/(Highest High - Lowest Low) * -100
        """
        df = df.copy()
        
        # Group by code to calculate WR for each stock
        for code in df['code'].unique():
            mask = df['code'] == code
            df_stock = df[mask].copy()
            
            # Calculate highest high and lowest low for the period
            high_list = df_stock['high'].rolling(window=period, min_periods=1).max()
            low_list = df_stock['low'].rolling(window=period, min_periods=1).min()
            
            # Calculate Williams %R
            wr = ((high_list - df_stock['close']) / (high_list - low_list) * -100)
            
            df.loc[mask, f'wr_{period}'] = wr
            
        return df 

    @staticmethod
    def calculate_macd(df, fast_period=12, slow_period=26, signal_period=9):
        """
        Calculate MACD indicator
        fast_period: short EMA period (default 12)
        slow_period: long EMA period (default 26)
        signal_period: signal line EMA period (default 9)
        """
        df = df.copy()
        for code in df['code'].unique():
            mask = df['code'] == code
            df_stock = df[mask].copy()
            close = df_stock['close']
            ema_fast = close.ewm(span=fast_period, adjust=False).mean()
            ema_slow = close.ewm(span=slow_period, adjust=False).mean()
            dif = ema_fast - ema_slow
            dea = dif.ewm(span=signal_period, adjust=False).mean()
            macd = 2 * (dif - dea)
            df.loc[mask, 'macd_dif'] = dif.values
            df.loc[mask, 'macd_dea'] = dea.values
            df.loc[mask, 'macd'] = macd.values
        return df

    @staticmethod
    def calculate_boll(df, window=20, num_std=2):
        """
        Calculate Bollinger Bands (BOLL)
        window: moving average window (default 20)
        num_std: number of standard deviations (default 2)
        """
        df = df.copy()
        for code in df['code'].unique():
            mask = df['code'] == code
            df_stock = df[mask].copy()
            mid = df_stock['close'].rolling(window=window, min_periods=1).mean()
            std = df_stock['close'].rolling(window=window, min_periods=1).std()
            upper = mid + num_std * std
            lower = mid - num_std * std
            df.loc[mask, f'boll_mid_{window}'] = mid.values
            df.loc[mask, f'boll_upper_{window}'] = upper.values
            df.loc[mask, f'boll_lower_{window}'] = lower.values
        return df 