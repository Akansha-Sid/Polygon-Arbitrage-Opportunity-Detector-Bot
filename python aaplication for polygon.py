import json
import time
from web3 import Web3


with open("config.json") as f:
    CONFIG = json.load(f)

RPC_URL = CONFIG["rpc_url"]
TRADE_AMOUNT = Web3.to_wei(CONFIG["trade_amount_eth"], "ether")
MIN_PROFIT = CONFIG["min_profit_usdc"]

DEX_ROUTERS = CONFIG["dexes"]  
TOKENS = CONFIG["tokens"]      


web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise Exception(" Could not connect to Polygon RPC")


with open("UniswapV2RouterABI.json") as f:
    ROUTER_ABI = json.load(f)


def get_price(router_addr, token_in, token_out, amount_in):
    router = web3.eth.contract(address=router_addr, abi=ROUTER_ABI)
    try:
        amounts = router.functions.getAmountsOut(amount_in, [token_in, token_out]).call()
        return amounts[-1]
    except Exception as e:
        print(f" Error fetching price: {e}")
        return None


def check_arbitrage():
    weth = Web3.to_checksum_address(TOKENS["WETH"])
    usdc = Web3.to_checksum_address(TOKENS["USDC"])

    prices = {}
    for dex, addr in DEX_ROUTERS.items():
        price_out = get_price(addr, weth, usdc, TRADE_AMOUNT)
        if price_out:
            prices[dex] = Web3.from_wei(price_out, "ether")

    if len(prices) < 2:
        return None

    best_buy = min(prices, key=prices.get)
    best_sell = max(prices, key=prices.get)

    profit = prices[best_sell] - prices[best_buy]

    if profit > MIN_PROFIT:
        return {
            "buy_from": best_buy,
            "sell_to": best_sell,
            "profit": profit,
            "prices": prices
        }
    return None


def main():
    while True:
        opp = check_arbitrage()
        if opp:
            print(f" Arbitrage Opportunity: {opp}")
            with open("arbitrage_log.txt", "a") as log:
                log.write(json.dumps(opp) + "\n")
        time.sleep(CONFIG["poll_interval"])

if __name__ == "__main__":
    main()
