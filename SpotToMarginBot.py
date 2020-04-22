#coding:utf-8
from threading import Thread, RLock
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, TIME_IN_FORCE_GTC
from time import strftime, sleep

def log_func(msg):
    with open('log.txt','a') as f:
        f.write('{}\n'.format(msg))


class Bot(Thread):
    """ Bot de trading"""

    def __init__(self, client, spot_monnaie, margin_monnaie, spot_usdt, spot_asset, margin_usdt, margin_asset):
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
        self.last_order_memory=client.get_my_trades(symbol=self.spot_monnaie)[-1]
        self.last_order=None
        self.paused = False

    def log(self, message:str):
        log_func(strftime('[%d/%m %H:%M:%S] Bot {} : {}'.format(id(self), message)))

    @property
    def detect_new_order(self):
        self.last_order = self.client.get_my_trades(symbol=self.spot_monnaie)[-1]
        return not self.last_order['orderId'] == self.last_order_memory['orderId']
       
#self.last_order attributes : 'qty', 'price', 'quoteQty'
        
    def buy_as_strategy(self):
        self.buy_spot_used_usdt = float(self.last_order['quoteQty'])
        #get buy_pourcentage
        self.buy_pourcentage = (self.buy_spot_used_usdt)/float(self.spot_usdt)
        #usdt used by margin to buy
        self.usdt_quantity = self.buy_pourcentage*float(self.margin_usdt)
        #quantity to be bought with margin_asset
        self.asset_quantity = float(int((self.usdt_quantity/float(self.last_order['price']))*10**5)/10**5)
        #Check les quantites
        if self.asset_quantity*float(self.last_order['price']) > 10.5 :
            #place order
            self.client.create_margin_order(
                    symbol=self.margin_monnaie,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity = self.asset_quantity,
                    )
            #prix d achat
            self.buy_price = float(client.get_margin_trades(symbol=margin_monnaie)[-1]['price'])
            #actualise spot_wallet
            self.spot_usdt=self.spot_usdt - float(self.last_order['quoteQty'])
            self.spot_asset=self.spot_asset + float(self.last_order['qty'])
            if float(int(self.spot_usdt*10**5)/10**5) > 0.01 :
                self.spot_usdt=float(int(self.spot_usdt*10**5)/10**5)
            else :
                self.spot_usdt=0.01
            if float(int(self.spot_asset*10**5)/10**5) > 0.00001:
                self.spot_asset=float(int(self.spot_asset*10**5)/10**5)
            else :
                self.spot_asset=0.00001
            #actualise margin_wallet
            self.margin_usdt=self.margin_usdt - float(client.get_margin_trades(symbol=margin_monnaie)[-1]['quoteQty'])
            self.margin_asset=self.margin_asset + float(client.get_margin_trades(symbol=margin_monnaie)[-1]['qty'])
            if float(int(self.margin_usdt*10**5)/10**5) > 0.01 :
                self.margin_usdt=float(int(self.margin_usdt*10**5)/10**5)
            else : 
                self.margin_usdt=0.01
            if float(int(self.margin_asset*10**5)/10**5) > 0.00001 :
                self.margin_asset=float(int(self.margin_asset*10**5)/10**5)
            else :
                self.margin_asset=0.00001
            #log
            self.log('Achat de {} {} au prix de {}'.format(self.asset_quantity,self.margin_monnaie,self.buy_price))

        else :
            self.log('ERROR 2 : Order too low, buy skipped')

        
        
    def sell_as_strategy(self):
        self.sell_spot_used_asset = float(self.last_order['qty'])
        #get sell_pourcentage
        self.sell_pourcentage = (self.sell_spot_used_asset)/(self.spot_asset)
        #asset used by margin to sell
        self.asset_quantity = float(int(self.sell_pourcentage*self.margin_asset*10**5)/10**5)
        #check les quantites
        if self.asset_quantity*float(self.last_order['price']) > 10.5 :
            #place order
            client.create_margin_order(
                            symbol=self.margin_monnaie,
                            side=SIDE_SELL,
                            type=ORDER_TYPE_MARKET,
                            quantity = self.asset_quantity,
                            )
            #prix de vente
            self.sell_price = float(float(client.get_margin_trades(symbol=margin_monnaie)[-1]['price']))
            #actualise spot_wallet
            self.spot_usdt=self.spot_usdt + float(self.last_order['quoteQty'])
            self.spot_asset=self.spot_asset - float(self.last_order['qty'])
            if float(int(self.spot_usdt*10**5)/10**5) > 0.01 :
                self.spot_usdt=float(int(self.spot_usdt*10**5)/10**5)
            else : 
                self.spot_usdt=0.01
            if float(int(self.spot_asset*10**5)/10**5) > 0.00001 :
                self.spot_asset=float(int(self.spot_asset*10**5)/10**5)
            else :
                self.spot_asset=0.00001
            #actualise margin_wallet
            self.margin_usdt=self.margin_usdt + float(client.get_margin_trades(symbol=margin_monnaie)[-1]['quoteQty'])
            self.margin_asset=self.margin_asset - float(client.get_margin_trades(symbol=margin_monnaie)[-1]['qty'])
            if float(int(self.margin_usdt*10**5)/10**5) > 0.01 :
                self.margin_usdt=float(int(self.margin_usdt*10**5)/10**5)
            else :
                self.margin_usdt=0.01
            if float(int(self.margin_asset*10**5)/10**5) > 0.00001 :
                self.margin_asset=float(int(self.margin_asset*10**5)/10**5)
            else :
                self.margin_asset=0.00001
            #log
            self.log('Vente de {} {} au prix de {}'.format(self.asset_quantity,self.margin_monnaie,self.buy_price))
        else :
            self.log('ERROR 2 : Order too low, sell skipped')
        


   
    def run(self):
        self.log("A l'ecoute...")
        while self.continuer:
            sleep(0.32)
            while self.paused:
                pass
            if self.detect_new_order:
                self.last_order_memory = self.last_order
                
                if self.last_order['side'] == 'BUY':
                    self.log('Nouvel achat repere, copie en cours...')
                    self.buy_as_strategy()
                    self.log('Current status wallet : {} Asset et {} USD'.format(self.margin_asset,self.margin_usdt))
                elif self.last_order['side'] == 'SELL':
                    self.log('Nouvelle vente reperee, copie en cours...')
                    self.sell_as_strategy()
                    self.log('Current margin status wallet : {} Asset et {} USD'.format(self.margin_asset,self.margin_usdt))
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

