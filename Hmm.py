# -*- coding:utf-8 -*-
import numpy as np
import tushare as ts
from hmmlearn.hmm import GaussianHMM
from TradeModel import TradeModel


class Hmm(object):

    def __init__(self, code, start_date, end_date, state_num=3):
        self.code = code
        self.stock_data = ts.get_h_data(code, start=start_date).sort_index()
        self.state_num = state_num
        # 切分训练集
        train_data = self.stock_data.loc[:end_date]
        # 训练模型
        model = GaussianHMM(n_components=state_num, covariance_type="full", n_iter=1000).fit(self._pre_hmm(train_data))
        # 模型回测
        hidden_states = model.predict(self._pre_hmm(train_data))
        trade_model = TradeModel({code: self.stock_data})
        trade_model.fit(self._get_strategy(hidden_states))
        trade_model.plot()
        # 切分测试集
        hidden_states = model.predict(self._pre_hmm(self.stock_data.loc[end_date:]))
        # hidden_states = []
        # num = 1
        # for date in self.stock_data.loc[end_date:].index.strftime("%Y-%m-%d"):
        #     test_data = self.stock_data.loc[:date]
        #     if num % 5 == 0:
        #         model = GaussianHMM(n_components=state_num, covariance_type="full", n_iter=1000).fit(self._pre_hmm(test_data))
        #     hidden_states.append(model.predict(self._pre_hmm(test_data))[-1])
        trade_model.fit(self._get_strategy(hidden_states))
        trade_model.plot()

    def _pre_hmm(self, df):
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

    def _get_strategy(self, hidden_states):
        strategy = {}
        for n in range(0, self.state_num):
            strategy[n] = {}
        for index, state in enumerate(hidden_states):
            date = self.stock_data.index[5 + index].strftime("%Y-%m-%d")
            for n in range(0, self.state_num):
                strategy[n][date] = ()
                if index == 0 and state == n:
                    strategy[n][date] = ("buy", self.code, "close")
                elif index > 0 and state != hidden_states[index - 1]:
                    if hidden_states[index - 1] == n:
                        strategy[n][date] = ("sell", self.code, "close")
                    elif state == n:
                        strategy[n][date] = ("buy", self.code, "close")
        return strategy


if __name__ == "__main__":
    Hmm("300137", "2017-07-13", "2018-05-13", state_num=5)
