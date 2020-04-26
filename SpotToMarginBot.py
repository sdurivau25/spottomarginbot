#Final SpotToMarginBot
from threading import Thread, RLock
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from time import strftime, sleep

#Constantes :
SIDE_BUY = 'BUY'
SIDE_SELL = 'SELL'

ORDER_TYPE_LIMIT = 'LIMIT'
ORDER_TYPE_MARKET = 'MARKET'
ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

#Fonctions :
def log_func(msg):
    with open('log.txt','a') as f:
        f.write('{}\n'.format(msg))
        
def round_to_5_decimal(x):
        return float(int(x*10**5)/10**5)
        
def pourcentage_is_fraction(x):
    x = float(x)
    if x < 0 :
        x = 0.0
    elif x > 1 :
        x = 1.0
    x = float(x)
    return x

#Bot :
class Bot(Thread) :
    """SpotToMarginBot"""
    
    def __init__(self, client, paire_de_base, paire_tradee, spot_qty_paire_de_base, spot_qty_paire_tradee, margin_qty_paire_de_base, margin_qty_paire_tradee):
        self.log('Initialisation...')
        assert isinstance(client, Client)
        Thread.__init__(self)
        self.client = client
        self.paire_de_base = paire_de_base
        self.paire_tradee = paire_tradee
        self.binance_format_asset = '{}{}'.format(self.paire_tradee,self.paire_de_base)
        self.spot_qty_paire_de_base = spot_qty_paire_de_base
        self.spot_qty_paire_tradee = spot_qty_paire_tradee
        self.margin_qty_paire_de_base = margin_qty_paire_de_base
        self.margin_qty_paire_tradee = margin_qty_paire_tradee
        self.last_spotorder_exed_memory = client.get_all_orders(symbol=self.binance_format_asset)[-1]
        self.continuer=True
        self.last_spotorder_exed=None
        self.paused = False
        
    def log(self, message:str):
        log_func(strftime('[%d/%m %H:%M:%S] Bot {} : {}'.format(id(self), message)))
        
    @property 
    def detect_new_order(self):
        self.last_spotorder_exed = client.get_all_orders(symbol=self.binance_format_asset)[-1]
        return not self.last_spotorder_exed['orderId'] == self.last_spotorder_exed_memory['orderId']
 

    def get_infos(self):
        self.lastprice = float(client.get_my_trades(symbol=self.binance_format_asset)[-1]['price'])
        self.lastexecutedQty = float(client.get_all_orders(symbol=self.binance_format_asset)[-1]['executedQty'])
        self.lastcummulativeQuoteQty = float(client.get_all_orders(symbol=self.binance_format_asset)[-1]['cummulativeQuoteQty'])
        self.lastside = client.get_all_orders(symbol=self.binance_format_asset)[-1]['side']
        self.lastmarginexecutedQty = float(client.get_all_margin_orders(symbol=self.binance_format_asset)[-1]['executedQty'])
        self.lastmargincummulativeQuoteQty = float(client.get_all_margin_orders(symbol=self.binance_format_asset)[-1]['cummulativeQuoteQty'])
        
    def get_side(self):
        self.log('Enter on get_side')
        if self.lastside == 'BUY' :
            self.side = SIDE_BUY
            self.side_is_buy = True
            self.log('Last trade is a BUY')
        elif self.lastside == 'SELL' :
            self.side = SIDE_SELL
            self.side_is_buy = False
            self.log('Last trade is a SELL')
        else :
            self.side_is_buy = 'Error'
            self.log('Error on get_side')   
            
    def calc_pourcentage(self):
        self.log('Enter in calc_pourcentage')
        if self.side_is_buy :
            self.pourcentage = self.lastcummulativeQuoteQty/float(self.spot_qty_paire_de_base)
            self.pourcentage = pourcentage_is_fraction(self.pourcentage)
            self.log('Pourcentage of wallet involved in last trade : {} '.format(self.pourcentage))
        elif not self.side_is_buy :
            self.pourcentage = self.lastexecutedQty /float(self.spot_qty_paire_tradee)
            self.pourcentage = pourcentage_is_fraction(self.pourcentage)
            self.log('Pourcentage of wallet involved in last trade : {} '.format(self.pourcentage))
        else :
            self.log('Error in calc_pourcentage')

    def calc_margin_used(self):
        self.log('Enter in calc_margin_used')
        if self.side_is_buy :
            self.margin_base = float(self.pourcentage * self.margin_qty_paire_de_base)
            self.log('Gonna use {} {} from margin'.format(self.margin_base, self.paire_de_base))
            self.margin_used = self.margin_base/self.lastprice
            self.log('Gonna buy {} {}'.format(self.margin_used, self.paire_tradee))
        elif not self.side_is_buy :
            self.margin_used = float(self.pourcentage * self.margin_qty_paire_tradee)
            self.log('Gonna use {} {} from margin'.format(self.margin_used, self.paire_tradee))
        else :
            self.log('Error in calc_margin_used')
        self.margin_used = 0.9*self.margin_used #au cas ou le prix change trop entre le dernier ordre spot et notre ordre marche margin
        self.margin_orderQty = round_to_5_decimal(self.margin_used)
        
    def check_minimum(self):
        self.log('Enter in check_minimum')
        # Attention ! les contrôles ne sont faits que si la paire est USDT, BTC, ETH, BNB 
        if self.side_is_buy :
            if self.paire_de_base == 'USDT' and self.margin_base > 10 or self.paire_de_base == 'BTC' and self.margin_base > 0.0001 or self.paire_de_base == 'ETH' and self.margin_base > 0.01 or self.paire_de_base == 'BNB' and self.margin_base > 0.1 or self.paire_de_base not in ['USDT', 'BTC', 'ETH', 'BNB'] :
                self.minimum_ok = True 
            else :
                self.minimum_ok = False
        elif not self.side_is_buy :
            if self.paire_tradee == 'USDT' and self.margin_orderQty > 10 or self.paire_tradee == 'BTC' and self.margin_orderQty > 0.0001 or self.paire_tradee == 'ETH' and self.margin_orderQty > 0.01 or self.paire_tradee == 'BNB' and self.margin_orderQty > 0.1 or self.paire_tradee not in ['USDT', 'BTC', 'ETH', 'BNB'] :
                self.minimum_ok = True 
            else :
                self.minimum_ok = False
        else :
            self.log('Error in check_minimum')
        
    def place_order(self):
        self.log('Enter in place_order')
        if self.side_is_buy :
            self.log("Let's place a buy order !")
        elif not self.side_is_buy :
            self.log("Let's place a sell order !")
        else :
            self.log("Is this a buy or a sell ? I'm lost !")
            self.log('Error in place_order')
        if self.minimum_ok :
            client.create_margin_order(
                            symbol=self.binance_format_asset,
                            side=self.side,
                            type=ORDER_TYPE_MARKET,
                            quantity = self.margin_orderQty,
                            )
            self.log('Ordre put, please wait')
            while client.get_open_margin_orders(symbol=self.binance_format_asset) !=[] :
                pass
            self.last_spotorder_exed_memory = self.last_spotorder_exed
            self.last_margin_trade = client.get_margin_trades(symbol=self.binance_format_asset)[-1]
            self.last_margin_order = client.get_all_margin_orders(symbol=self.binance_format_asset)[-1]
            self.log('Traded {}, {}, at price {}, qty : {}, quoteQty : {}'.format(self.binance_format_asset, self.side, self.last_margin_trade['price'], self.last_margin_order['executedQty'], self.last_margin_order['cummulativeQuoteQty']))
        else :
            self.log('Sorry, order too low, order skipped')
        
    def actualize_wallet(self):
        self.log('Enter in actualize_wallet')
        if self.side_is_buy :
            self.get_infos()
            #Spot Wallet 
            self.spot_qty_paire_de_base = float(self.spot_qty_paire_de_base) - float(self.lastcummulativeQuoteQty)
            self.spot_qty_paire_de_base = round_to_5_decimal(self.spot_qty_paire_de_base)
            self.spot_qty_paire_tradee = float(self.spot_qty_paire_tradee) + float(self.lastexecutedQty)
            self.spot_qty_paire_tradee = round_to_5_decimal(self.spot_qty_paire_tradee)
            #Margin Wallet
            self.margin_qty_paire_de_base = float(self.margin_qty_paire_de_base) - float(self.lastmargincummulativeQuoteQty)
            self.margin_qty_paire_de_base = round_to_5_decimal(self.margin_qty_paire_de_base)
            self.margin_qty_paire_tradee = float(self.margin_qty_paire_tradee) + float(self.lastmarginexecutedQty)
            self.margin_qty_paire_tradee = round_to_5_decimal(self.margin_qty_paire_tradee)
        elif not self.side_is_buy :
            self.get_infos()
            #Spot Wallet 
            self.spot_qty_paire_de_base = float(self.spot_qty_paire_de_base) + float(self.lastcummulativeQuoteQty)
            self.spot_qty_paire_de_base = round_to_5_decimal(self.spot_qty_paire_de_base)
            self.spot_qty_paire_tradee = float(self.spot_qty_paire_tradee) - float(self.lastexecutedQty)
            self.margin_qty_paire_tradee = round_to_5_decimal(self.margin_qty_paire_tradee)
            #Margin Wallet
            self.margin_qty_paire_de_base = float(self.margin_qty_paire_de_base) + float(self.lastmargincummulativeQuoteQty)
            self.margin_qty_paire_de_base = round_to_5_decimal(self.margin_qty_paire_de_base)
            self.margin_qty_paire_tradee = float(self.margin_qty_paire_tradee) - float(self.lastmarginexecutedQty)
            self.margin_qty_paire_tradee = round_to_5_decimal(self.margin_qty_paire_tradee)
        else :
            self.log('Error in actualize_wallet')
        self.log('New spot wallet balance : {} {} and {} {}'.format(self.spot_qty_paire_de_base, self.paire_de_base, self.spot_qty_paire_tradee, self.paire_tradee))
        self.log('New margin wallet balance : {} {} and {} {}'.format(self.margin_qty_paire_de_base, self.paire_de_base, self.margin_qty_paire_tradee, self.paire_tradee))
        
    def run(self):
        self.log('Bot is ready...')
        while self.continuer:
            sleep(0.32)
            while self.paused:
                pass
            if self.detect_new_order:
                self.log('New spot trade detected')
                self.get_infos()
                self.get_side()
                self.calc_pourcentage()
                self.calc_margin_used()
                self.check_minimum()
                self.place_order()
                self.log("Waiting for open orders to be taken...")
                while client.get_open_orders(symbol=self.binance_format_asset) !=[] or client.get_open_margin_orders(symbol=self.binance_format_asset) != [] :
                    pass
                self.actualize_wallet()
                self.last_spotorder_exed_memory = self.last_spotorder_exed
                self.log('All went well, bot is ready for service')
                
        self.log('Operations terminees, bot en veille.')
        
