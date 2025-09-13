import threading
import argparse
import logging
import time
import os
from  Nadaraya_Zeta import final
from Position import absPos
from binance.um_futures import UMFutures
from binance.error import ClientError
import configparser

os.system('pkg install tmux -y')

config = configparser.ConfigParser()
config.read('config.ini')

key = config.get('binance', 'key')
secret = config.get('binance', 'secret')

quantity = "0.200"  # (-)SHORT (+)LONG
symbol = "BTCUSDT"


# Create an argparse parser
parser = argparse.ArgumentParser(description="Your program description")

# Add a start command-line argument
parser.add_argument("--start", action="store_true", help="Start the program")

# Add an exit command-line argument
parser.add_argument("--exit", action="store_true", help="Exit the program")

# Add a quantity command-line argument
parser.add_argument("--quantity", type=float, help="Specify the quantity")

# Add a testnet command-line argument
parser.add_argument("--testnet", action="store_true", help="Use the testnet")

# Parse the command-line arguments
args = parser.parse_args()

# Set the base URL based on the testnet option
base_url = "https://testnet.binancefuture.com" if args.testnet else "https://fapi.binance.com"
um_futures_client = UMFutures(key=key, secret=secret)
um_futures_client.base_url = base_url


class Order():

    @staticmethod
    def place_Order(symbol, side, quantity):
        try:
            response = um_futures_client.new_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                timeInForce="GTC",
                positionSide=Order.sideSystem(side),
                price=Order.getCurrentPrice(),
            )
            return response
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return None

    @staticmethod
    def close_position(symbol, sideToClose, quantity):
        try:
            response = um_futures_client.new_order(
                symbol=symbol,
                side=Order.closeSystem(sideToClose),
                type='LIMIT',
                quantity=quantity,
                timeInForce="GTC",
                positionSide=Order.sideSystem(sideToClose),
                price=Order.getCurrentPrice(),
            )
            return response
        except Exception as e:
            logging.error(f"Error closing position: {e}")
            return None

    @staticmethod
    def immediateClose():
        try:
            response = um_futures_client.new_order(
                symbol=symbol,
                side=Order.closeSystem(side),
                type='LIMIT',
                quantity=quantity,
                timeInForce="GTC",
                positionSide=Order.sideSystem(side),
                price=Order.getCurrentPrice(),
            )
            return response
        except Exception as e:
            logging.error(f"Error closing position: {e}")
            return None


    @staticmethod
    def getCurrentPrice():
        try:
            info = um_futures_client.ticker_price(symbol)
            return float(info['price'])
        except Exception as e:
            logging.error(f"Error getting current price: {e}")
            return None

    @staticmethod
    def sideSystem(side):
        return 'LONG' if side == 'BUY' else 'SHORT' if side == 'SELL' else None
    
    @staticmethod
    def closeSystem(side):
        return 'SELL' if side == 'BUY' else 'BUY' if side == 'SELL' else None

#Indicator
final_signal = final()
#The current side of the signal
side = 'BUY' if (final_signal == 1) else 'SELL' if (final_signal == 2) else None

