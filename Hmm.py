# -*- coding:utf-8 -*-
import numpy as np
import tushare as ts
from hmmlearn.hmm import GaussianHMM
from TradeModel import TradeModel


def pre_hmm(df):
    """
    hmm数据预处理
    :param df: 待处理数据，列名同tushare返回格式
    :return: [最高最低价格对数差，每5日收盘价对数差，每5日成交量对数差]
    """
    volume = df['volume']
    close = df['close']
    log_del = np.log(np.array(df['high'])) - np.log(np.array(df['low']))
    log_ret_5 = np.log(np.array(close[5:])) - np.log(np.array(close[:-5]))
    log_vol_5 = np.log(np.array(volume[5:])) - np.log(np.array(volume[:-5]))
    log_del = log_del[5:]
    return np.column_stack([log_del, log_ret_5, log_vol_5])


def main(code, start_date, end_date, state_num=3):
    stock_data = ts.get_h_data(code, start=start_date).sort_index()
    # 切分训练集，注意区间左闭右开
    train_data = stock_data.loc[:end_date]
    # 训练模型
    model = GaussianHMM(n_components=state_num, covariance_type="full", n_iter=1000).fit(pre_hmm(train_data))
    # 模型回测
    hidden_states = model.predict(pre_hmm(train_data))
    strategy = {}
    for n in range(0, state_num):
        strategy[n] = {}
    for index, state in enumerate(hidden_states):
        date = train_data.index[5 + index].strftime("%Y-%m-%d")
        for n in range(0, state_num):
            strategy[n][date] = ()
            if index == 0 and state == n:
                strategy[n][date] = ("buy", code, "close")
            elif index > 0 and state != hidden_states[index-1]:
                if hidden_states[index-1] == n:
                    strategy[n][date] = ("sell", code, "close")
                elif state == n:
                    strategy[n][date] = ("buy", code, "close")
    trade_model = TradeModel({code: stock_data})
    trade_model.fit(strategy)
    trade_model.plot()


if __name__ == "__main__":
    main("000010", "2018-01-13", "2018-07-13")