#Interpreteur :

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
                b.last_spotorder_exed_memory = client.get_all_orders(symbol=b.binance_format_asset)[-1]
                b.paused=False
        elif ' ' not in comm:
            print('G pa capte')
        else:
            for b in bots:
                if str(id(b))==comm.split(' ')[1]:
                    b.last_spotorder_exed_memory = client.get_all_orders(symbol=b.binance_format_asset)[-1]
                    b.paused = False
                    break
            else:
                print("Ce bot n'existe pas")
    elif comm == 'list':
        for b in bots:
            print('Bot {} is trading on {}. status : {}, spot wallet : {} {}, {} {} , margin wallet : {} {}, {} {}'.format(id(b), b.binance_format_asset, ['ENABLED', 'PAUSED'][b.paused], b.spot_qty_paire_de_base, b.paire_de_base, b.spot_qty_paire_tradee, b.paire_tradee, b.margin_qty_paire_de_base, b.paire_de_base , b.margin_qty_paire_tradee, b.paire_tradee))
    elif comm == 'start':
        paire_de_base=input('Paire de base :')
        paire_tradee=input('Paire tradee :')
        spot_qty_paire_de_base=float(input('Spot qty paire de base :'))
        spot_qty_paire_tradee=float(input('Spot qty paire tradee : '))
        margin_qty_paire_de_base=float(input('Margin qty paire de base : '))
        margin_qty_paire_tradee=float(input('Margin qty paire tradee : '))

        n=Bot(client, paire_de_base, paire_tradee, spot_qty_paire_de_base, spot_qty_paire_tradee, margin_qty_paire_de_base, margin_qty_paire_tradee)
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

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        