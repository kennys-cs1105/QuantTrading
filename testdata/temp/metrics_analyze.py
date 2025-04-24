import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from data_loader import DataLoader
from strategy import TradingStrategy
import matplotlib as mpl
import platform

# 设置matplotlib中文字体
if platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows系统
elif platform.system() == 'Linux':
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # Linux系统
elif platform.system() == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS系统
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置seaborn样式
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.5)

class MetricsAnalyzer:
    def __init__(self, signals_df):
        self.signals = signals_df
        
    def analyze_correlations(self):
        """分析各指标与收益率的相关性"""
        # 选择需要分析的指标
        metrics = ['D1_J值', 'D2_J值', 'D1_WR14', 'D2_WR14', 'D1_WR28', 'D2_WR28']
        
        # 计算相关性
        corr_data = self.signals[metrics + ['D1-D2收益率']]
        correlation = corr_data.corr()['D1-D2收益率'].sort_values()
        
        print("\n=== 指标与收益率的相关性分析 ===")
        print(correlation)
        
        # 绘制相关性热图
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_data.corr(), annot=True, cmap='coolwarm', center=0, fmt='.2f')
        plt.title('指标相关性热图', pad=20, fontsize=16)
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def analyze_by_wr_zones(self):
        """根据WR指标的不同区间分析收益率"""
        def categorize_wr(value):
            if value > -20:
                return '超买区间 (>-20)'
            elif value < -80:
                return '超卖区间 (<-80)'
            else:
                return '中性区间 (-80~-20)'
        
        # 对WR14和WR28进行分类
        self.signals['D1_WR14_Zone'] = self.signals['D1_WR14'].apply(categorize_wr)
        self.signals['D1_WR28_Zone'] = self.signals['D1_WR28'].apply(categorize_wr)
        
        # 分析WR14区间的收益率
        wr14_analysis = self.signals.groupby('D1_WR14_Zone').agg({
            'D1-D2收益率': ['count', 'mean', 'std', 'median'],
            '持仓天数': 'mean'
        })
        
        # 分析WR28区间的收益率
        wr28_analysis = self.signals.groupby('D1_WR28_Zone').agg({
            'D1-D2收益率': ['count', 'mean', 'std', 'median'],
            '持仓天数': 'mean'
        })
        
        print("\n=== WR14区间收益率分析 ===")
        print(wr14_analysis)
        print("\n=== WR28区间收益率分析 ===")
        print(wr28_analysis)
        
        # 绘制箱线图
        plt.figure(figsize=(15, 7))
        
        plt.subplot(1, 2, 1)
        sns.boxplot(x='D1_WR14_Zone', y='D1-D2收益率', data=self.signals)
        plt.title('WR14区间收益率分布', pad=20, fontsize=14)
        plt.xlabel('WR14区间', fontsize=12)
        plt.ylabel('收益率 (%)', fontsize=12)
        plt.xticks(rotation=45)
        
        plt.subplot(1, 2, 2)
        sns.boxplot(x='D1_WR28_Zone', y='D1-D2收益率', data=self.signals)
        plt.title('WR28区间收益率分布', pad=20, fontsize=14)
        plt.xlabel('WR28区间', fontsize=12)
        plt.ylabel('收益率 (%)', fontsize=12)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('wr_returns_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def analyze_by_j_value(self):
        """分析J值与收益率的关系"""
        # 将J值分组
        self.signals['D1_J值_Range'] = pd.qcut(self.signals['D1_J值'], q=5, labels=[
            '极低', '较低', '中等', '较高', '极高'
        ])
        
        # 分析不同J值区间的收益率
        j_analysis = self.signals.groupby('D1_J值_Range').agg({
            'D1-D2收益率': ['count', 'mean', 'std', 'median'],
            '持仓天数': 'mean',
            'D1_J值': ['min', 'max']
        })
        
        print("\n=== J值区间收益率分析 ===")
        print(j_analysis)
        
        # 绘制J值与收益率的散点图
        plt.figure(figsize=(12, 8))
        plt.scatter(self.signals['D1_J值'], self.signals['D1-D2收益率'], alpha=0.5)
        plt.xlabel('D1日J值', fontsize=12)
        plt.ylabel('D1-D2收益率 (%)', fontsize=12)
        plt.title('J值与收益率的关系', pad=20, fontsize=16)
        plt.grid(True)
        plt.savefig('j_value_returns_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def analyze_combined_signals(self):
        """分析J值和WR指标组合条件下的收益率"""
        def get_combined_signal(row):
            j_signal = "J值低" if row['D1_J值'] < -10 else "J值高"
            wr_signal = "WR超卖" if row['D1_WR14'] < -80 else ("WR超买" if row['D1_WR14'] > -20 else "WR中性")
            return f"{j_signal}_{wr_signal}"
        
        self.signals['Combined_Signal'] = self.signals.apply(get_combined_signal, axis=1)
        
        # 分析组合信号的收益率
        combined_analysis = self.signals.groupby('Combined_Signal').agg({
            'D1-D2收益率': ['count', 'mean', 'std', 'median'],
            '持仓天数': 'mean'
        })
        
        print("\n=== 组合信号收益率分析 ===")
        print(combined_analysis)
        
        # 绘制组合信号的箱线图
        plt.figure(figsize=(14, 8))
        sns.boxplot(x='Combined_Signal', y='D1-D2收益率', data=self.signals)
        plt.title('组合信号收益率分布', pad=20, fontsize=16)
        plt.xlabel('组合信号类型', fontsize=12)
        plt.ylabel('收益率 (%)', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('combined_signals_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    # 加载数据
    stock_data_path = "/home/kennys/MineX/QuantTrading/dataset/沪深300-2024年至今数据.csv"
    hs300_constituents_path = "/home/kennys/MineX/QuantTrading/dataset/沪深300成分股.csv"
    data_loader = DataLoader(stock_data_path, hs300_constituents_path)
    
    stock_data = data_loader.load_stock_data()
    hs300_constituents = data_loader.load_hs300_constituents()
    
    stock_data = pd.merge(stock_data, hs300_constituents[['code', 'code_name']], on='code', how='inner')
    
    # 运行策略获取信号
    strategy = TradingStrategy()
    prepared_data = strategy.prepare_data(stock_data)
    signals = strategy.find_trading_signals(prepared_data)
    
    if len(signals) > 0:
        # 添加股票名称
        signals = pd.merge(signals, hs300_constituents[['code', 'code_name']], on='code', how='left')
        
        # 创建分析器并进行分析
        analyzer = MetricsAnalyzer(signals)
        
        # 运行各项分析
        analyzer.analyze_correlations()
        analyzer.analyze_by_wr_zones()
        analyzer.analyze_by_j_value()
        analyzer.analyze_combined_signals()
        
        print("\n分析结果已保存为图表文件：")
        print("1. correlation_heatmap.png - 指标相关性热图")
        print("2. wr_returns_boxplot.png - WR指标区间收益率分布")
        print("3. j_value_returns_scatter.png - J值与收益率散点图")
        print("4. combined_signals_boxplot.png - 组合信号收益率分布")
    else:
        print("\n未找到交易信号，无法进行分析")

if __name__ == "__main__":
    main() 