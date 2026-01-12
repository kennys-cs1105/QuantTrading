"""
股票量化策略筛选主程序

根据以下条件筛选个股：
1. 最近10日内，某一日（D1）出现上涨，第二天（D2）出现大于等于三倍D1成交量的放量上涨
2. D2放量阳线出现上影线
3. D2阳线突破前期趋势
4. 最新日期的收盘价和D2的收盘价在±1%内
"""

from stock_screening import screen_stocks
import pandas as pd


def main():
    """
    主函数：执行股票筛选并保存结果
    """
    print("=" * 60)
    print("股票量化策略筛选程序")
    print("=" * 60)
    
    # 执行筛选
    result = screen_stocks()
    
    # 显示结果
    if len(result) > 0:
        print("\n" + "=" * 60)
        print("筛选结果:")
        print("=" * 60)
        print(result)
        
        # 保存结果到CSV文件
        output_file = "/home/kennys/workspace/MineX/QuantTrading/demo_2026_01_10/2025-01-12-main.csv"
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n结果已保存到: {output_file}")
        
        # 显示统计信息
        print("\n" + "=" * 60)
        print("统计信息:")
        print("=" * 60)
        print(f"满足条件的记录数: {len(result)}")
        print(f"涉及股票数量: {result['code'].nunique()}")
        print(f"日期范围: {result['date'].min()} 至 {result['date'].max()}")
        
        # 按股票代码分组统计
        print("\n各股票满足条件的次数:")
        stock_counts = result.groupby(['code']).size().sort_values(ascending=False)
        print(stock_counts.head(10))
        
    else:
        print("\n未找到满足条件的股票")
        print("提示：可以尝试放宽筛选条件或检查数据源")


if __name__ == "__main__":
    main()
