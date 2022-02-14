import yaml
import time
import json
import requests
import numpy as np
import pandas as pd

from web3 import Web3
from datetime import datetime


class TokenERC20:
    def __init__(self, token_address):
        token_abi_file = open('erc20_abi.json','r')
        token_abi = json.load(token_abi_file)
        self.address = token_address
        self.contract = web3.eth.contract(address=token_address, abi=token_abi)
        self.symbol = self.contract.functions.symbol().call()
        self.decimals = self.contract.functions.decimals().call()

    def balanceOf(self, owner):
        balance = self.contract.functions.balanceOf(owner).call()
        return balance

    def approve(self, owner, spender, amount):
        allowance = self.contract.functions.allowance(owner, spender).call()
        if allowance == 0:
            approve = self.contract.functions.approve(spender, amount).buildTransaction({
                        'from': owner,
                        'gasPrice': web3.toWei('5','gwei'),
                        'nonce': web3.eth.get_transaction_count(owner),
                        })
            signed_txn = web3.eth.account.sign_transaction(approve, private_key=PRIVATE_KEY)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print("Approved: " + web3.toHex(tx_token))


class PancakeSwapAPI:
    def __init__(self, router_address):
        pancake_abi_file = open('pancake_abi.json','r')
        pancake_abi = json.load(pancake_abi_file)
        self.router_address = router_address
        self.pancake_contract = web3.eth.contract(address=router_address, abi=pancake_abi)
        self.token_info_url = 'https://api.pancakeswap.info/api/v2/tokens/'

    def get_token_info(self, token_address):
        response = requests.get(self.token_info_url + token_address)
        token_info = json.loads(response.content)
        return token_info

    # def get_price(self, token_address):
    #     response = requests.get(self.token_info_url + token_address)
    #     token_info = json.loads(response.content)
    #     return token_info['data']['price']

    def get_price(self, token_address):
        router_path = [token_address, WBNB_ADDRESS, BUSD_ADDRESS]
        amountsOut = self.pancake_contract.functions.getAmountsOut(web3.toWei(1, 'ether'), router_path).call()
        return web3.fromWei(amountsOut[2], 'ether')

    def swap_with_tokens(self, wallet_address, input_token, bnb_token, output_token, amount, slippage=0.5):
        router_path = [input_token.address, bnb_token.address, output_token.address]

        amountsOut = self.pancake_contract.functions.getAmountsOut(amount, router_path).call()
        amountsOutMin = int(amountsOut[2] - amountsOut[2] * (slippage / 100))

        input_token.approve(wallet_address, self.router_address, amount)

        nonce = web3.eth.get_transaction_count(wallet_address)
        txn = self.pancake_contract.functions.swapExactTokensForTokens(
              amount,
              amountsOutMin, # here setup the minimum destination token you want to have, you can do some math, or you can put a 0 if you don't want to care
              router_path,
              wallet_address,
              (int(time.time()) + 1000000)
            ).buildTransaction({
              'from': wallet_address,
              #'gas': 260947,
              'gasPrice': web3.toWei('5','gwei'),
              'nonce': nonce,
            })
        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return web3.toHex(tx_token)

    def swap_with_bnb(self, wallet_address, input_token, output_token, value_in_wei, slippage=0.5):
        router_path = [input_token.address, output_token.address]
        amountsOut = self.pancake_contract.functions.getAmountsOut(value_in_wei, router_path).call()
        amountsOutMin = amountsOut[1] - amountsOut[1] * (slippage / 100)

        nonce = web3.eth.get_transaction_count(wallet_address)
        txn = self.pancake_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
              value_in_wei,        
              amountsOutMin, # here setup the minimum destination token you want to have, you can do some math, or you can put a 0 if you don't want to care
              router_path,
              wallet_address,
              (int(time.time()) + 1000000)
            ).buildTransaction({
              'from': wallet_address,
              #'gas': 260947,
              'gasPrice': web3.toWei('5','gwei'),
              'nonce': nonce,
            })
        signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return web3.toHex(tx_token)


class ConfigReader:
    def __init__(self, config_file_path):
        self._file = open(config_file_path)
        self._config = yaml.load(self._file, Loader=yaml.FullLoader)

    def getWalletConfig(self):
        return self._config['wallet']

    def getWalletAddress(self):
        return self._config['wallet']['address']

    def getWalletPrivateKey(self):
        return self._config['wallet']['private_key']

    def getPancakeConfig(self):
        return self._config['pancakeswap']

    def getPancakeRouter(self):
        return self._config['pancakeswap']['router_address']

    def getWBNBAddress(self):
        return self._config['pancakeswap']['wbnb_address']

    def getBUSDAddress(self):
        return self._config['pancakeswap']['busd_address']

    def getStopLossTokens(self):
        return self._config['stoploss']['tokens']

    def getStopLossTokens(self):
        return self._config['stoploss']['tokens']


config = ConfigReader('config.yaml')

bsc = 'https://bsc-dataseed.binance.org/'
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.isConnected(): print('Connected to BSC.')

WALLET_ADDRESS = web3.toChecksumAddress(config.getWalletAddress())
PRIVATE_KEY = config.getWalletPrivateKey()

ROUTER_ADDRESS = web3.toChecksumAddress(config.getPancakeRouter()) # Pancakeswap v2 router
BUSD_ADDRESS = web3.toChecksumAddress(config.getBUSDAddress()) # BUSD
WBNB_ADDRESS = web3.toChecksumAddress(config.getWBNBAddress()) # WBNB

bnb_token = TokenERC20(WBNB_ADDRESS)
busd_token = TokenERC20(BUSD_ADDRESS)

stoploss_tokens = config.getStopLossTokens()
token_list = list(stoploss_tokens)
token_contracts = {}
for token in token_list:
    token_contracts[token] = TokenERC20(web3.toChecksumAddress(stoploss_tokens[token]['address']))

pancake = PancakeSwapAPI(ROUTER_ADDRESS)

# Price monitor and stoploss
price_monitor_list = {}
for token in token_list:
    price_monitor_list[token] = pd.DataFrame(columns=['timestamp', 'price'])
stoploss_tx_list = []

num_samples = 0
while (1):
    try:
        num_samples += 1
        for token in token_list:
            # Get token contract
            token_contract = token_contracts[token]

            # Check price
            price = pancake.get_price(token_contract.address)
            current_timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S.%f')
            print(f'[{current_timestamp}] {token_contract.symbol} => {price}')
            
            # Add price to the price monitor (NOT USED YET)
            #price_monitor_list[token] = price_monitor_list[token].append({'timestamp': current_timestamp, 'price': price}, ignore_index=True)

            # Check balance
            balance = token_contract.balanceOf(WALLET_ADDRESS)

            # If price is less than stoploss value, sell it
            stoploss_value = stoploss_tokens[token]['value']
            if balance == 0 or balance < stoploss_value:
                continue

            slippage = stoploss_tokens[token]['slippage'] / 100
            if price <= stoploss_value:
                tx = pancake.swap_with_tokens(WALLET_ADDRESS, token_contract, bnb_token, busd_token, balance)
                current_timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S.%f")
                print(f"[Stoploss] Timestamp = {current_timestamp} --- Tx = {tx}")
                stoploss_tx_list.append(tx)
    except:
        continue
    
    time.sleep(1)
