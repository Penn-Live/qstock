# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 15:12:06 2022

@author: Jinyi Zhang
"""

import pandas as pd
import requests
from tqdm import tqdm
import json

from qstock.data import demjson
from qstock.data.util import trans_num

###同业拆借利率
def ib_rate(market='sh',fc=None):
    '''market:同业拆借市场简称，各个市场英文缩写为：
    {'sh':'上海银行同业拆借市场','ch':'中国银行同业拆借市场','l':'伦敦银行同业拆借市场',
     'eu':'欧洲银行同业拆借市场','hk':'香港银行同业拆借市场','s':'新加坡银行同业拆借市场'}
    香港市场，fc可选：'港元'，'美元','人民币'；新加坡市场，fc可选：'星元','美元';
    伦敦市场，fc可选：'英镑','美元','欧元','日元'；
    
    '''
    if fc is None:
        fc='USD'
    if market=='ch':
        fc='CNY'
        period=['隔夜','1周','2周','3周','1月','2月','3月','4月','6月','9月','1年']
    elif market=='eu':
        fc='EUR'
        period=['1周','2周','3周','1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','1年']
    elif market=='l':
        period=['隔夜','1周','1月','2月','3月','8月']
    elif market=='hk':
        period=['隔夜','1周','2周','1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月''1年']
    elif market=='s':
        period=['1月','2月','3月','6月','9月','1年']
    else:
        fc='CNY'
        period=['隔夜','1周','2周','1月','3月','6月','9月','1年']
        
    df=interbank_rate(market, fc, period[0])[['报告日','利率']]
    df=df.rename(columns={'利率':period[0]})
    for p in period[1:]:
        try:
            temp=interbank_rate(market, fc, p)[['报告日','利率']]
            temp=temp.rename(columns={'利率':p})
            df=pd.merge(df,temp,how='outer')
        except:
            continue
    return df.sort_values('报告日')

def interbank_rate(market,fc,indicator):
    """
    获取东方财富银行间市场拆借利率数据
    """
    market_dict = {
        "上海银行同业拆借市场": "001",
        "中国银行同业拆借市场": "002",
        "伦敦银行同业拆借市场": "003",
        "欧洲银行同业拆借市场": "004",
        "香港银行同业拆借市场": "005",
        "新加坡银行同业拆借市场": "006",
        "sh": "001",
        "ch": "002",
        "l": "003",
        "eu": "004",
        "hk": "005",
        "s": "006",
    }
    fc_dict = {
        "人民币": "CNY",
        "英镑": "GBP",
        "欧元": "EUR",
        "美元": "USD",
        "港币": "HKD",
        "港元": "HKD",
        "星元": "SGD",
        "新元": "SGD",
    }
    
    if fc.isalpha():
        fc=fc.upper()
    else:
        fc=fc_dict[fc]
    if market.isalpha():
        market=market.lower()
    market=market_dict[market]
    
    if market=="005" and fc=="CNY":
        fc="CNH"
    
    indicator_dict = {
        "隔夜": "001",
        "1周": "101",
        "2周": "102",
        "3周": "103",
        "1月": "201",
        "2月": "202",
        "3月": "203",
        "4月": "204",
        "5月": "205",
        "6月": "206",
        "7月": "207",
        "8月": "208",
        "9月": "209",
        "10月": "210",
        "11月": "211",
        "1年": "301",
    }
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RPT_IMP_INTRESTRATEN",
        "columns": "REPORT_DATE,REPORT_PERIOD,IR_RATE,CHANGE_RATE,INDICATOR_ID,LATEST_RECORD,MARKET,MARKET_CODE,CURRENCY,CURRENCY_CODE",
        "quoteColumns": "",
        "filter": f"""(MARKET_CODE="{market}")(CURRENCY_CODE="{fc}")(INDICATOR_ID="{indicator_dict[indicator]}")""",
        "pageNumber": "1",
        "pageSize": "500",
        "sortTypes": "-1",
        "sortColumns": "REPORT_DATE",
        "source": "WEB",
        "client": "WEB",
        "p": "1",
        "pageNo": "1",
        "pageNum": "1",
        "_": "1653376974939",
    }
    res = requests.get(url, params=params)
    data_json = res.json()
    total_page = data_json["result"]["pages"]
    df = pd.DataFrame()
    for page in tqdm(range(1, total_page + 1), leave=False):
        params.update(
            {
                "pageNumber": page,
                "p": page,
                "pageNo": page,
                "pageNum": page,
            }
        )
        r = requests.get(url, params=params)
        data_json = r.json()
        temp_df = pd.DataFrame(data_json["result"]["data"])
        df = pd.concat([df, temp_df], ignore_index=True)
    df.columns = [
        "报告日",
        "-",
        "利率",
        "涨跌",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]
    df = df[
        [
            "报告日",
            "利率",
            "涨跌",
        ]
    ]
    df["报告日"] = pd.to_datetime(df["报告日"]).dt.date
    df["利率"] = pd.to_numeric(df["利率"])
    df["涨跌"] = pd.to_numeric(df["涨跌"])
    df.sort_values(["报告日"], inplace=True)
    df.reset_index(inplace=True, drop=True)
    return df

##############################################################################
def macro_data(flag=None):
    '''
    获取宏观经济常见指标
    flag:lpr:贷款基准利率；ms：货币供应量；cpi:消费者物价指数；
    ppi:工业品出厂价格指数;pmi:采购经理人指数
    默认返回gdp数据
        
    '''
    if flag=='lpr':
        return lpr()
    elif flag=='ms':
        return ms()
    elif flag=='cpi':
        return cpi()
    elif flag=='ppi':
        return ppi()
    elif flag=='pmi':
        return ms()
    elif flag=='pmi':
        return cpi()
    else:
        return gdp()


#中国贷款报价利率
def lpr():
    """
    http://data.eastmoney.com/cjsj/globalRateLPR.html
    LPR品种详细数据
    """
    url = "http://datacenter.eastmoney.com/api/data/get"
    params = {
        "type": "RPTA_WEB_RATE",
        "sty": "ALL",
        "token": "894050c76af8597a853f5b408b759f5d",
        "p": "1",
        "ps": "2000",
        "st": "TRADE_DATE",
        "sr": "-1",
        "var": "WPuRCBoA",
        "rt": "52826782",
    }
    res = requests.get(url, params=params)
    data_text = res.text
    data_json = json.loads(data_text.strip("var WPuRCBoA=")[:-1])
    df = pd.DataFrame(data_json["result"]["data"])
    df["TRADE_DATE"] = pd.to_datetime(df["TRADE_DATE"]).dt.date
    df["LPR1Y"] = pd.to_numeric(df["LPR1Y"])
    df["LPR5Y"] = pd.to_numeric(df["LPR5Y"])
    df["RATE_1"] = pd.to_numeric(df["RATE_1"])
    df["RATE_2"] = pd.to_numeric(df["RATE_2"])
    df.sort_values(["TRADE_DATE"], inplace=True)
    df.reset_index(inplace=True, drop=True)
    new_cols=['日期','1年lpr','5年lpr','短期(6个月至1年)','中长期(5年以上)']
    df=df.rename(columns=dict(zip(df.columns,new_cols)))
    return df

#我国宏观经济指标
def ms():
    """
    东方财富-货币供应量
    http://data.eastmoney.com/cjsj/hbgyl.html
    """
    url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
    params = {
        "type": "GJZB",
        "sty": "ZGZB",
        "p": "1",
        "ps": "200",
        "mkt": "11",
    }
    res = requests.get(url=url, params=params)
    data_text = res.text
    tmp_list = data_text[data_text.find("[") + 2 : -3]
    tmp_list = tmp_list.split('","')
    res_list = []
    for li in tmp_list:
        res_list.append(li.split(","))
    columns = [
        "月份",
        "M2(亿)",
        "M2同比",
        "M2环比",
        "M1(亿)",
        "M1同比",
        "M1环比",
        "M0(亿)",
        "M0同比",
        "M0环比",
    ]
    df = pd.DataFrame(res_list, columns=columns)
    cols = ['月份']
    df = trans_num(df, cols).round(3)
    return df

def cpi():
    """
    东方财富-中国居民消费价格指数
    http://data.eastmoney.com/cjsj/cpi.html
    """
    url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
    params = {
        "type": "GJZB",
        "sty": "ZGZB",
        "js": "({data:[(x)],pages:(pc)})",
        "p": "1",
        "ps": "2000",
        "mkt": "19",
        "pageNo": "1",
        "pageNum": "1",
        "_": "1603023435552",
    }
    res = requests.get(url, params=params)
    data_text = res.text
    data_json = demjson.decode(data_text[data_text.find("{") : -1])
    df = pd.DataFrame([item.split(",") for item in data_json["data"]])
    df.columns = [
        "月份",
        "全国",
        "全国比",
        "全国环比",
        "全国累计",
        "城市",
        "城市同比",
        "城市环比",
        "城市累计",
        "农村",
        "农村同比",
        "农村环比",
        "农村累计",]
    df.sort_values(["月份"], inplace=True)
    df.reset_index(inplace=True, drop=True)
    cols = ['月份']
    df = trans_num(df, cols).round(3)
    return df


def gdp():
    """
    东方财富-中国国内生产总值
    http://data.eastmoney.com/cjsj/gdp.html
    """
    url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
    params = {
        "type": "GJZB",
        "sty": "ZGZB",
        "js": "({data:[(x)],pages:(pc)})",
        "p": "1",
        "ps": "2000",
        "mkt": "20",
        "pageNo": "1",
        "pageNum": "1",
        "_": "1603023435552",
    }
    res = requests.get(url, params=params)
    data_text = res.text
    data_json = demjson.decode(data_text[data_text.find("{") : -1])
    df = pd.DataFrame([item.split(",") for item in data_json["data"]])
    df.columns = [
        "季度",
        "国内生产总值",
        "同比增长",
        "第一产业",
        "第一产业同比",
        "第二产业",
        "第二产业同比",
        "第三产业",
        "第三产业同比",]
    
    cols = ['季度']
    df = trans_num(df, cols).round(3)
    return df


def ppi():
    """
    中国工业品出厂价格指数
    http://data.eastmoney.com/cjsj/ppi.html
    """
    url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    }
    params = {
        "cb": "datatable6912149",
        "type": "GJZB",
        "sty": "ZGZB",
        "js": "({data:[(x)],pages:(pc)})",
        "p": "1",
        "ps": "2000",
        "mkt": "22",
        "pageNo": "1",
        "pageNum": "1",
        "_": "1603023435552",
    }
    res = requests.get(url, params=params, headers=headers)
    data_text = res.text
    data_json = demjson.decode(data_text[data_text.find("{") : -1])
    df = pd.DataFrame([item.split(",") for item in data_json["data"]])
    df.columns = ["月份", "当月", "当月同比", "累计"]
    return df


def pmi():
    """
    中国采购经理人指数
    http://data.eastmoney.com/cjsj/pmi.html
    """
    url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
    params = {
        "type": "GJZB",
        "sty": "ZGZB",
        "js": "({data:[(x)],pages:(pc)})",
        "p": "1",
        "ps": "2000",
        "mkt": "21",
        "pageNo": "1",
        "pageNum": "1",
        "_": "1603023435552",
    }
    res = requests.get(url, params=params)
    data_text = res.text
    data_json = demjson.decode(data_text[data_text.find("{") : -1])
    df = pd.DataFrame([item.split(",") for item in data_json["data"]])
    df.columns = [
        "月份",
        "制造业指数",
        "制造业同比",
        "非制造业指数",
        "非制造业同比",
    ]
    df["制造业指数"] = pd.to_numeric(df["制造业指数"])
    df["制造业同比"] = pd.to_numeric(df["制造业同比"])
    df["非制造业指数"] = pd.to_numeric(df["非制造业指数"])
    df["非制造业同比"] = pd.to_numeric(df["非制造业同比"])
    return df
