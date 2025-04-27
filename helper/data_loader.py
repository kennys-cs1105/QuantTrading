import os
import pandas as pd


class DataLoader:
    """
    数据加载
    """
    def __init__(self, 
                 stock_data_path, 
                 hs300_constituents_path):
        self.stock_data_path = stock_data_path
        self.hs300_constituents_path = hs300_constituents_path
        
    def load_hs300_constituents(self):
        """Load HS300 constituent stocks data from CSV file"""
        if not os.path.exists(self.hs300_constituents_path):
            raise FileNotFoundError(f"HS300 constituents file not found: {self.hs300_constituents_path}")
            
        df = pd.read_csv(self.hs300_constituents_path)
        df['updateDate'] = pd.to_datetime(df['updateDate'])
        return df
        
    def load_stock_data(self):
        """Load stock price data from CSV file"""
        if not os.path.exists(self.stock_data_path):
            raise FileNotFoundError(f"Stock data file not found: {self.stock_data_path}")
            
        df = pd.read_csv(self.stock_data_path)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['code', 'date'])
        return df 