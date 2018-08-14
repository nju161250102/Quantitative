# coding=utf-8


class TradeModel(object):
    """
    :param h_data_dict 历史行情数据（前复权）{ 股票代号 ：DataFrame }
    """

    def __init__(self, h_data_dict):
        self._data = h_data_dict
        self._money = 10000000.0
        self._stocks = []
        self._rates = []

    def _buy(self, code, price):
        num = int(self._money / (price * 100)) * 100
        if num <= 0:
            return
        # 剩余资金足够购买
        self._money -= num * price
        for stock in self._stocks:
            if code == stock["code"]:
                stock["num"] += num
                return
        self._stocks.append({"code": code, "num": num})

    def _sell(self, code, price):
        for stock in self._stocks:
            if code == stock["code"]:
                self._money += stock["num"] * price
                self._stocks.remove(stock)

    def fit(self, trade_list):
        for index, trade in enumerate(trade_list):
            code = trade["code"]
            buy_price = trade["buy_price"]
            sell_price = trade["sell_price"]
            if buy_price is not None:
                self._buy(code, self._data[code]["open"][index])
            if sell_price is not None:
                self._sell(code, self._data[code]["open"][index])
            # 计算总资产
            money = self._money
            for stock in self._stocks:
                money += stock["num"] * self._data[stock["code"]]["close"][index]
            self._rates.append(1 - money / 10000000.0)
        return self._rates
