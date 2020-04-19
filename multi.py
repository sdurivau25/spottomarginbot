#coding:utf-8
from threading import Thread, RLock
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from time import strftime

verrou = Rlock()

def log_func(msg):
    print(msg)

class Interpreteur(Thread):
    
    def __init__(self):
        print('Initialisation...')
        self.bots=[]


class Bot(Thread):
    """ Bot de trading"""

    def __init__(self, client, spot_monnaie, margin_monnaie, spot_usdt, spot_asset, margin_usdt, margin_asset):
        with verrou:
            self.log('Initialisation...')
            assert isinstance(client, Client)
            Thread.__init__(self)
            self.client=client
            self.spot_monnaie=spot_monnaie
            self.margin_monnaie=margin_monnaie
            self.spot_usdt=spot_usdt
            self.spot_asset=spot_asset
            self.margin_usdt=margin_usdt
            self.margin_asset=margin_asset
            self.continuer=True
            self.last_order_memory=client.get_all_orders(symbol=spot_monnaie)[-1]
            self.last_order=None

    def log(self, message:str):
        log_func(strftime('[%d/%m %H:%M:%S] Bot {} : {}'.format(id(self), message)))

    @property
    def detect_new_order(self):
        self.last_order = self.client.get_all_orders(symbol=self.spot_monnaie)[-1]
        return self.last_order['orderId'] == self.last_order_memory['orderId']
       
        
    def buy_as_strategy(self):
        self.buy_spot_used_usdt = self.last_order['executedQty']*self.last_order['price'] 
        #get buy_pourcentage
        self.buy_pourcentage = (self.buy_spot_used_usdt)/(self.spot_usdt)
        #usdt used by margin to buy
        self.usdt_quantity = round(float((self.buy_pourcentage*self.margin_usdt)),5)
        #quantity to be bought with margin_asset
        self.asset_quantity = round(float((self.buy_pourcentage*self.margin_usdt)/(self.last_order['price']) - 0.00001),5)
        #Check les quantites
        if self.asset_quantity*float(self.last_order['price']) > 11 :
            #place order
            self.client.create_margin_order(
                    symbol=self.margin_monnaie,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity = self.asset_quantity,
                    )
            #prix d achat
            self.buy_price = client.get_all_margin_orders(symbol=margin_monnaie)[-1]['price']
            #actualise spot_wallet
            self.spot_usdt=self.spot_usdt - self.lastorder['executedQty']*self.last_order['price']
            self.spot_asset=self.spot_asset + self.lastorder['executedQty']
            if round(float(self.usdt),5) - 0.00001 > 0 :
                self.spot_usdt=round(float(self.usdt),5) - 0.00001
            else :
                self.spot_usdt=0.0
            if round(float(self.asset),5)- 0.00001 > 0
                self.spot_asset=round(float(self.asset),5)- 0.00001
            else :
                self.spot_asset=0.0
            #actualise margin_wallet
            self.margin_usdt=self.margin_usdt - self.usdt_quantity 
            self.margin_asset=self.margin_asset + self.asset_quantity
            if round(float(self.margin_usdt),5) - 0.00001 > 0 :
                self.margin_usdt=round(float(self.margin_usdt),5) - 0.00001
            else : 
                self.margin_usdt=0.0
            if round(float(self.margin_asset),5)- 0.00001 > 0 :
                self.margin_asset=round(float(self.margin_asset),5)- 0.00001
            else :
                self.margin_asset=0.0
            #log
            self.log('Achat de {} {} au prix de {}'.format(self.asset_quantity,self.margin_monnaie,self.buy_price))

        else :
            self.log('ERROR 2 : Order too low, buy skipped')

        
        
    def sell_as_strategy(self):
        self.sell_spot_used_asset = self.last_order['executedQty']
        #get sell_pourcentage
        self.sell_pourcentage = (sell_spot_used_asset)/(self.spot_asset)
        #asset used by margin to sell
        self.asset_quantity = round(float(self.sell_pourcentage*self.margin_asset),5)
        #check les quantites
        if self.asset_quantity*float(self.last_order['price']) > 11 :
            #place order
            client.create_margin_order(
                            symbol=self.margin_monnaie,
                            side=SIDE_SELL,
                            type=ORDER_TYPE_MARKET,
                            quantity=self.asset_quantity,
                            )
            #prix de vente
            self.sell_price = client.get_all_margin_orders(symbol=margin_monnaie)[-1]['price']
            #actualise spot_wallet
            self.spot_usdt=self.spot_usdt + self.lastorder['executedQty']*self.last_order['price']
            self.spot_asset=self.spot_asset - self.lastorder['executedQty']
            if round(float(self.spot_usdt),5) - 0.00001 > 0 :
                self.spot_usdt=round(float(self.spot_usdt),5) - 0.00001
            else : 
                self.spot_usdt=0.0
            if round(float(self.spot_asset),5) - 0.00001 > 0 :
                self.spot_asset=round(float(self.spot_asset),5) - 0.00001
            else :
                self.spot_asset=0.0
            #actualise margin_wallet
            self.margin_usdt=self.margin_usdt + self.asset_quantity*sell_price
            self.margin_asset=self.margin_asset - self.asset_quantity
            if round(float(self.margin_usdt),5) - 0.00001 > 0 :
                self.margin_usdt=round(float(self.margin_usdt),5) - 0.00001
            else :
                self.margin_usdt=0.0
            if round(float(self.margin_asset),5)- 0.00001 > 0 :
                self.margin_asset=round(float(self.margin_asset),5)- 0.00001
            else :
                self.margin_asset=0.0
            #log
            self.log('Vente de {} {} au prix de {}'.format(self.asset_quantity,self.margin_monnaie,self.buy_price))
        else :
            self.log('ERROR 2 : Order too low, sell skipped')
        


   
    def run(self):
        self.log("A l'ecoute...")
        while self.continuer:
            if self.detect_new_order:
                self.last_order_memory = self.last_order
                
                if self.last_order['side'] == 'BUY':
                    self.log('Nouvel achat repere, copie en cours...')
                    self.buy_as_strategy()
                    self.log('Current status wallet : {} Asset et {} USD'.format(self.margin_asset,self.margin_usdt)
                elif self.last_order['side'] == 'SELL':
                    self.log('Nouvelle vente reperee, copie en cours...')
                    self.sell_as_strategy()
                    self.log('Current status wallet : {} Asset et {} USD'.format(self.margin_asset,self.margin_usdt)
                else:
                    self.log('ERREUR 1: Abort')
                    self.continuer = False

                self.log("En attente du passage du dernier ordre detecte...")
                while self.client.get_open_orders(symbol=self.spot_monnaie) !=[]:
                    pass
                self.log('Bot en ecoute.')



        self.log('Operations terminees, bot en veille.')

#lancer le thread interpreteur
#il est capable d'ajouter a une liste via commande un nouveau bot
#feature: listage des bots en cours AVEC LA MONNAIE QUI LUI CORRESPOND
#feature: ne demarre pas un nouveau bot si il y en a deja un
