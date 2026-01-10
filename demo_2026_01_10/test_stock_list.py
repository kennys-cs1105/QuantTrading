"""
测试脚本：验证股票列表获取功能
"""
import sys
sys.path.append('/home/kennys/workspace/MineX/QuantTrading/demo_2026_01_10')

from stock_screening import get_main_board_and_chinext_stocks
import pandas as pd

if __name__ == "__main__":
    print("开始测试股票列表获取功能...\n")
    
    try:
        df_stocks = get_main_board_and_chinext_stocks()
        
        print(f"\n测试结果：")
        print(f"成功获取 {len(df_stocks)} 只股票")
        
        if len(df_stocks) > 0:
            print("\n前10只股票：")
            print(df_stocks.head(10))
            
            print("\n股票分布：")
            # 统计各板块股票数量
            sh_count = len(df_stocks[df_stocks['code'].str.startswith('sh.')])
            sz_main_count = len(df_stocks[df_stocks['code'].str.startswith('sz.000')])
            sz_chinext_count = len(df_stocks[df_stocks['code'].str.startswith('sz.300')])
            
            print(f"上海主板: {sh_count} 只")
            print(f"深圳主板: {sz_main_count} 只")
            print(f"创业板: {sz_chinext_count} 只")
        else:
            print("警告：未获取到任何股票！")
    
    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()

