# README

## 背景

根据股票量化策略筛选个股

## 输入数据

获取沪深主板、创业板所有个股最近30天的股票数据，包括"date,code,open,high,low,close,preclose,volume,amount,turn"信息

获取方式通过`import baostock as bs`第三方库进行获取

## 策略

根据获取的股票数据进行筛选，筛选条件：

1. 最近10日内，某一日（D1）出现上涨，第二天（D2）出现大于等于三倍D1成交量的放量上涨
2. D2放量阳线出现上影线
3. D2阳线突破前期趋势

## 输出

请筛选个股，返回包含"date,code,open,high,low,close,preclose,volume,amount,turn"的dataframe