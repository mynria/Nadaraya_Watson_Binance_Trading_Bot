from binance.um_futures import UMFutures
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

key = config.get('binance', 'key')
secret = config.get('binance', 'secret')

symbol = "BTCUSDT"
quantity = ""  # Must be in accordance with the given symbol

um_futures_client = UMFutures(key=key, secret=secret)
um_futures_client.base_url = "https://testnet.binancefuture.com"


def position(symbol, SymbolQuantity):
    sides=['BUY', 'SELL']
    for side in sides:
        adjusted_quantity = SymbolQuantity if side == 'BUY' else "-" + SymbolQuantity
        response = um_futures_client.get_position_risk(recvWindow=3000)
        for pos in response:
            if pos.get("symbol") == symbol and pos.get("positionAmt") == adjusted_quantity:
                return side
    return None

def absPos(symbol, quantity):
    position_side = position(symbol, quantity)

    if position_side is not None:
        return position_side
    else:
        return None
    
print(absPos(symbol, quantity))
