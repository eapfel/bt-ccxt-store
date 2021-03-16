import json
import os
import time
from datetime import datetime, timedelta

import backtrader as bt

from ccxtbt import CCXTStore


class TestStrategy(bt.Strategy):

    def __init__(self):

        self.bought = False
        # To keep track of pending orders and buy price/commission
        self.order = None

    def next(self):
        print(f'{datetime.now()} - next: {self.data0.close[0]}')
        if self.live_data and not self.bought:
            self.buy(size=1)
            self.bought = True

        self.analyzers.ta.pprint()
        self.analyzers.sqn.pprint()

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}, Order Status: {}'.format(data._getstatusname(status), status)
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False

    def notify_order(self, order):
        print(f'Order created - status: {order.Status[order.status]}')
        self.order = order


# absolute dir the script is in
script_dir = os.path.dirname(__file__)
abs_file_path = os.path.join(script_dir, '../params.json')
with open(abs_file_path, 'r') as f:
    params = json.load(f)

cerebro = bt.Cerebro(quicknotify=True)

cerebro.broker.setcash(10.0)

# Add the strategy
cerebro.addstrategy(TestStrategy)

# Create our store
config = {'apiKey': params["binance"]["apikey"],
          'secret': params["binance"]["secret"],
          'enableRateLimit': True,
          'nonce': lambda: str(int(time.time() * 1000)),
          }

store = CCXTStore(exchange='binance', currency='BNB', config=config, retries=5, debug=False)

# Get our data
# Drop newest will prevent us from loading partial data from incomplete candles
hist_start_date = datetime.utcnow() - timedelta(days=20)
to_date = datetime.utcnow() + timedelta(minutes=3)
data = store.getdata(dataname='BNB/USDT', name="BNBUSDT",
                     timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date, todate=to_date,
                     compression=5, ohlcv_limit=1000, debug=False)  # , historical=True)

#
broker = cerebro.getbroker()
broker.setcash(1000.0)

# Add the feed
cerebro.adddata(data)

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")

# Run the strategy
result = cerebro.run()

result[0].analyzers.ta.pprint()
result[0].analyzers.sqn.pprint()
