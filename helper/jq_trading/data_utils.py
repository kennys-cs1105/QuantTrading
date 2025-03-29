from typing import Union, List, str

import os
import time
from pathlib import Path
import pandas as np
import datetime
import numpy as np

from jqdatasdk import *

"""
股票行情获取
- 获取所有a股股票列表
- 获取单个股票行情数据
- 导出股票行情数据
- 转换股票行情周期
- 获取单个股票财务指标
- 获取单个股票估值指标
"""

auth("account", "password") # jqtrading api

# set pd.dataframe
pd.set_option("display.max_rows", 10000)
pd.set_option("display.max_columns", 1000)


def get_stock_list():
    """
    获取股票列表
    .XSHG -> 上证  .XSHE -> 深证
    
    return:
        stock_list(List), 股票代码列表
    """

    return list(get_all_securities(["stock"]).index)


def get_single_stock_price(
        stock_code: Union[int, List],
        start_date: str,
        end_date: str,
        time_frequency: str
):
    """
    获取单个股票数据
    
    params:
        stock_code (Union[int, List]): 单个股票代码或列表
        start_date (str): 起始时间 xx-xx-xx
        end_date (str): 终止时间 xx-xx-xx
        time_frequency (str): 行情周期 "daily" "Xd" "Xm"    
    
    return:
        data(pd.DataFrame), 单个股票的行情数据
    """
    data = get_price(
        security=stock_code,
        start_date=start_date,
        end_date=end_date,
        frequency=time_frequency,
        panel=False
    )

    return data


def export_stock_data(
        stock_data: pd.DataFrame,
        save_dir: Union[str, Path],
        data_type: str
):
    """
    导出股票行情数据

    params:
        stock_data (pd.DataFrame): 股票行情数据
        save_dir (Union[str, Path]): 保存目录
        data_type (str): 股票数据类型, 如price, finance
    """
    save_path = os.path.join(save_dir, f"{data_type}.csv")
    stock_data.to_csv(save_path)
    print(f"Stock data saved to {save_path}...")


def transfer_price_frequency(
        stock_data: pd.DataFrame,
        time_frequency: str
):
    """
    转换股票行情周期 (例如日K转换周K)

    params:
        stock_data (pd.DataFrame): 股票行情数据
        time_frequency (str): 需要转换的行情周期
    
    returns:
        转换后的目标行情周期行情数据
    """
    df_target = pd.DataFrame()
    df_target["open"] = stock_data["open"].resample(time_frequency).first()
    df_target["close"] = stock_data["close"].resample(time_frequency).last()
    df_target["high"] = stock_data["high"].resample(time_frequency).max()
    df_target["low"] = stock_data["low"].resample(time_frequency).min()

    return df_target


def get_single_finance(
        stock_code: Union[int, List],
        date: str,
        stock_data: pd.DataFrame
):
    """
    获取单个股票的财务指标

    params:
        stock_code (Union[int, List]): 股票代码或列表
        date (str): 需要查询的日期, 例如年份/季度/月份
        stock_data: 股票行情数据
    
    returns:
        过滤后的单个股票的财务指标
    """
    data = get_fundamentals(
        query(indicator).filter(indicator.code == stock_code),
        date=date,
        statDate=stock_data
    )

    return data


def get_single_valuation(
        stock_code: Union[int, List],
        date: str,
        stock_data: pd.DataFrame
):
    """
    获取单个股票估值指标

    params:
        stock_code (Union[int, List]): 股票代码或列表
        date (str): 需要查询的日期, 例如年份/季度/月份
        stock_data: 股票行情数据
    
    returns:
        过滤后的单个股票的估值指标
    """
    data = get_fundamentals(
        query(valuation).filter(valuation.code == stock_code),
        date=date,
        statDate=stock_data
    )