import json

import time
from web3 import Web3


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

    def approve(self, owner, spender, amount, private_key):
        allowance = self.contract.functions.allowance(owner, spender).call()
        if allowance == 0:
            approve = self.contract.functions.approve(spender, amount).buildTransaction({
                        'from': owner,
                        'gasPrice': web3.toWei('5','gwei'),
                        'nonce': web3.eth.get_transaction_count(owner),
                        })
            signed_txn = web3.eth.account.sign_transaction(approve, private_key=private_key)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print("Approved: " + web3.toHex(tx_token))


bsc = 'https://bsc-dataseed.binance.org/'
global web3
web3 = Web3(Web3.HTTPProvider(bsc))