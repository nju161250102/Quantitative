# -*- coding:utf-8 -*-
import datetime
import numpy as np
import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance as mpf
from hmmlearn.hmm import GaussianHMM
from TradeModel import TradeModel


def draw_pic(hist_data):
    data_list = []
    date_list = []
    dates = len(hist_data)
    for date, row in hist_data.iterrows():
        date_list.append(date)
        open, high, close, low = row[:4]
        datas = (dates, open, high, low, close)
        dates -= 1
        data_list.append(datas)
    date_list.reverse()

    # 先设定一个日期转换方法
    def format_date(x, pos=None):
        if x < 0 or x > len(date_list) - 1:
            return ''
        return date_list[int(x)]

    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.xticks(rotation=45)
    plt.yticks()
    mpf.candlestick_ohlc(ax, data_list, width=0.6, colorup="red", colordown="green")
    plt.show(dpi=300)
    # model = TradeModel("600714", "2018-01-11")
    # plt.plot(model.fit(trade), '-')
    plt.show()


def pre_hmm(data):
    volume = data['volume']
    close = data['close']
    logDel = np.log(np.array(data['high'])) - np.log(np.array(data['low']))
    logRet_5 = np.log(np.array(close[5:])) - np.log(np.array(close[:-5]))
    logVol_5 = np.log(np.array(volume[5:])) - np.log(np.array(volume[:-5]))
    logDel = logDel[5:]
    A = np.column_stack([logDel, logRet_5, logVol_5])
    return A


def main():
    code = "000010"
    stock_data = ts.get_h_data(code, start="2017-08-13").sort_index()
    print stock_data.head(10)
    plt.rcParams['figure.figsize'] = (int(len(stock_data.index) / 15), 4.0)
    train_data = pre_hmm(stock_data.ix[:"2018-03-13"])
    model = GaussianHMM(n_components=6, covariance_type="full", n_iter=1000).fit(train_data)

    trade_list = []
    for state in range(0, 6):
        t_list = [{"code": code, "buy_price": None, "sell_price": None}] * 5
        train_result = model.predict(train_data)
        index = 0
        for day in pd.to_datetime(stock_data.ix["2017-08-20":"2018-03-12"].index, unit='s').strftime('%Y-%m-%d'):
            if train_result[index] == state:
                t_list.append({"code": code, "buy_price": stock_data.ix[:"2018-03-12"].ix[day, "close"], "sell_price": None})
            else:
                t_list.append({"code": code, "buy_price": None, "sell_price": stock_data.ix[:"2018-03-12"].ix[day, "close"]})
            index += 1
        trade_list.append(t_list)

    for t_list in trade_list:
        trade_model = TradeModel({code: stock_data.ix["2017-08-13":"2018-03-14"]})
        plt.plot(trade_model.fit(t_list), '-')
    plt.show(dpi=300)

    trade_list = []
    for state in range(0, 6):
        t_list = []
        for day in pd.to_datetime(stock_data.ix["2018-03-13":].index, unit='s').strftime('%Y-%m-%d'):
            test_data = stock_data.ix[:day]
            hidden_states = model.predict(pre_hmm(test_data))
            if hidden_states[-1] == state:
                t_list.append({"code": code, "buy_price": test_data.ix[day, "close"], "sell_price": None})
            else:
                t_list.append({"code": code, "buy_price": None, "sell_price": test_data.ix[day, "close"]})
        trade_list.append(t_list[0:-1])

    for t_list in trade_list:
        trade_model = TradeModel({code: stock_data.ix["2018-03-14":]})
        plt.plot(trade_model.fit(t_list), '-')
    plt.show(dpi=300)


if __name__ == "__main__":
    main()
