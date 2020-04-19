#coding:utf-8
from threading import Thread, RLock
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from time import strftime

wallet_usdt_ethusdt = float(input('usdt dans la strategie ethusdt ?'))
wallet_eth_ethusdt = 0.0
wallet_usdt_btcusdt = float(input('usdt dans la strategie btcusdt ?'))
wallet_btc_btcusdt = 0.0

verrou = Rlock()

def log_func(msg):
    print(msg)

class Interpreteur(Thread):
    
    def __init__(self):
        print('Initialisation...')