def execute():
    global buy_position, sell_position
    current_signal_side = side
    open_position = None  # Initialize open_position here

    if side:
        open_position = absPos(symbol, quantity)
        
    if open_position is not None:
        print("Current Position Side:", open_position)
        print("Current Signal Side:", current_signal_side)

        if open_position != current_signal_side:
            # Close the current position if not in the process of closing
            print("Closing current position...")
            response = Order.close_position(symbol=symbol, sideToClose=open_position, quantity=quantity)
            print(response)

            # Wait for the open position to be closed
            order_id = response.get("orderId") if response and response.get("orderId") else None
            if order_id:
                while True:
                    try:
                        order_info = um_futures_client.query_order(symbol=symbol, orderId=order_id)
                        print("Order Info:", order_info)
                        if order_info['status'] == 'FILLED':
                            print("Position closed.")
                            break
                        time.sleep(1)
                    except ClientError as e:
                        if e.status_code == 408 and e.error_code == -1007:
                            # Handle timeout during query_order, retrying...
                            logging.warning("Timeout error during order query, retrying...")
                            time.sleep(1)
                            continue
                        else:
                            logging.error(f"Error querying order: {e}")
                            time.sleep(1)

            # Open a new position in the opposite direction
            if current_signal_side == 'BUY':
                print("Opening new BUY position...")
                response = Order.place_Order(symbol=symbol, side="BUY", quantity=quantity)
                if response and response.get("orderId"):
                    buy_position = True
                    sell_position = False
            elif current_signal_side == 'SELL':
                print("Opening new SELL position...")
                response = Order.place_Order(symbol=symbol, side="SELL", quantity=quantity)
                if response and response.get("orderId"):
                    sell_position = True
                    buy_position = False


    elif open_position is None :
        # No open position
        current_position_side = None
        
        print("No open position.")
        print("Current Signal Side:", current_signal_side)

        # Check for pending orders
        open_orders = um_futures_client.get_orders(symbol=symbol, recvWindow=3000)
        if not open_orders:
            # No open position and no pending orders, open a new position
            if current_position_side is None or open_position != current_signal_side:
                # Open a new position only if there is no open position or the signal is different
                if current_signal_side == 'BUY':
                    print("Opening new BUY position...")
                    response = Order.place_Order(symbol=symbol, side="BUY", quantity=quantity)
                    if response and response.get("orderId"):
                        buy_position = True
                        sell_position = False
                elif current_signal_side == 'SELL':
                    print("Opening new SELL position...")
                    response = Order.place_Order(symbol=symbol, side="SELL", quantity=quantity)
                    if response and response.get("orderId"):
                        sell_position = True
                        buy_position = False
        else:
            print("There are pending orders. Waiting for orders to be filled...")

            # Wait for all open orders to be filled
            while open_orders:
                time.sleep(1)
                open_orders = um_futures_client.get_orders(symbol=symbol, recvWindow=3000)
                if not open_orders:
                    print("All pending orders filled. Proceeding...")
                    'current_position_side'
    else:
        return 0



def clear_output():
    os.system('clear' if os.name == 'posix' else 'cls')

exit_requested = False

def run_in_background():
    
    global exit_requested
    while True:
        try:
            while not exit_requested:  # Check the exit_requested flag
                execute()
                time.sleep(1)
                clear_output()
        except ClientError as error:
            if error.status_code == 408 and error.error_code == -1007:
                # Handle timeout by retrying after a short delay
                logging.warning("Timeout error during update, retrying...")
                time.sleep(1)
                continue
            else:
                logging.error(
                    "Found error. status: {}, error code: {}, error message: {}".format(
                        error.status_code, error.error_code, error.error_message
                    )
                )
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt: Stopping the program.")
            # Set the exit_requested flag
            exit_requested = True

# ... (rest of your code)

# Check the command-line arguments
if args.start:
    # Start the background thread
    exit_requested = False
    background_thread = threading.Thread(target=run_in_background)
    background_thread.daemon = True
    background_thread.start()

    # Check if quantity is provided and update the global variable
    if args.quantity is not None:
        number = args.quantity
        formatted_number = f"{number:.3f}"
        quantity = str(formatted_number)

    print(f"Program started with quantity {quantity} and testnet {'enabled' if args.testnet else 'disabled'}. Press Ctrl+C to stop.")

    try:
        # Your main program logic can be here if needed
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Execution interrupted by user.")
        exit_requested = True  # Set the exit_requested flag

elif args.exit:
    print("Exiting the program.")
    
    # Stop the tmux session named 'mysession'
    os.system('tmux kill-session -t mysession')
    
    # Perform any cleanup or additional actions before exiting

else:
    print("Invalid command. Use '--start' to start the program or '--exit' to exit.")
