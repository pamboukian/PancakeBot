import time
import yaml
from web3 import Web3
from utils.token_erc20 import TokenERC20
from utils.telegram import Telegram


class ConfigReader:
    def __init__(self, config_file_path):
        self._file = open(config_file_path)
        self._config = yaml.load(self._file, Loader=yaml.FullLoader)

    def getWallets(self):
        return list(self._config['wallets'])

    def getToken(self, wallet_name):
        return self._config['wallets'][wallet_name]['token']

    def getTokenAddress(self, wallet_name):
        return self._config['wallets'][wallet_name]['token_address']

    def getWalletAddress(self, wallet_name):
        return self._config['wallets'][wallet_name]['wallet_address']

    def getTelegramToken(self):
        return self._config['telegram']['token']

    def getTelegramClientId(self):
        return self._config['telegram']['client_id']


config = ConfigReader('config_wallet_monitor.yaml')

telegram = Telegram(config.getTelegramToken(), config.getTelegramClientId())

bsc = 'https://bsc-dataseed.binance.org/'
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.isConnected(): print('Connected to BSC')

wallets_list = config.getWallets()
wallets_balance = {}
token_contracts = {}
for wallet in wallets_list:
    token = config.getToken(wallet)
    token_address = config.getTokenAddress(wallet)
    token_contracts[token] = TokenERC20(web3.toChecksumAddress(token_address))

    wallet_address = config.getWalletAddress(wallet)
    wallets_balance[wallet_address] = token_contracts[token].balanceOf(web3.toChecksumAddress(wallet_address))

while (1):
    try:
        for wallet in wallets_list:
            token = config.getToken(wallet)
            wallet_address = config.getWalletAddress(wallet)
            previous_balance = wallets_balance[wallet_address]
            current_balance = token_contracts[token].balanceOf(web3.toChecksumAddress(wallet_address))
            if current_balance != previous_balance:
                msg = f"The balance of wallet '{wallet}' change!!\nPrevious balance: {web3.fromWei(previous_balance, 'ether')}\nCurrent balance: {web3.fromWei(current_balance, 'ether')}"
                telegram.send(msg)
                print(msg)
                wallets_balance[wallet_address] = current_balance
    except:
        continue
    
    time.sleep(5)




