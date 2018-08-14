# coding=utf-8
import matplotlib.pyplot as plt


class TradeModel(object):
    """
    :param h_data_dict (dict) 历史行情数据（前复权）
    { 股票代号 ：DataFrame }
    :param init_money 初始资金
    """

    def __init__(self, h_data_dict, init_money=1000000.0):
        self._data = h_data_dict
        self._init_money = init_money
        self._money = init_money
        self._stocks = []
        self._rates_dict = {}

    def _check(self, code, date, price):
        """
        :param code (str) 股票代号
        :param date (str) 交易日期 yyyy-MM-dd
        :param price (double, str={"open","close"}) 设定成交价
        """
        # 检查历史数据是否含有此股票
        if code not in self._data.keys():
            raise KeyError("The stock %s in history data" % code)
        # 检查日期范围
        if date not in self._data[code].index:
            raise KeyError("Date out of range: %s" % date)
        # 价格转换与校验
        if price == "open":
            price = self._data[code].ix[date, "open"]
        elif price == "close":
            price = self._data[code].ix[date, "close"]
        elif price < self._data[code].ix[date, "low"] or price > self._data[code].ix[date, "high"]:
            return None  # 价格不在当日区间
        return price

    def _buy(self, code, date, price, show_info=False):
        """
        :param code (str) 股票代号
        :param date (str) 交易日期 yyyy-MM-dd
        :param price (double, str={"open","close"}) 设定成交价
        :param show_info (bool) 是否显示交易记录
        """
        price = self._check(code, date, price)
        if price is None:
            return
        # 计算购买数量
        num = int(self._money / (price * 100)) * 100
        # 资金不足
        if num <= 0:
            if show_info:
                print "[%s] Buy %s Failed: Money is not enough" % (date, code)
            return
        # 剩余资金足够购买
        self._money -= num * price
        if show_info:
            print "[%s] Buy %s : %s * %s" % (date, code, num, price)
        for stock in self._stocks:
            if code == stock["code"]:
                stock["num"] += num
                return
        self._stocks.append({"code": code, "num": num})

    def _sell(self, code, date, price, show_info=False):
        """
        :param code (str) 股票代号
        :param date (str) 交易日期 yyyy-MM-dd
        :param price (double, str={"open","close"}) 设定成交价
        :param show_info (bool) 是否显示交易记录
        """
        price = self._check(code, date, price)
        if price is None:
            return
        for stock in self._stocks:
            if code == stock["code"]:
                if show_info:
                    print "[%s] Sell %s : %s * %s" % (date, code, stock["num"], price)
                self._money += stock["num"] * price
                self._stocks.remove(stock)
                return

    def _transact(self, date, transaction):
        """
        完成一次交易
        :param date: 日期
        :param transaction: (action={"buy","sell"}, code, price)操作元组
        """
        action = transaction[0]
        if action == "buy":
            self._buy(transaction[1], date, transaction[2])
        elif action == "sell":
            self._sell(transaction[1], date, transaction[2])
        else:
            raise Exception("Wrong action type: %s" % action)

    def fit(self, transaction_dicts):
        """
        输入交易策略
        :param transaction_dicts: 交易策略组
        { 策略名 : {date : (action, code, price)} }
        """
        self._rates_dict = {}
        for name, transaction_dict in transaction_dicts.items():
            date_list = transaction_dict.keys()
            date_list.sort()
            rate_list = []
            for date in date_list:
                self._transact(date, transaction_dict[date])
                # 以收盘价计算收益率
                money = self._money
                for stock in self._stocks:
                    money += stock["num"] * self._data[stock["code"]].ix[date, "close"]
                rate_list.append(1 - money / self._init_money)
            self._rates_dict[name] = rate_list
        return self._rates_dict

    def plot(self):
        if len(self._rates_dict) == 0:
            return
        for name, rate_list in self._rates_dict.items():
            plt.plot(rate_list, '-')
        plt.show()