bots = []
log_func('Initialisation...')
client = Client(input('Quelle est votre cle publique? : '),input('Quelle est votre cle privee? : '))
log_func('Connecte')

while True:
    comm = input('@ : ')
    if comm == 'help':
        print("""Aide : liste des commandes : 
- start
    Cree un nouveau bot
- pause [id/all]
- kill [id/all]
- list
- resume [id/all]
- log
- dellog
""")
    elif comm.startswith('pause'):
        if comm=='pause all':
            for b in bots:
                b.paused=True
        elif ' ' not in comm:
            print('G pa capte')
        else:
            for b in bots:
                if str(id(b))==comm.split(' ')[1]:
                    b.paused = True
                    break
            else:
                print("Ce bot n'existe pas")
    elif comm == 'dellog':
        with open('log.txt','w+') as f:
            f.write('')
    elif comm.startswith('resume'):
        if comm=='resume all':
            for b in bots:
                b.paused=False
                b.last_order_memory = b.client.get_my_trades(symbol=self.spot_monnaie)[-1]
        elif ' ' not in comm:
            print('G pa capte')
        else:
            for b in bots:
                if str(id(b))==comm.split(' ')[1]:
                    b.paused = False
                    b.last_order_memory = b.client.get_my_trades(symbol=self.spot_monnaie)[-1]
                    break
            else:
                print("Ce bot n'existe pas")
    elif comm == 'list':
        for b in bots:
            print('Bot {} is trading on spot_monnaie :{}. status : {}, spot wallet : {} asset, {} USDT , margin wallet : {} asset, {} usdt'.format(id(b), b.spot_monnaie, ['ENABLED', 'PAUSED'][b.paused], b.spot_asset, b.spot_usdt, b.margin_asset, b.margin_usdt))
    elif comm == 'start':
        spot_monnaie=input('Spot_monnaie : ')
        margin_monnaie=input('Margin_monnaie : ')
        spot_usdt=float(input('Spot_usdt : '))
        spot_asset=float(input('Spot_asset : '))
        margin_usdt=float(input('Margin_usdt : '))
        margin_asset=float(input('Margin_asset : '))

        n=Bot(client, spot_monnaie, margin_monnaie, spot_usdt, spot_asset, margin_usdt, margin_asset)
        n.start()
        bots.append(n)
    elif comm=='log':
        with open('log.txt','r') as f:
            print(f.read())

    elif comm.startswith('kill'):
        if comm=='kill all':
            for b in bots:
                b.continuer = False
            del b
            break
        elif ' ' not in comm:
            print('G pa capte')
        else:
            for i in range(len(bots)):
                if str(id(bots[i])) == comm.split(' ')[1]:
                    bots[i].continuer = False
            else:
                print("Ce bot n'existe pas")
                continue
            del bots[i]
    else:
        print('Commande inconnue, veuillez taper "help" pour voir la liste des commandes')

print('Programme termine')
