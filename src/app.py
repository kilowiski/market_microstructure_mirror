import tkinter as tk
from queue import Queue
from threading import Thread

from book_keeper.main import BookKeeper
from gateway.market_data_stream import MarketDataStream
from gateway.data_stream import DataStream
from gateway.main import TradeExecutor
from risk_manager.main import RiskManager
from trading_engine.main import TradingStrategy
from datetime import datetime

# use this to create get requests
from rest_connect.rest_factory import *

# from training_engine.review_engine import ReviewEngine
import time
import random

# this is offset to timestamp, ensure it is in sync with server
offset = 15000


class ExecManager:
    def __init__(self, tradeExecutorObj, bookKeeperObj, restGateway) -> None:
        self.queue = Queue()
        self.tradeExecutor = tradeExecutorObj
        self.bookKeeper = bookKeeperObj

        self.restGateway = restGateway

        # probably pass a obj
        self.strategy = TradingStrategy(self.queue)
        self.tradeExecutor.connect()

    def updateQueue(self, s):
        output = (s["datetime"], s["lastprice"])
        print(f"test the callback {output}")
        self.queue.put(output)

    def execStrat(self, s):
        check = s["lastprice"]
        print(f"what is S even {check}")
        # what is S even {'lastprice': '', 'lastquantity': '', 'bestbidprice': '67150.00', 'bestbidquantity': '3.000', 'bestaskprice': '67430.90', 'bestaskquantity': '6.000', 'datetime': datetime.datetime(2024, 6, 1, 19, 13, 48, 104897)}

        if s["lastprice"] != "":
            """
            1. update book
            2. after book update, check with risk if need liquidate
            3. if risk_liquidate
                a. create liquidate order
                b. cancel standing order
            4. if no risk_liquidate
                a. call strategy to generate signal
                b. call risk to check order doable or not
                    i   ) Risk Metrics OK?
                    ii  ) Check if there is a pending order.
                    iii ) If have pending order, cancel the pending to replace with new order or?
            5. if risk say not doable, do nothing --> THIS ONE SHOULD CHECK ALSO IF THERE ARE ANY PENDING ORDERS
            6. if risk say doable --> send to trade executor
            """

            print("CALL BOOK FUNCTION")
            print("CALL RISK FUNCTION")

            # this is to model risk liquidate
            random_number = random.randint(0, 10)
            print(random_number)
            if random_number == 0:
                print(f"we will be liquidating all {random_number}")
                print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            else:
                self.updateQueue(s)
                self.strategy.collect_new_data()
                self.strategy.aggregate_data()  # Only aggregate data, do not collect here
                # if time_elapsed > 40:
                output = (
                    self.strategy.analyze_data()
                )  # analyse data and gather prediction
                print("model output: ", output)
                print("MODEL RISK CALL")
                approve_random_number = random.randint(0, 5)
                if approve_random_number == 0:
                    print(f"not approved, do not do anything{approve_random_number}")
                else:
                    print(f"TRADE APPROVED{approve_random_number}")
                    if output != None:

                        direction = output[0].upper()
                        limit_price = float(output[1])
                        timestamp = output[2]
                        date_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        edjacob_time = int(time.time() * 1000)

                        # get our gateway time
                        response = self.restGateway.time()
                        if response != None:
                            servertime = int(response["serverTime"])
                            print(
                                f"gateway : {servertime} vs edjacob : {edjacob_time} vs andre: {int(date_obj.timestamp() * 1000)} ; diff wrt edjacob {int(response['serverTime']) - edjacob_time}"
                            )

                            # I try LIMIT ORDER ya
                            data = {
                                "symbol": "BTCUSDT",
                                "price": limit_price,
                                "side": direction,
                                "type": "LIMIT",
                                "quantity": 0.002,
                                "timestamp": servertime - offset,
                                "recvWindow": 60000,
                                "timeinforce": "GTC",
                            }
                            # data = {
                            #    "symbol": "BTCUSDT",
                            #    "side": direction,
                            #    "type": "MARKET",
                            #    "quantity": 0.002,
                            #    "timestamp": servertime - offset,
                            #    "recvWindow": 60000,
                            # }
                            print(data)
                            self.tradeExecutor.execute_trade(data, "trade")
                get_pnl = self.bookKeeper.get_realized_pnl()
                print("******MY_PNL******", get_pnl)


def on_exec():
    print("Lorem ipsum dolor sit amet, consectetur adipiscing elit.")


# create this app.py to serve as our actual strat file, the main.py is used by strategy already.
if __name__ == "__main__":

    # lets fucking go
    print("LETS FUCKING GO")

    # 1. symbol and API key. someone can help the getenv thing pls
    symbol = "BTCUSDT"
    api_key = ""
    api_secret = ""

    # 2. create a rest api caller object for rest requests. I only use this to get server time
    my_restfactory = RestFactory()
    futuretestnet_base_url = "https://testnet.binancefuture.com"
    # 2a. in our case its this
    futuretestnet_gateway = my_restfactory.create_gateway(
        "BINANCE_TESTNET_FUTURE",
        futuretestnet_base_url,
        api_key,
        api_secret,
    )

    # 3. create EdJacob trade executor object. Will call the TradeExecutor.connect in the Exec Manager constructor
    print("instantiate trade executor")
    myTradeExecutor = TradeExecutor(symbol, api_key, api_secret)
    myTradeExecutor.register_exec_callback(
        on_exec
    )  # this is dummy it is literally just a lorem ipsum
    print("trade executor OK")

    myBookKeeper = BookKeeper(10000, 'USDBTCT')

    print("456MY BOOK KEEPER OK")

    # 4. create the Execution Manager.
    # Impl wise can be cleaner, but for now pass the rest request caller and EdJacob trade executor
    myExecManager = ExecManager(myTradeExecutor, myBookKeeper, futuretestnet_gateway)

    # 5. create the Datastream object, this is to stream data
    myDataStream = DataStream(symbol, api_key, api_secret)

    # 6. register the trading strategy itself as a callback for data stream
    # essentially its saying if there is new data, run the strategy
    # room for improvement probably pass the TradingStrategy as an object. At the moment the proj supports Andre's trading strategy object
    myDataStream.register_tick_callback(myExecManager.execStrat)

    # 7. start connection data stream
    myDataStream.connect()

    # 8. I think this is just for looping.
    while True:
        time.sleep(10)
        print("done wait")