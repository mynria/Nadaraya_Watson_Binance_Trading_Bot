import logging
import time
import pandas as pd
import pandas_ta as ta
from binance.um_futures import UMFutures
from binance.error import ClientError


key = '...'
secret = '...'

quantity = "0.149"  # (-)SHORT (+)LONG
symbol = "BTCUSDT"

um_futures_client = UMFutures(key=key, secret=secret)
um_futures_client.base_url = "https://testnet.binancefuture.com"


def get_data(symbol=symbol, interval='15m', limit=300):
    while True:
        try:
            klines = um_futures_client.klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            
            yield df  # Using 'yield' allows you to create a generator that continuously produces updated data
            
        except ClientError as e:
            if e.status_code == 408 and e.error_code == -1007:
                # Handle timeout by retrying after a short delay
                logging.warning("Timeout error, retrying...")
                time.sleep(1)
                continue
            else:
                logging.error(f"Error fetching data: {e}")
                time.sleep(1)  # To avoid spamming the API in case of other errors

#Signal
emas_length = 6
emab_length = 21


def signal(df):
    signal_ = []
    df['EMAS'] = ta.ema(df['close'], length=emas_length)
    df['EMAB'] = ta.ema(df['high'], length=emab_length)

    for i in range(len(df)):
        if df['EMAS'].iloc[i] < df['EMAB'].iloc[i]:
            signal_.append(1)
        elif df['EMAS'].iloc[i] > df['EMAB'].iloc[i]:
            signal_.append(2)
        else:
            signal_.append(None)

    return signal_

#Returns Updated data
updated_data_generator = get_data()
df = next(updated_data_generator)

# Print the last signal or return nothing if it's None
signals = signal(df)
current_signal = signals[-1] if signals and signals[-1] is not None else None

print(current_signal)