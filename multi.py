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

class Bot(Thread):
    """ Bot de trading"""

    def __init__(self, client, monnaie, argent):
        with verrou:
            self.log('Initialisation...')
            assert isinstance(client, Client)
            Thread.__init__(self)
            self.client=client
            self.argent=argent
            self.monnaie=monnaie
            self.continuer=True
            self.last_order_memory=client.get_all_orders(symbol=MONNAIE)[-1]
            self.last_order=None

    def log(self, message):
        log_func(strftime('[%d/%m %H:%M:%S] Bot {} : {}'.format(id(self), message)))

    @property
    def detect_new_order(self):
        self.last_order = self.client.get_all_orders(symbol=self.monnaie)[-1]
        return self.last_order['orderId'] == self.last_order_memory['orderId']

    def buy_all(self):
        self.client.create_margin_order(
                symbol=self.monnaie,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity = round((connaitre_la_thune(client)-5)/float(client.get_recent_trades(symbol=self.monnaie)[-1]['price']), 4),
                )

    def sell_all(self):
        pass


    def run(self):
        self.log("A l'ecoute...")
        while self.continuer:
            if self.detect_new_order:
                self.last_order_memory = self.last_order
                
                if self.last_order['side'] == 'BUY':
                    self.log('Nouvel achat repere, copie en cours...')
                    self.buy_all()
                elif self.last_order['side'] == 'SELL':
                    self.log('Nouvelle vente reperee, copie en cours...')
                    self.sell_all()
                else:
                    self.log('ERREUR 1: Abort')
                    self.continuer = False

                self.log("En attente du passage du dernier ordre detecte...")
                while self.client.get_open_orders(symbol=self.monnaie) !=[]:
                    pass
                self.log('Bot en ecoute.')



        self.log('Operations terminees, bot en veille.')

#lancer le thread interpreteur
#il est capable d'ajouter a une liste via commande un nouveau bot
#feature: listage des bots en cours AVEC LA MONNAIE QUI LUI CORRESPOND
#feature: ne demarre pas un nouveau bot si il y en a deja un
